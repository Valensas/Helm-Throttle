import base64


def get_kubeconfig_value(config, value, type):
    for element in config[type]:
        name = element['name']
        if name == value:
            return element
    return None


def get_context(config, context):
    return get_kubeconfig_value(config, context, 'contexts')


def get_cluster(config, cluster):
    return get_kubeconfig_value(config, cluster, 'clusters')


def get_user(config, user):
    return get_kubeconfig_value(config, user, 'users')


def generate_proxied_kubeconfig(kubeconfig, kube_context):
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
            "server": 'https://127.0.0.1:5001',
            "insecure-skip-tls-verify": True
        }
    }]

    user = get_user(kubeconfig, current_context['context']['user'])

    if user is None:
        raise Exception()

    new_kubeconfig['users'] = [user]
    return new_kubeconfig


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