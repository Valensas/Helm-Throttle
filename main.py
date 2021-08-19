from concurrent.futures import ThreadPoolExecutor
from flask import request
import time
import requests
from flask import Flask, Response
import re
import os


app = Flask(__name__)


kube_api_URL = os.environ.get("KUBEAPI")
time_interval = os.environ.get("TIME_INTERVAL")
if kube_api_URL is None:
    raise Exception("URL Not Given!")
if time_interval is None:
    time_interval = 10
else:
    time_interval = int(time_interval)
last_write_request_throttled_timestamp = None

regex_list = [
    "^apis\/apps\/v1\/namespaces\/[^\/]+\/statefulsets(\/[^\/]+)?$",
    "^apis\/apps\/v1\/namespaces\/[^\/]+\/deployments(\/[^\/]+)?$",
]


def check_for_throttle(path):
    method_type = request.method
    is_method_type_matched = (
        method_type == "POST" or method_type == "PUT" or method_type == "PATCH"
    )
    is_regex_matched = any(re.search(element, path) for element in regex_list)
    is_dry_run = request.args.get("dryRun") == "All"
    return is_method_type_matched and is_regex_matched and not is_dry_run


executor = ThreadPoolExecutor(1)


@app.route(
    "/", defaults={"path": ""}, methods=["POST", "GET", "PUT", "PATCH", "DELETE"]
)
@app.route("/<string:path>", methods=["POST", "GET", "PUT", "PATCH", "DELETE"])
@app.route("/<path:path>", methods=["POST", "GET", "PUT", "PATCH", "DELETE"])
def _proxy(path):
    global last_write_request_throttled_timestamp
    if check_for_throttle(path=path):
        if last_write_request_throttled_timestamp is not None:
            milli_sec = int(round(time.time() * 1000))
            timeDif = milli_sec - last_write_request_throttled_timestamp
            dif = (time_interval * 1000 - timeDif) / 1000.0
            if dif > 0:
                executor.submit(time.sleep, (dif)).result()
        last_write_request_throttled_timestamp = int(
            round(time.time() * 1000))
    resp = requests.request(
        params=request.args,
        method=request.method,
        url=kube_api_URL + "/" + path,
        headers={key: value for (key, value)
                 in request.headers if key != "Host"},
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
    response = Response(resp.content, resp.status_code, headers)
    return response


if __name__ == "__main__":
    app.run(debug=False, ssl_context="adhoc")
