#!/bin/sh

if [ "$HELM_DEBUG" "=" "true" ]; then
  set -x
  export DEBUG="1"
fi

set -eu

trap finish EXIT
function finish {
  set +eu
  if test -d "$TMP_DIR" ;then
    rm -rf "$TMP_DIR"
  fi
  kill %
}

KUBECONTEXT=${HELM_KUBECONTEXT:-""}
KUBECONFIG=${KUBECONFIG:-~/.kube/config}

source ${HELM_PLUGIN_DIR}/venv/bin/activate
TMP_DIR="$(mktemp -d)"

export KUBEAPI=${HELM_KUBEAPISERVER:-$(python3 $HELM_PLUGIN_DIR/find-kube-property.py server                   --kube-config="${KUBECONFIG}" --kube-context="${KUBECONTEXT}" -o "${TMP_DIR}")}
export INSECURE_SKIP_TLS_VERIFY=$(python3      $HELM_PLUGIN_DIR/find-kube-property.py insecure-skip-tls-verify --kube-config="${KUBECONFIG}" --kube-context="${KUBECONTEXT}" -o "${TMP_DIR}")
export CA_CERT=$(python3                       $HELM_PLUGIN_DIR/find-kube-property.py certificate-authority    --kube-config="${KUBECONFIG}" --kube-context="${KUBECONTEXT}" -o "${TMP_DIR}")
export CLIENT_CERT=$(python3                   $HELM_PLUGIN_DIR/find-kube-property.py client-certificate       --kube-config="${KUBECONFIG}" --kube-context="${KUBECONTEXT}" -o "${TMP_DIR}")
export CLIENT_KEY=$(python3                    $HELM_PLUGIN_DIR/find-kube-property.py client-key               --kube-config="${KUBECONFIG}" --kube-context="${KUBECONTEXT}" -o "${TMP_DIR}")
export TIME_INTERVAL=5

python3 $HELM_PLUGIN_DIR/throttle-proxy.py &
${HELM_PLUGIN_DIR}/wait-for-it.sh -h 127.0.0.1 -p 5000 -t 5 --quiet
NEW_KUBECONFIG="$TMP_DIR/kubeconfig"
touch "${NEW_KUBECONFIG}"
chmod 600 "${NEW_KUBECONFIG}"
python3 $HELM_PLUGIN_DIR/gen-kubeconfig.py --kube-config="${KUBECONFIG}"  --kube-context="${KUBECONTEXT}" -o "${NEW_KUBECONFIG}"

export KUBECONFIG="${NEW_KUBECONFIG}"
unset HELM_KUBEAPISERVER
helm $*