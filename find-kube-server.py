import os

from kubeconfig import *
import yaml
from optparse import OptionParser

parser = OptionParser()
parser.add_option(
    "--kube-config",
    dest="kube_config",
    type="str",
    default=os.path.expanduser("~/.kube/config"),
    help="Enter a time-interval",
)
parser.add_option(
    "--kube-context",
    dest="kube_context",
    type="str",
    help="Enter an url",
)
(options, args) = parser.parse_args()
kube_config = options.kube_config
kube_context = options.kube_context

with open(kube_config, "r") as file:
    kubeconfig = yaml.safe_load(file)
    if kube_context is None or kube_context == "":
        kube_context = kubeconfig['current-context']
    context = get_context(kubeconfig, kube_context)
    cluster = get_cluster(kubeconfig, context['context']['cluster'])
    print(cluster['cluster']['server'])
