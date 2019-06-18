#!/usr/bin/env python3
import os
import time
import logging
import subprocess
import tempfile

from retry import retry as _retry
import click
import click_log
import jinja2

log = logging.getLogger(__name__)
click_log.basic_config(log)
log.setLevel(logging.DEBUG)


class Config():
    def __init__(self):
        self.NOMAD_URL = os.environ['NOMAD_URL']
        self.CONSUL_URL = os.environ['CONSUL_URL']

        self.K3S_HTTP_PORT = os.environ.get('K3S_HTTP_PORT', 6480)
        self.K3S_HTTPS_PORT = os.environ.get('K3S_HTTPS_PORT', 6443)
        self.SENTRY_HTTP_PORT = os.environ.get('SENTRY_HTTP_PORT', 6643)
        self.TELEGRAF_HTTP_PORT = os.environ.get('TELEGRAF_HTTP_PORT', 6463)
        self.GRAFANA_HTTP_PORT = os.environ.get('GRAFANA_HTTP_PORT', 6663)
        self.PROMETHEUS_HTTP_PORT = os.environ.get('PROMETHEUS_HTTP_PORT', 6446)

        self.DATA_DIR = '/data'
        self.KUBECONFIG = '/data/kubeconfig.yml'

        self.CHARTS = ['sentry', 'telegraf', 'prometheus', 'grafana']


config = Config()

def retry(exc):
    return _retry(exc, tries=7, delay=5, backoff=1.3, jitter=(1,3), logger=log)


def execve(args):
    args = [str(a) for a in args]
    log.debug("+ exec  %s", " ".join(args))
    os.execve(args[0], args, os.environ)


def run(args, **kwargs):
    args = [str(a) for a in args]
    log.debug("+ %s", " ".join(args))
    t0 = time.time()
    ret = subprocess.check_output(args, **kwargs).decode('latin1')
    dt = int((time.time() - t0)*1000)
    log.debug("... after %s ms:\n%s", dt, ret)
    return ret


@click.group()
def cli():
    pass


@cli.command()
def healthcheck():
    raise NotImplemented()


def k3s_server_args():
    return [
        '/bin/k3s',
        'server',
        '--data-dir', config.DATA_DIR + "/k3s",
        '--bind-address', "0.0.0.0",
        '--https-listen-port', config.K3S_HTTPS_PORT,
        '--http-listen-port', config.K3S_HTTP_PORT,
        '--log', config.DATA_DIR + '/k3s/server.log',
        '--write-kubeconfig', config.KUBECONFIG,
        '--no-deploy=traefik',
        #'--node-name', 'monitoring',  # this checks with DNS and crashes our server :(
    ]


def helm_args():
    return ["/bin/helm", "--kubeconfig", config.KUBECONFIG]


def kubectl_args():
    return ["/bin/k3s", "kubectl", "--kubeconfig", config.KUBECONFIG]


@cli.command()
@click.argument('args', nargs=-1)
def helm(args):
    execve(helm_args() + list(args))


@cli.command()
@click.argument('args', nargs=-1)
def kubectl(args):
    execve(kubectl_args() + list(args))


def _helm(*args):
    return run(helm_args() + list(args))


def helm_install(name):
    if name in _helm('ls', '--deployed', '-q', name):
        log.info('Already deployed: %s', name)
    elif name in _helm('ls', '--all', '-q', name):
        log.error('Past deployment failure!')
        return

    with open(f'values/{name}.yaml', 'r') as f:
        template = jinja2.Template(f.read())
    chart = f'stable/{name}'
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml') as values:
        values.write(template.render(config=config))
        values.flush()

        args = ['install', '--dep-up', '--atomic', '-f', values.name, '-n', name, chart]
        _helm(*args)


def _kubectl(*args):
    return run(kubectl_args() + list(args))


@retry(subprocess.CalledProcessError)
def wait_for_k3s():
    _kubectl('get', 'node')


@retry(subprocess.CalledProcessError)
def wait_for_helm():
    _helm('install', '--dep-up', '--dry-run', 'stable/sentry')


def server_init():
    # setup k3s pvc
    log.info("Setting up local path storage PVC")
    _kubectl('apply', '-f', 'charts/local-path-storage.yaml')
    _kubectl('patch', 'storageclass', 'local-path', '-p', K3S_LOCAL_STORAGE_PATCH)
    if 'serviceaccount/tiller' not in _kubectl('get', 'serviceaccounts', '-A', '-o', 'name'):
        log.info("Setting up serviceaccount for tiller")
        _kubectl('create', 'serviceaccount', '--namespace', 'kube-system', 'tiller')
        _kubectl('create', 'clusterrolebinding', 'tiller-cluster-rule',
                 '--clusterrole=cluster-admin', '--serviceaccount=kube-system:tiller')

    log.info("Installing and upgrading helm")
    _helm('init', '--upgrade', '--history-max', 200, '--service-account', 'tiller')
    _helm('repo', 'update')

    wait_for_helm()

    for chart in config.CHARTS:
        helm_install(chart)


K3S_LOCAL_STORAGE_PATCH = '{"metadata":{"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'  # noqa: E501


@cli.command()
def runserver():
    log.info("Forking")
    if os.fork() == 0:
        execve(k3s_server_args())

    # wait until `kubectl get node` works
    wait_for_k3s()

    server_init()

    log.info('We are set! Sleeping forever')
    while True:
        _kubectl('get', '-A', 'all')
        time.sleep(15)

if __name__ == '__main__':
    cli()
