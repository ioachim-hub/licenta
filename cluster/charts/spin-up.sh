#!/bin/bash

# https://github.com/kubernetes/kubernetes/blob/master/CHANGELOG/CHANGELOG-1.23.md
KUBERNETES_VERSION=1.23.5

# https://github.com/kubernetes/kubernetes/blob/master/CHANGELOG/CHANGELOG-1.22.md
#KUBERNETES_VERSION=1.22.8

# https://github.com/kubernetes/kubernetes/blob/master/CHANGELOG/CHANGELOG-1.21.md
#KUBERNETES_VERSION=1.21.11

# https://github.com/kubernetes/kubernetes/blob/master/CHANGELOG/CHANGELOG-1.20.md
#KUBERNETES_VERSION=1.20.15

# https://github.com/kubernetes/kubernetes/blob/master/CHANGELOG/CHANGELOG-1.19.md
#KUBERNETES_VERSION=1.19.16

# https://github.com/kubernetes/kubernetes/blob/master/CHANGELOG/CHANGELOG-1.18.md
#KUBERNETES_VERSION=1.18.20

fixups () {
    sudo systemctl disable --now firewalld
    # https://kind.sigs.k8s.io/docs/user/known-issues/#pod-errors-due-to-too-many-open-files
    sudo sysctl fs.inotify.max_user_watches=524288
    sudo sysctl fs.inotify.max_user_instances=512

    return 0
}

cleanup () {
    sudo sed -i '/minikube.radcom.com/d' /etc/hosts

    return 0
}

container_network_connected () {
    container=$1
    network=$2

    sudo podman inspect ${container} -f "{{json .NetworkSettings.Networks }}" |python -m json.tool |grep ${network} &> /dev/null
    ret=$?

    return ${ret}
}

container_network_disconnect () {
    container=$1
    network=$2

    echo "[INFO] network: disconnecting container (${REGISTRY_NAME}) from network (${network})"
    container_network_connected ${container} ${network}
    ret=$?
    if [ ${ret} -ne 0 ]; then
        echo "[INFO] network: disconnecting container (${REGISTRY_NAME}) from network (${network}) - no need, not connected"

        return 0
    fi

    sudo podman network disconnect ${network} ${container}
    ret=$?
    if [ $ret -eq 0 ]; then
        echo "[INFO] network: disconnecting container (${REGISTRY_NAME}) from network (${network}) - OK"
    else
        echo "[INFO] network: disconnecting container (${REGISTRY_NAME}) from network (${network}) - FAILED"
    fi

    return ${ret}
}

container_network_connect () {
    container=$1
    network=$2

    echo "[INFO] network: connecting container (${REGISTRY_NAME}) to network (${network})"
    sudo podman network connect ${network} ${container}
    ret=$?
    if [ $ret -eq 0 ]; then
        echo "[INFO] network: connecting container (${REGISTRY_NAME}) to network (${network}) - OK"
    else
        echo "[INFO] network: connecting container (${REGISTRY_NAME}) to network (${network}) - FAILED"
    fi

    return ${ret}
}

start_registry () {
    echo "[INFO] start_registry"

    running=$(sudo podman inspect -f '{{.State.Running}}' "${REGISTRY_NAME}" 2>/dev/null)
    ret=$?
    exists=${ret}

    if [ "${exists}" -eq 0 ]; then
        status=$(sudo podman inspect -f '{{.State.Status}}' "${REGISTRY_NAME}" 2>/dev/null)
        ret=$?
        echo "status: ${status}"

        if [ "${running}" != "true" ]; then
            echo "[INFO] registry: exists, starting..."
            sudo podman start ${REGISTRY_NAME}
            ret=$?
            if [ $ret -ne 0 ]; then
                echo "[ERROR] registry: failed to start container, ret: ${ret}"
                return 1
            fi
        else
            echo "[INFO] registry exists and is already running..."
        fi
    else
        echo "[INFO] starting registry..."
        sudo podman run -d --name ${REGISTRY_NAME} docker.io/registry:2
        ret=$?
        if [ $ret -ne 0 ]; then
            echo "[ERROR] failed to start registry, ret: ${ret}"
            return 1
        fi
    fi

    container_network_disconnect ${REGISTRY_NAME} minikube
    ret=$?

    container_network_disconnect ${REGISTRY_NAME} kind
    ret=$?

    container_network_disconnect ${REGISTRY_NAME} podman
    ret=$?

    echo "[INFO] start_registry done"

    return 0
}

