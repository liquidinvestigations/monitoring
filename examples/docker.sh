#!/bin/bash -ex

HERE=$(realpath "$(dirname "$(dirname "$0")")")

docker run \
  --env-file config.env \
  --detach \
  --restart always \
  --name monitoring \
  --privileged \
  --tmpfs /run \
  --tmpfs /var/run \
  --publish 6443:6443 \
  --volume $HERE:/opt/monitoring:ro \
  --volume $HERE/data:/data \
  liquidinvestigations/monitoring
