#!/bin/sh
set -eux

trap finish EXIT
function finish {
  set +eu
  if test -z "$OUT";then
    rm $OUT
    fi
  kill %
}

KUBECONTEXT=${HELM_KUBECONTEXT:-""}
KUBECONFIG=${KUBECONFIG:-~/.kube/config}

python3 -m venv ${HELM_PLUGIN_DIR}/venv
source ${HELM_PLUGIN_DIR}/venv/bin/activate
pip install -r ${HELM_PLUGIN_DIR}/requirements.txt

KUBEAPI=$(python3 $HELM_PLUGIN_DIR/script.py --kube-config="${KUBECONFIG}"  --kube-context="${KUBECONTEXT}")
TIME_INTERVAL=5
export TIME_INTERVAL
export KUBEAPI


python3 $HELM_PLUGIN_DIR/main.py &
${HELM_PLUGIN_DIR}/wait-for-it.sh -h 127.0.0.1 -p 5000 -t 5
OUT="$(mktemp)"
python3 $HELM_PLUGIN_DIR/config_script.py --kube-config="${KUBECONFIG}"  --kube-context="${KUBECONTEXT}" --temp-config="${OUT}"

HELM_KUBEAPISERVER=https://localhost:5000 helm $* --kubeconfig="${OUT}"
