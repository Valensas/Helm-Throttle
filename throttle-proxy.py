import logging
import os
import re
import time
import warnings
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, Response
from flask import request
from requests import Session
from urllib3.exceptions import InsecureRequestWarning

app = Flask(__name__)

kube_api_url = os.environ.get("KUBEAPI")
if kube_api_url is None:
    raise Exception("URL Not Given!")
kube_api_url = kube_api_url.removesuffix('/')

throttle_interval = int(os.environ.get("THROTTLE_INTERVAL", 10))

last_write_timestamp = None

regex_list = [
    "^/apis/apps/v1/namespaces/[^/]+/statefulsets(/[^/]+)?$",
    "^/apis/apps/v1/namespaces/[^/]+/deployments(/[^/]+)?$",
]

executor = ThreadPoolExecutor(1)
session = Session()


def is_write():
    return request.method == "POST" or request.method == "PUT" or request.method == "PATCH"


def should_throttle(path):
    global last_write_timestamp
    if last_write_timestamp is None:
        return False

    resource_is_listed = any(re.search(element, path) for element in regex_list)
    is_dry_run = request.args.get("dryRun") == "All"
    return is_write() and resource_is_listed and not is_dry_run


def proxy_request():
    resp = session.request(
        params=request.args,
        method=request.method,
        url=kube_api_url + request.path,
        headers={key: value for (key, value) in request.headers if key.lower() != "host"},
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False,
    )
    excluded_headers = [
        "content-encoding",
        "content-length",
        "transfer-encoding",
        "connection",
    ]
    headers = [
        (name, value)
        for (name, value) in resp.raw.headers.items()
        if name.lower() not in excluded_headers
    ]
    return Response(resp.content, resp.status_code, headers)


if os.environ.get('CA_CERT') and os.environ.get('CA_CERT') != '':
    session.verify = os.environ.get('CA_CERT')

if os.environ.get('INSECURE_SKIP_TLS_VERIFY') and os.environ.get('INSECURE_SKIP_TLS_VERIFY').lower() == 'true':
    session.verify = False
    # Disable SSL Warnings
    warnings.simplefilter('ignore', InsecureRequestWarning)

if os.environ.get('CLIENT_CERT') and os.environ.get('CLIENT_CERT') != '':
    session.cert = (os.environ.get('CLIENT_CERT'), os.environ.get('CLIENT_KEY'))

@app.route(
    "/", defaults={"path": ""}, methods=["POST", "GET", "PUT", "PATCH", "DELETE"]
)
@app.route("/<string:_>", methods=["POST", "GET", "PUT", "PATCH", "DELETE"])
@app.route("/<path:_>", methods=["POST", "GET", "PUT", "PATCH", "DELETE"])
def _proxy(_):
    global last_write_timestamp
    if should_throttle(path=request.path):
        current_timestamp = int(round(time.time() * 1000))
        time_since_last_throttle = current_timestamp - last_write_timestamp
        throttle_time = (throttle_interval * 1000 - time_since_last_throttle) / 1000.0
        if throttle_time > 0:
            executor.submit(time.sleep, throttle_time).result()
    if is_write():
        last_write_timestamp = int(round(time.time() * 1000))

    return proxy_request()


def disable_logs():
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.WARNING)
    os.environ['WERKZEUG_RUN_MAIN'] = 'true'


if os.environ.get('DEBUG') is None:
    disable_logs()

if __name__ == "__main__":
    app.run(debug=False, ssl_context="adhoc")
