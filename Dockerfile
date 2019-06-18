FROM python:3.7-stretch


ENV DEBIAN_FRONTEND noninteractive
ENV PYTHONUNBUFFERED true

RUN set -e \
 && apt-get update -qq \
 && apt-get install  -qq -y --no-install-recommends \
    curl wget unzip

ADD docker/install.sh /install.sh
ENV K3S_VERSION v0.5.0
ENV HELM_VERSION v2.14.1
RUN /install.sh

RUN mkdir -p /opt/monitoring
WORKDIR /opt/monitoring
ADD Pipfile Pipfile.lock ./
RUN pip3 install pipenv \
 && pipenv install --system --deploy --ignore-pipfile

ADD . .

VOLUME /data
ENV KUBECONFIG /data/kubeconfig.yml
ENV HELM_HOME /data/helm

ADD docker/entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["runserver"]
