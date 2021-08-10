from sys import stdout
from typing import SupportsRound
from flask import Flask, Response
from flask import request
import time
from flask.scaffold import F
import requests
from requests.api import get, head
import re
from optparse import OptionParser
app = Flask(__name__)
parser = OptionParser()
parser.add_option(
    "--sleep-interval",
    dest="interval",
    type="int",
    default=5,
    help="write report to FILE",
    metavar="FILE",
)
parser.add_option(
    "--kube-api",
    dest="kube_api",
    type="str",
    default="https://rancher.valensas.com/k8s/clusters/c-dvgp5",
    help="don't print status messages to stdout",
)
(options, args) = parser.parse_args()
kubeApiURL = options.kube_api
second = {"prevProcessMilisec": -1}
@app.route(
    "/", defaults={"path": ""}, methods=["POST", "GET", "PUT", "PATCH", "DELETE"]
)
@app.route("/<string:path>", methods=["POST", "GET", "PUT", "PATCH", "DELETE"])
@app.route("/<path:path>", methods=["POST", "GET", "PUT", "PATCH", "DELETE"])
def _proxy(path):
    statefulRegex = "^apis\/apps\/v1\/namespaces\/[^\/]+\/statefulsets(\/[^\/]+)?$"
    deploymentRegex = "^apis\/apps\/v1\/namespaces\/[^\/]+\/deployments(\/[^\/]+)?$"
    methodType = request.method
    isDryRun = request.args.get("dryRun") == "All"
    if methodType == "POST" or methodType == "PUT" or methodType == "PATCH":
        if (
            re.search(statefulRegex, path) is not None
            or re.search(deploymentRegex, path)
        ) and not isDryRun:
            if second["prevProcessMilisec"] != -1:
                milli_sec = int(round(time.time() * 1000))
                timeDif = milli_sec - second["prevProcessMilisec"]
                dif = (options.interval * 1000 - timeDif) / 1000.0
                print("Time dif: ", timeDif)
                print("Milli sec: ", milli_sec % 100000)
                print("Dif: ", dif)
                print("Prev milisec: ", second["prevProcessMilisec"] % 100000)
                if dif > 0:
                    print("Sleeping!")
                    time.sleep(dif)
                    print("Sleeping over!")
                    print(
                        "================================================================================================="
                    )
            second["prevProcessMilisec"] = int(round(time.time() * 1000))
    resp = requests.request(
        params=request.args,
        method=request.method,
        url=kubeApiURL + "/" + path,
        headers={key: value for (key, value) in request.headers if key != "Host"},
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