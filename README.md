# Helm Throttle

A Helm plugin to throttle deployments of controllers. This plugin solves the issue where a big Helm charts that defines many
Deployments and/or Statefulsets is installed or updated results in a big number of Pods being created. By throttling the rate
at which controllers are created or updated, the number of rollouts can also be limited. This will also reduce the number of
nodes a cluster autoscaler has to scale up or resource congestions on your nodes during rollouts.

## Usage

To install Helm Throttle, run the following command:

```bash
helm plugin install https://github.com/Valensas/Helm-Throttle
```

Make sure the `timeout` command is on your path. On macOS systems, it can be installed using brew: `brew install coreutils`.

Deploy your charts with throttling:

```bash
helm throttle install my-chart my-repo/my-chart
```

This will make sure every creation or update has 10 seconds between them. You can also specify a custom throttling interval:

```bash
helm throttle install my-chart my-repo/my-chart -t 5
```

All commands and options you use are directly forwarded to helm, so you can use any command and option as you normally would
trough this plugin.

Example:

```
$ helm throttle version --short
v3.12.0+gc9f554d
```

## How does it work?

This plugin creates temporary proxy on your machine where all requests are sent instead of your Kubernetes API. The proxy then
forwards the requests to Kubernetes by delaying them if necessary.

## Limitations

This plugin is only tested with bearer token and client TLS authentication. If you're using other kinds of authentication, you might
encounter issues.
