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

throttle_paths_regex = [
    "^/apis/apps/v1/namespaces/[^/]+/statefulsets(/[^/]+)?$",
    "^/apis/apps/v1/namespaces/[^/]+/deployments(/[^/]+)?$",
]


def _disable_logs():
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.WARNING)
    os.environ['WERKZEUG_RUN_MAIN'] = 'true'


def _is_write():
    return request.method == "POST" or request.method == "PUT" or request.method == "PATCH"


class KubeApiProxy:
    def __init__(self, kube_api, throttle_interval, ca_cert, skip_tls_verification, client_cert, client_key, debug):
        self._kube_api = kube_api.removesuffix('/')
        self._throttle_interval = throttle_interval

        self._app = Flask(__name__)
        self._executor = ThreadPoolExecutor(1)
        self._session = Session()
        self._last_write_timestamp = None
        self._debug = debug

        if ca_cert is not None:
            self._session.verify = ca_cert

        if skip_tls_verification:
            self._session.verify = False
            # Disable SSL Warnings
            warnings.simplefilter('ignore', InsecureRequestWarning)

        if client_cert is not None:
            self._session.cert = (client_cert, client_key)

        context = self

        @self._app.route(
            "/", defaults={"path": ""}, methods=["POST", "GET", "PUT", "PATCH", "DELETE"]
        )
        @self._app.route("/<string:_>", methods=["POST", "GET", "PUT", "PATCH", "DELETE"])
        @self._app.route("/<path:_>", methods=["POST", "GET", "PUT", "PATCH", "DELETE"])
        def _proxy(_):
            if context._should_throttle(path=request.path):
                current_timestamp = int(round(time.time() * 1000))
                time_since_last_throttle = current_timestamp - context._last_write_timestamp
                throttle_time = (throttle_interval * 1000 - time_since_last_throttle) / 1000.0
                if throttle_time > 0:
                    context._executor.submit(time.sleep, throttle_time).result()
            if _is_write():
                context._last_write_timestamp = int(round(time.time() * 1000))

            return context._proxy_request()

    def _should_throttle(self, path):
        if self._last_write_timestamp is None:
            return False

        resource_is_listed = any(re.search(element, path) for element in throttle_paths_regex)
        is_dry_run = request.args.get("dryRun") == "All"
        return _is_write() and resource_is_listed and not is_dry_run

    def _proxy_request(self):
        resp = self._session.request(
            params=request.args,
            method=request.method,
            url=self._kube_api + request.path,
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

    def run(self):
        if not self._debug:
            _disable_logs()
        self._app.run(debug=False, ssl_context="adhoc", port=5001)
