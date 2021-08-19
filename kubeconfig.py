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