start_minikube () {
    echo "[INFO] start_minikube"
    echo "[INFO] checking if you have a previous instance..."
    minikube profile list &> /dev/null
    ret=$?
    if [ $ret -eq 0 ]; then
        echo "[WARNING] you already have a minikube, you will lose data"
        while true; do
            read -p "Do you want to remove the existing minikube (Y/N)?" yn
            case $yn in
                [N]* ) return 1;;
                [Y]* ) echo "okay..."; break;;
                * ) echo "Please answer Y or N.";;
            esac
        done
        echo "[INFO] deleting previous minikube..."
        minikube delete
        ret=$?
    else
        echo "[INFO] checking if you have a previous instance... NO"
    fi

    echo "[INFO] starting minikube..."
    minikube start \
    --container-runtime=docker \
    --docker-opt="default-ulimit=nofile=102400:102400" \
    --kubernetes-version=${KUBERNETES_VERSION} \
    --nodes=${NODE_COUNT} \
    --install-addons=false \
    --insecure-registry=${REGISTRY_NAME}:5000 \
    --driver=podman \
    --cpus=max \
    --memory=max
    ret=$?
    if [ $ret -ne 0 ]; then
        echo "[ERROR] failed to start minikube, ret: ${ret}"

        return ${ret}
    fi

    container_network_connect ${REGISTRY_NAME} minikube
    ret=$?
    if [ $ret -ne 0 ]; then
        return ${ret}
    fi

    container_network_disconnect ${REGISTRY_NAME} podman
    ret=$?
    if [ $ret -ne 0 ]; then
        return ${ret}
    fi

    REGISTRY_IP=$(sudo podman inspect  --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ${REGISTRY_NAME})
    ret=$?
    if [ $ret -ne 0 ]; then
        echo "[ERROR] failed to get registry ip, ret: ${ret}"
        return 1
    fi
    echo "[INFO] REGISTRY_IP: ${REGISTRY_IP}"
    ipcalc -cs ${REGISTRY_IP}
    ret=$?
    if [ $ret -ne 0 ]; then
        echo "[ERROR] invalid ip"
        return 1
    fi

    NODE_IP=$(minikube ip)
    ret=$?
    if [ $ret -ne 0 ]; then
        echo "[ERROR] failed to get minikube ip, ret: ${ret}"
        return 1
    fi
    echo "[INFO] NODE_IP: ${NODE_IP}"

    echo "[INFO] start_minikube DONE"

    return 0
}

