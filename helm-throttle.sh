#!/bin/sh

if [ "$HELM_DEBUG" "=" "true" ]; then
  set -x
  export DEBUG="1"
else
  REDIRECT=""
fi

set -eu

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

source ${HELM_PLUGIN_DIR}/venv/bin/activate

export KUBEAPI=$(python3 $HELM_PLUGIN_DIR/find-kube-server.py --kube-config="${KUBECONFIG}"  --kube-context="${KUBECONTEXT}")
export TIME_INTERVAL=5

python3 $HELM_PLUGIN_DIR/throttle-proxy.py &
${HELM_PLUGIN_DIR}/wait-for-it.sh -h 127.0.0.1 -p 5000 -t 5 --quiet
OUT="$(mktemp)"
python3 $HELM_PLUGIN_DIR/gen_kubeconfig.py --kube-config="${KUBECONFIG}"  --kube-context="${KUBECONTEXT}" -o "${OUT}"

helm $* --kubeconfig="${OUT}"

