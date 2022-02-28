#!/bin/bash

set -e

KUBE_CONTEXT="minikube"

minikube start \
--container-runtime=docker \
--docker-opt="default-ulimit=nofile=102400:102400" \
--kubernetes-version=1.21.9 \
--nodes=1 \
--install-addons=false \
--insecure-registry=srp.minikube.com:5000 \
--vm-driver=virtualbox \
--driver=podman \
--cpus=max \
--memory=max

minikube ssh 'docker run -d -p 5000:5000 --restart=always --name registry docker.io/registry:2'

sudo sed -i '/minikube.com/d' /etc/hosts
MINIKUBE_IP=$(minikube ip)

cat <<EOF | sudo tee -a /etc/hosts
${MINIKUBE_IP} srp.minikube.com
${MINIKUBE_IP} ingress.minikube.com
${MINIKUBE_IP} grafana.monitoring.minikube.com prometheus.monitoring.minikube.com
${MINIKUBE_IP} mongodb.minikube.com
${MINIKUBE_IP} grafana.minikube.com
EOF
