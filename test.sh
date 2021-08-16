#!/bin/sh
set -eux

SLEEP=$1
KUBE_API=$2

python3 $HELM_PLUGIN_DIR/main.py --sleep-interval=$SLEEP --kube-api=$KUBE_API &
helm $* --kube-api-server=https://localhost:5000
kill %

 ##python3 app.py --sleep-interval 10 --kube-api https://rancher.valensas.com/k8s/clusters/c-dvgp5