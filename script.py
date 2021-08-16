import yaml
from optparse import OptionParser

parser = OptionParser()
parser.add_option(
    "--kube-config",
    dest="kube_config",
    type="str",
    default="/Users/okanokumusoglu/.kube/config",
    help="Enter a time-interval",
)
parser.add_option(
    "--kube-context",
    dest="kube_context",
    type="str",
    default="helm-proxy",
    help="Enter an url",
)
(options, args) = parser.parse_args()
kube_config = options.kube_config
kube_context = options.kube_context

with open(kube_config, "r") as file:
    dict = yaml.safe_load(file)
    contexts = dict['contexts']
    cluster_name = None
    for element in contexts:
        name = element['name']
        if name == kube_context:
            cluster_name = element['context']['cluster']
            break
    clusters = dict['clusters']
    server_name = None
    for element in clusters:
        name = element['name']
        if name == cluster_name:
            server_name = element['cluster']['server']
            break

    print(server_name)
