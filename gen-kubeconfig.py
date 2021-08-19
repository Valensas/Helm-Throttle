import os
from optparse import OptionParser

import yaml

from kubeconfig import *


def modify_yaml_dict(kube_config_path, kube_context):
    with open(kube_config_path, "r") as file:

        kubeconfig = yaml.safe_load(file)
        if kube_context is None or kube_context == "":
            kube_context = kubeconfig['current-context']

        new_kubeconfig = {
            'apiVersion': kubeconfig['apiVersion'],
            'kind': kubeconfig['kind'],
            'current-context': kube_context
        }

        current_context = get_context(kubeconfig, kube_context)
        if current_context is None:
            raise Exception()

        new_kubeconfig['contexts'] = [current_context]

        cluster = get_cluster(kubeconfig, current_context['context']['cluster'])

        if cluster is None:
            raise Exception()

        new_kubeconfig['clusters'] = [{
            'name': cluster['name'],
            'cluster': {
                "server": 'https://localhost:5000',
                "insecure-skip-tls-verify": True
            }
        }]

        user = get_user(kubeconfig, current_context['context']['user'])

        if user is None:
            raise Exception()

        new_kubeconfig['users'] = [user]
        return new_kubeconfig


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
    default=None,
    help="Enter an url",
)

parser.add_option(
    "-o",
    dest="temp_config",
    type="str",
    help="",
)
(options, args) = parser.parse_args()

kube_config_path = options.kube_config
kube_context = options.kube_context
temp_config = options.temp_config

with open(temp_config, 'w') as outfile:
    modified_yaml_dict = modify_yaml_dict(kube_config_path, kube_context)
    yaml.dump(modified_yaml_dict, outfile, default_flow_style=False)
