from flask import request
import time
import requests
from flask import Flask, Response
import re
from optparse import OptionParser

app = Flask(__name__)
parser = OptionParser()
parser.add_option(
    "--sleep-interval",
    dest="interval",
    type="int",
    default=5,
    help="Enter a time-interval",
)
parser.add_option(
    "--kube-api",
    dest="kube_api",
    type="str",
    default="",
    help="Enter an url",
)
(options, args) = parser.parse_args()
kube_api_URL = options.kube_api
time_interval = options.interval
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
                time.sleep(dif)
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
    app.run(debug=True, ssl_context="adhoc")
