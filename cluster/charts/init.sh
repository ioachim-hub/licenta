#!/bin/bash

set -e

KUBE_CONTEXT="minikube"

minikube start \
--container-runtime=docker \
--docker-opt="default-ulimit=nofile=102400:102400" \
--kubernetes-version=1.20.10 \
--nodes=1 \
--install-addons=false \
--insecure-registry=srp.aa.minikube.com:5000 \
--vm-driver=virtualbox \
--driver=docker \
--cpus=max \
--memory=max

minikube ssh 'docker run -d -p 5000:5000 --restart=always --name registry docker.io/registry:2'

sudo sed -i '/minikube.com/d' /etc/hosts
MINIKUBE_IP=$(minikube ip)

cat <<EOF | sudo tee -a /etc/hosts
${MINIKUBE_IP} srp.aa.minikube.com
${MINIKUBE_IP} ingress.minikube.com
${MINIKUBE_IP} grafana.monitoring.minikube.com prometheus.monitoring.minikube.com
${MINIKUBE_IP} mongodb.aa.minikube.com
${MINIKUBE_IP} grafana.aa.minikube.com
EOF

