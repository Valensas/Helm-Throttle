#!/bin/bash

SERVER_OPTS=""

if [ "$HELM_DEBUG" "=" "true" ]; then
  set -x
  SERVER_OPTS="${SERVER_OPTS} --debug"
fi

set -eu

function cleanup {
  set +eu
  if test -d "$TMP_DIR" ;then
    rm -rf "$TMP_DIR"
  fi
  kill %
}

trap cleanup EXIT
trap cleanup INT

source ${HELM_PLUGIN_DIR}/venv/bin/activate
TMP_DIR="$(mktemp -d)"
NEW_KUBECONFIG="$TMP_DIR/kubeconfig"

SERVER_OPTS="${SERVER_OPTS} --tmp-kube-config ${NEW_KUBECONFIG}"

set +e
HELM_ARGS=()
for var in "$@"; do
    # Ignore known bad arguments
    shopt -s extglob
    if [[ "$var" = --throttle=* ]]; then
        SERVER_OPTS="${SERVER_OPTS} ${var}"
        continue
    fi
    HELM_ARGS[${#HELM_ARGS[@]}]="$var"
done
set -e

python $HELM_PLUGIN_DIR/server.py ${SERVER_OPTS} &
${HELM_PLUGIN_DIR}/wait-for-it.sh 127.0.0.1:5001 -t 5 --quiet

export KUBECONFIG="${NEW_KUBECONFIG}"
unset HELM_KUBEAPISERVER


helm "${HELM_ARGS[@]}"