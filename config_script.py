import yaml
from unipath import Path
import os
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
    default=None,
    help="Enter an url",
)

parser.add_option(
    "--temp-config",
    dest="temp_config",
    type="str",
    default=Path(os.path.expanduser("~/.kube/config")
                 ).parent+"/config_temp",
    help="",
)
(options, args) = parser.parse_args()

kube_config = options.kube_config
kube_context = options.kube_context
temp_config = options.temp_config


def modify_yaml_dict(kube_config, kube_context):
    with open(kube_config, "r") as file:

        yaml_dict = yaml.safe_load(file)
        if kube_context == "":
            kube_context = yaml_dict['current-context']

        new_yaml_dict = dict()

        new_yaml_dict['apiVersion'] = yaml_dict['apiVersion']
        new_yaml_dict['kind'] = yaml_dict['kind']
        new_yaml_dict['clusters'] = []
        new_yaml_dict['users'] = []
        new_yaml_dict['contexts'] = []
        new_yaml_dict['current-context'] = kube_context

        cluster_name = None
        for element in yaml_dict['contexts']:
            name = element['name']
            if name == kube_context:
                cluster_name = element['context']['cluster']
                new_yaml_dict['contexts'].append(element)
                break

        for element in yaml_dict['clusters']:
            name = element['name']
            if name == cluster_name:
                element['cluster']['server'] = "https://localhost:5000"
                element['cluster']['insecure-skip-tls-verify'] = True
                new_yaml_dict['clusters'].append(element)
                break

        for element in yaml_dict['users']:
            name = element['name']
            if name == cluster_name:
                new_yaml_dict['users'].append(element)
                break

        return new_yaml_dict


with open(temp_config, 'w') as outfile:
    modified_yaml_dict = modify_yaml_dict(kube_config, kube_context)
    yaml.dump(modified_yaml_dict, outfile, default_flow_style=False)

# 1- environmet variable cevir
# 2- kubecontext cevir helm-context varsa onu al yoksa current-context alicaz
