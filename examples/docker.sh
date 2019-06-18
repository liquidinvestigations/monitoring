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
  --publish 6480 \
  --publish 6443 \
  --publish 6643 \
  --publish 6463 \
  --publish 6663 \
  --publish 6446 \
  liquidinvestigations/monitoring
