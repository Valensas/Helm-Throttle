#!/bin/sh
set -eux

trap finish EXIT

function finish {
  kill %
}

KUBECONTEXT="helm-proxy"
KUBECONFIG=${KUBECONFIG:-~/.kube/config}

python3 -m venv ${HELM_PLUGIN_DIR}/venv
source ${HELM_PLUGIN_DIR}/venv/bin/activate
pip install -r ${HELM_PLUGIN_DIR}/requirements.txt

KUBEAPI=$(python3 $HELM_PLUGIN_DIR/script.py --kube-config="${KUBECONFIG}"  --kube-context=$KUBECONTEXT)

python3 $HELM_PLUGIN_DIR/main.py --kube-api=$KUBEAPI &
${HELM_PLUGIN_DIR}/wait-for-it.sh -h 127.0.0.1 -p 5000 -t 5

HELM_KUBEAPISERVER=https://localhost:5000 helm $*