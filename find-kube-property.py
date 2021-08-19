import base64
import os
import sys

from kubeconfig import *
import yaml
from optparse import OptionParser

parser = OptionParser()
parser.add_option(
    "-o",
    dest="output",
    type="str",
    help="Directory to use to write temporary files",
)
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
output = options.output


def get_data_property(base, property, filename):
    if property in base:
        return base[property]
    property = property + '-data'
    if property not in base:
        return None

    with open(filename, 'wb') as f:
        data = base64.b64decode(base[property])
        f.write(data)
    return filename


with open(kube_config, "r") as file:
    kubeconfig = yaml.safe_load(file)
    if kube_context is None or kube_context == "":
        kube_context = kubeconfig['current-context']
    context = get_context(kubeconfig, kube_context)
    cluster = get_cluster(kubeconfig, context['context']['cluster'])
    user = get_user(kubeconfig, context['context']['user'])
    argument = args[0]
    if argument == 'server':
        print(cluster['cluster']['server'])
    elif argument == 'insecure-skip-tls-verify' and 'insecure-skip-tls-verify' in cluster['cluster']:
        print(cluster['cluster']['insecure-skip-tls-verify'])
    elif argument == 'certificate-authority':
        certificate_authority = get_data_property(cluster['cluster'], 'certificate-authority', f'{output}/ca.crt')
        if certificate_authority is not None:
            print(certificate_authority)
    elif argument == 'client-certificate':
        client_certificate = get_data_property(user['user'], 'client-certificate', f"{output}/client.crt")
        if client_certificate:
            print(client_certificate)
    elif argument == 'client-key':
        client_key = get_data_property(user['user'], 'client-key', f"{output}/client.key")
        if client_key:
            print(client_key)
