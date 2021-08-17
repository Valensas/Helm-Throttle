#!/bin/sh
set -eux

KUBECONFIG="/Users/okanokumusoglu/.kube/config"
KUBECONTEXT="helm-proxy"
##KUBE_API=$2
KUBEAPI=$(python3 $HELM_PLUGIN_DIR/script.py --kube-config=$KUBECONFIG --kube-context=$KUBECONTEXT)
echo $KUBEAPI
echo $*
python3 $HELM_PLUGIN_DIR/main.py --kube-api=$KUBEAPI &
sleep 1

HELM_KUBEAPISERVER=https://localhost:5000 helm $*
#kill %

 #python3 main.py --sleep-interval 10 --kube-api https://rancher.valensas.com/k8s/clusters/c-dvgp5