# kind: to switch kubernetes version, check https://hub.docker.com/r/kindest/node/tags
# TODO: supports IPv6 however rabbitmq will fail to start, we need to force ipv6_only flag
# ipFamily: ipv6
# TODO: configurable workers
# - role: worker
#  image: docker.io/kindest/node:v1.20.15
start_kind () {
    echo "[INFO] start_kind"
    cat <<EOF > /tmp/kind.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: kind
nodes:
- role: control-plane
  image: docker.io/kindest/node:v${KUBERNETES_VERSION}
  kubeadmConfigPatches:
  - |
      kind: InitConfiguration
      nodeRegistration:
        kubeletExtraArgs:
          node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 6443
    hostPort: 6443
    protocol: TCP
  - containerPort: 5433
    hostPort: 5433
    protocol: TCP
  - containerPort: 27017
    hostPort: 27017
    protocol: TCP
  - containerPort: 6379
    hostPort: 6379
    protocol: TCP
  - containerPort: 5672
    hostPort: 5672
    protocol: TCP
  - containerPort: 9093
    hostPort: 9093
    protocol: TCP
networking:
  ipFamily: ipv4
  apiServerAddress: "::"
  apiServerPort: 6443
containerdConfigPatches:
- |-
  [plugins."io.containerd.grpc.v1.cri".registry.mirrors."${REGISTRY_NAME}:5000"]
    endpoint = ["http://${REGISTRY_NAME}:5000"]
EOF
    KIND="sudo KIND_EXPERIMENTAL_PROVIDER=podman ${HOME}/bin/kind"
    echo "[INFO] kind: deleting old cluster"
    ${KIND} delete cluster --name kind
    ret=$?
    if [ $ret -ne 0 ]; then
        echo "[ERROR] failed"
        return $ret
    fi

    echo "[INFO] kind: creating cluster"
    ${KIND} create cluster --config=/tmp/kind.yaml
    ret=$?
    if [ $ret -ne 0 ]; then
        echo "[ERROR] failed"
        return $ret
    fi

    echo "[INFO] kind: copying config"
    ${KIND} export kubeconfig --kubeconfig $HOME/.kube/config
    ret=$?
    if [ $ret -ne 0 ]; then
        echo "[ERROR] failed"
        return $ret
    fi

    NODE_IP=$(sudo podman inspect  --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' kind-control-plane)
    echo "[INFO] kind: NODE_IP: ${NODE_IP}"
    echo "[INFO] kind: configuring cluster..."
    kubectl config set-cluster kind-kind --server=https://${NODE_IP}:6443 --insecure-skip-tls-verify
    ret=$?
    if [ $ret -ne 0 ]; then
        echo "[ERROR] failed"
        return $ret
    fi

    echo "[INFO] registry: connecting to kind network"
    sudo podman network connect kind ${REGISTRY_NAME}
    ret=$?
    if [ $ret -ne 0 ]; then
        echo "[ERROR] failed"
        return $ret
    fi

    REGISTRY_IP=$(sudo podman inspect  --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ${REGISTRY_NAME})
    echo "[INFO] REGISTRY_IP: ${REGISTRY_IP}"

    echo "[INFO] kind: deleting standard sc"
    ${KUBECTL} delete sc/standard
    ret=$?
    if [ $ret -ne 0 ]; then
        echo "[ERROR] failed"
        return $ret
    fi

    echo "[INFO] kind: removing taint master"
    ${KUBECTL} taint nodes --all node-role.kubernetes.io/master-
    ret=$?
    if [ $ret -ne 0 ]; then
        echo "[ERROR] FIX ME"
    fi

    echo "[INFO] kind: checking registry connectivity"
    sudo podman exec -it kind-control-plane curl http://${REGISTRY_NAME}:5000/v2/_catalog
    ret=$?
    if [ $ret -ne 0 ]; then
        echo "[ERROR] failed"
        return $ret
    fi

    echo "[INFO] start_kind DONE"
}

add_hosts() {
    if [ -z "${REGISTRY_IP}" ]; then
        echo "[ERROR] REGISTRY_IP empty"
        return 1
    fi

    if [ -z "${NODE_IP}" ]; then
        echo "[ERROR] NODE_IP empty"
        return 1
    fi

    cat <<EOF | sudo tee -a /etc/hosts
# BEGIN minikube.radcom.com
${REGISTRY_IP} srp.aa.minikube.radcom.com
${NODE_IP} ingress.minikube.radcom.com
${NODE_IP} vertica-upstream.aa.minikube.radcom.com
${NODE_IP} vertica.aa.minikube.radcom.com
${NODE_IP} mongodb.aa.minikube.radcom.com
${NODE_IP} mongosqld.aa.minikube.radcom.com
${NODE_IP} rabbitmq.aa.minikube.radcom.com
${NODE_IP} redis.aa.minikube.radcom.com
${NODE_IP} alertmanager.aa.minikube.radcom.com
${NODE_IP} celery-flower.aa.minikube.radcom.com
${NODE_IP} prymitive-karma.aa.minikube.radcom.com
${NODE_IP} grafana.aa.minikube.radcom.com
${NODE_IP} devui.aa.minikube.radcom.com
${NODE_IP} restapi.aa.minikube.radcom.com
${NODE_IP} celerybeat.aa.minikube.radcom.com
${NODE_IP} grafana-restapi.aa.minikube.radcom.com
${NODE_IP} prometheus-alertmanager.aa.minikube.radcom.com

${NODE_IP} grafana.monitoring.minikube.radcom.com
${NODE_IP} alertmanager.monitoring.minikube.radcom.com
${NODE_IP} prometheus.monitoring.minikube.radcom.com
# END minikube.radcom.com
EOF

    return 0
}

deploy () {
    if [ ${ENABLE_K8S_INFRA_IMAGES} -eq 1 ]; then
        ./mgr.sh --file_filter k8s-infra > /tmp/mgr-k8s-infra.log &
        MGR_K8S_INFRA_PID=$!
    fi

    if [ ${ENABLE_AA_INFRA_IMAGES} -eq 1 ]; then
        ./mgr.sh --file_filter aa-infra > /tmp/mgr-aa-infra.log &
        MGR_AA_INFRA_PID=$!
    fi

    if [ ${ENABLE_AA_LOGIC_IMAGES} -eq 1 ]; then
        ./mgr.sh --file_filter aa-logic > /tmp/mgr-aa-logic.log &
        MGR_AA_LOGIC_PID=$!
    fi

    # image build wait
    if [ ${ENABLE_K8S_INFRA_IMAGES} -eq 1 ]; then
        echo "[INFO] k8s-infra images: waiting..."
        wait ${MGR_K8S_INFRA_PID}
        ret=$?
        if [ $ret -ne 0 ]; then
            echo "[ERROR] Error on k8s-infra building, waiting..."
            wait
            echo "[ERROR] ret: ${ret}"
            return $ret
        fi
        echo "[INFO] k8s-infra images: DONE"
    fi

    if [ ${ENABLE_AA_INFRA_IMAGES} -eq 1 ]; then
        echo "[INFO] aa-infra images: waiting..."
        wait ${MGR_AA_INFRA_PID}
        ret=$?
        if [ $ret -ne 0 ]; then
            echo "[ERROR] Error on aa-infra building, waiting..."
            wait
            echo "[ERROR] ret: ${ret}"
            return $ret
        fi

        echo "[INFO] aa-infra images: DONE"
    fi

    if [ ${ENABLE_AA_LOGIC_IMAGES} -eq 1 ]; then
        echo "[INFO] aa-logic images: waiting..."
        wait ${MGR_AA_LOGIC_PID}
        ret=$?
        if [ $ret -ne 0 ]; then
            echo "[ERROR] Error on aa-logic building, waiting..."
            wait
            echo "[ERROR] ret: ${ret}"
            return $ret
        fi

        echo "[INFO] aa-logic images: DONE"
    fi

    if [ ${ENABLE_K8S_INFRA_HELMFILE} -eq 1 ]; then
        echo "[INFO] k8s-infra: deploying"
        cd k8s-infra

        echo "[INFO] k8s-infra: prom first..."
        ${HELMFILE} --selector name=prom sync --skip-deps
        ret=$?
        if [ $ret -ne 0 ]; then
            echo "[ERROR] k8s-infra prom failed"
            return $ret
        fi
        echo "[INFO] k8s-infra: prom DONE"

        echo "[INFO] k8s-infra: now rest of them..."
        ${HELMFILE} --selector name!=prom sync --skip-deps
        ret=$?
        if [ $ret -ne 0 ]; then
            echo "[ERROR] k8s-infra failed"
            return $ret
        fi
        echo "[INFO] k8s-infra: DONE"

        cd ..
    fi

    if [ ${ENABLE_AA_INFRA_HELMFILE} -eq 1 ]; then
        echo "[INFO] aa-infra: deploying..."
        cd aa-infra
        ${HELMFILE} sync
        ret=$?
        if [ $ret -ne 0 ]; then
            echo "[ERROR] aa-infra failed"
            return $ret
        fi

        echo "[INFO] aa-infra: DONE"
        cd ..

        echo "[INFO] vertica-init: running"
        export KUBECTL_CTX
        ./vertica-init.sh
        ret=$?
        if [ $ret -ne 0 ]; then
            echo "[ERROR] vertica-init: failed"
            return $ret
        fi

        echo "[INFO] vertica-init: DONE"
    fi

    echo "[INFO] aa-logic: deploying"
    cd aa-logic
    for INSTALL_NAME in aim-grafana-mariadb \
    aim-grafana-plugins \
    aim-grafana-log \
    aim-grafana-configmaps \
    aim-grafana-restapi \
    aim-grafana \
    aim-restapi \
    aim-celery-misc \
    aim-celery-beat \
    aim-celery-forecast \
    aim-celery-exceptioncheck \
    aim-celery-alarmcheck \
    aim-celery-grafana-live \
    aim-devui \
    ; do
        echo "INSTALL_NAME: ${INSTALL_NAME}"
        ${HELMFILE} --selector name=${INSTALL_NAME} sync
        ret=$?
        if [ $ret -ne 0 ]; then
            echo "[ERROR] aa-logic: ${INSTALL_NAME} failed"
            return $ret
        fi
    done
    cd ..

    if [ ${ENABLE_AA_LOGIC_HELMFILE} -eq 1 ]; then
        echo "[INFO] aa-logic: deploying..."
        cd aa-logic
        ${HELMFILE} sync
        cd ..
        echo "[INFO] aa-logic: DONE"
    fi

    return 0
}

NODE_COUNT=1
REGISTRY_NAME="srp.aa.minikube.radcom.com"

# in case of issues
# sudo podman stop srp.aa.minikube.radcom.com
# sudo podman rm srp.aa.minikube.radcom.com

ENABLE_K8S_INFRA_IMAGES=1
ENABLE_K8S_INFRA_HELMFILE=1

ENABLE_AA_INFRA_IMAGES=1
ENABLE_AA_INFRA_HELMFILE=1

ENABLE_AA_LOGIC_IMAGES=1
ENABLE_AA_LOGIC_HELMFILE=0

. env.sh

HELMFILE="helmfile --kube-context=${KUBECTL_CTX}"
KUBECTL="kubectl --context=${KUBECTL_CTX}"

echo "[INFO] TECHNOLOGY: ${TECHNOLOGY}"

# logic
fixups
ret=$?
if [ $ret -ne 0 ]; then
    echo "[ERROR] fixup failed, ret: ${ret}"
    exit 1
fi

cleanup
ret=$?
if [ $ret -ne 0 ]; then
    echo "[ERROR] cleanup failed, ret: ${ret}"
    exit 1
fi

start_registry
ret=$?
if [ $ret -ne 0 ]; then
    echo "[ERROR] start_registry failed, ret: ${ret}"
    exit 1
fi

if [ "${TECHNOLOGY}" == "kind" ]; then
    start_kind
    elif [ "${TECHNOLOGY}" == "minikube" ]; then
    start_minikube
fi
ret=$?
if [ $ret -ne 0 ]; then
    echo "[ERROR] start failed, ret: ${ret}"
    exit 1
fi

add_hosts
ret=$?
if [ $ret -ne 0 ]; then
    echo "[ERROR] add_hosts failed, ret: ${ret}"
    exit 1
fi

deploy
ret=$?
if [ $ret -ne 0 ]; then
    echo "[ERROR] deploy failed, ret: ${ret}"
    exit 1
fi
