import atexit
import os
import stat
import tempfile
from optparse import OptionParser

import yaml

import kubeconfig
from kube_api_proxy import KubeApiProxy

parser = OptionParser()
parser.add_option(
    "--tmp-kube-config",
    dest="tmp_kube_config_path",
    type="str",
    help="Path to temporary kubeconfig file",
)
parser.add_option(
    "--throttle",
    dest="throttle",
    type="int",
    help="Throttle duration between requests, in seconds. Defaults to 10.",
    default=10
)
parser.add_option(
    "--debug",
    dest="debug",
    default=False,
    action="store_true",
    help="Run in debugging mode",
)

(options, _) = parser.parse_args()

original_kube_config_path = os.environ.get('HELM_KUBECONFIG',
                                           os.environ.get(
                                               'KUBECONFIG',
                                               os.path.expanduser("~/.kube/config")))
with open(original_kube_config_path, "r") as file:
    original_kube_config = yaml.safe_load(file)

kube_context = os.environ.get('HELM_KUBECONTEXT', original_kube_config['current-context'])
if kube_context == '':
    kube_context = original_kube_config['current-context']

proxied_kubeconfig = kubeconfig.generate_proxied_kubeconfig(original_kube_config, kube_context)

with open(options.tmp_kube_config_path, 'w') as f:
    f.write(yaml.dump(proxied_kubeconfig))

os.chmod(options.tmp_kube_config_path, stat.S_IWUSR | stat.S_IRUSR)

cluster = kubeconfig.get_cluster(original_kube_config, kube_context)['cluster']
api_server = cluster['server']

tmp_dir = tempfile.mkdtemp()


@atexit.register
def cleanup():
    os.rmdir(tmp_dir)


ca_cert = kubeconfig.get_data_property(cluster, 'certificate-authority', f'{tmp_dir}/ca.crt')

kube_context_data = kubeconfig.get_context(original_kube_config, kube_context)['context']
user = kubeconfig.get_user(original_kube_config, kube_context_data['user'])['user']

client_cert = kubeconfig.get_data_property(user, 'client-certificate', f'{tmp_dir}/client.crt')
client_key = kubeconfig.get_data_property(user, 'client-key', f'{tmp_dir}/client.key')

proxy = KubeApiProxy(
    kube_api=api_server,
    throttle_interval=options.throttle,
    ca_cert=ca_cert,
    skip_tls_verification=cluster.get('insecure-skip-tls-verify', False),
    client_cert=client_cert,
    client_key=client_key,
    debug=options.debug
)

proxy.run()
