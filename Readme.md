# Bunch of monitoring software

This repository uses [k3s]() to deploy a bunch of monitoring backends and
dashboards configured to work with Consul and Nomad, all this in
a single isolated (althrough privileged) Docker container.


## Software installed

All these are stable helm charts:

- Sentry
- Prometheus, configured for Nomad
- Telegraf, configured for Consul
- Grafana


## Usage

First, set up your environment variabes:

```bash
cp examples/config.env .
vim config.env
```

Then, run the single monolith container, taking care to mount `/data` to a volume and to map your ports:

```bash
docker run
  --env-file config.env \
  --detach \
  --restart always \
  --name monitoring \
  --privileged \
  --tmpfs /run \
  --tmpfs /var/run \
  --publish 6443:6443 \
  --publish 6480:6480 \
  --volume /tmp/monitoring/data:/data \
  liquidinvestigations/monitoring
```

You can get all sorts of secrets back from the deployment by running scripts in the container:

```bash
docker exec monitoring healthcheck
docker exec monitoring getkubeconfig
docker exec monitoring sentry getdsn project1
docker exec monitoring shell
```

## Configuration

Configuration is passed through environment variables.

Configs about your already-running Nomad and Consul servers:

- `NOMAD_URL`
- `CONSUL_URL`


Configs about what ports to listen on:

- `K3S_HTTPS_PORT`, defaults 6443
- `SENTRY_HTTP_PORT`, defaults 6643
- `TELEGRAF_HTTP_PORT`, defaults 6463
- `GRAFANA_HTTP_PORT`, defaults 6663
- `PROMETHEUS_HTTP_PORT`, defaults 6446
