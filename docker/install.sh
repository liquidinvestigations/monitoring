#!/bin/bash -ex

cd $(mktemp -d)

echo "Installing k3s"
wget --quiet https://github.com/rancher/k3s/releases/download/$K3S_VERSION/k3s -O /bin/k3s
chmod +x /bin/k3s

echo "Installing helm"
wget --quiet https://get.helm.sh/helm-$HELM_VERSION-linux-amd64.tar.gz
tar xzvf helm-$HELM_VERSION-linux-amd64.tar.gz
cp linux-amd64/helm /bin/helm
cp linux-amd64/tiller /bin/tiller

echo "Are we here?"
k3s --version
