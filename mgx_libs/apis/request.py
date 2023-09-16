from mgx_libs.configs.env import Env
import requests
import json
import logging as log
from mgx_libs.cluster.state import State
import gevent
import urllib3
import copy
from tzlocal import get_localzone_name

# disable self signed warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def parse_json(data):
    try:
        return json.loads(data)
    except Exception as e:
        log.debug("parse_json: data: %s, err: %s", data, e)
        return data


def gevent_call(par):
    """
    Wrapper for gevent executor
    """
    ctx, path, data, method, node = par
    _, text = Request(ctx).call(path, data, method)
    return (node, text)


class ClusterRequest():

    def __init__(self, ctx, cluster):
        self.ctx = ctx
        self.cluster = cluster

    def call(self, path, data, method):

        state = State()

        res = {}
        pool = []
        for n in state.cluster_node_list(self.cluster):

            self.ctx.update_host(n["ip"])

            # copy ctx for each request
            ctx = copy.copy(self.ctx)

            pool.append(
                gevent.spawn(gevent_call,
                             (ctx, path, data, method, n["uuid"])))

        gevent.joinall(pool)

        for r in pool:
            node, value = r.value
            res[node] = value

        return res


class Request():

    def __init__(self, ctx):
        self.ctx = ctx

    def call(self, path, data, method="PLUGIN", file=None):

        log.debug("method: %s/ path: %s / data: %s", method, path, data)

        try:

            url_data = data.copy()
            url_data["cluster"] = (
                lambda x: x is None and self.ctx.cluster or x)(
                    data.get("cluster"))
            url_data["ns"] = (lambda x: x is None and self.ctx.ns or x)(
                data.get("ns"))

            if method == "POST":

                if self.ctx.async_endpoint:
                    path = "{}_async".format(path)

                r = requests.post(self.ctx.api_url + path.format(**url_data),
                                  headers=self.ctx.headers,
                                  data=json.dumps(url_data),
                                  timeout=self.ctx.timeout,
                                  verify=self.ctx.api_tls_verify)

            elif method == "GET":
                r = requests.get(self.ctx.api_url + path.format(**url_data),
                                 headers=self.ctx.headers,
                                 timeout=self.ctx.timeout,
                                 verify=self.ctx.api_tls_verify)

            elif method == "DELETE":
                r = requests.delete(self.ctx.api_url + path.format(**url_data),
                                    headers=self.ctx.headers,
                                    timeout=self.ctx.timeout,
                                    verify=self.ctx.api_tls_verify)

            elif method == "PUT":
                r = requests.put(self.ctx.api_url + path.format(**url_data),
                                 headers=self.ctx.headers,
                                 data=json.dumps(url_data),
                                 timeout=self.ctx.timeout,
                                 verify=self.ctx.api_tls_verify)

            elif method == "PUT_FILE":

                # rewrire header
                headers = self.ctx.headers.copy()
                del headers["Content-type"]

                log.debug("put headers: %s", self.ctx.headers)
                log.debug("put file: %s", file)

                r = requests.put(self.ctx.api_url + path.format(**url_data),
                                 headers=headers,
                                 files={'file': file},
                                 timeout=self.ctx.timeout,
                                 verify=self.ctx.api_tls_verify)

            elif method == "PLUGIN":

                plugin_id, op = path[0], path[1]

                req_ctx = data.get("context", {"op": op})

                # if requets data contains ctx and data
                if data.get("context") is not None and data.get(
                        "data") is not None:
                    req_data = data.get("data")
                else:
                    req_data = data

                log.debug("data: %s / req_ctx: %s", req_data, req_ctx)

                # add more meta to context
                req_ctx["cluster"] = self.ctx.cluster
                req_ctx["ns"] = self.ctx.ns
                req_ctx["path"] = self.ctx.path
                req_ctx["login"] = self.ctx.login

                req = {"context": req_ctx, "data": req_data}

                log.debug("call plugin: %s / req: %s", plugin_id, req_data)

                r = requests.put("{}/cluster/{}/plugins/{}".format(
                    self.ctx.api_url, self.ctx.cluster, plugin_id),
                                 headers=self.ctx.headers,
                                 data=json.dumps(req),
                                 timeout=self.ctx.timeout,
                                 verify=self.ctx.api_tls_verify)
            else:
                raise Exception("Wrong method data")

            return r.status_code, parse_json(r.text)

        except Exception as e:
            return 503, str(e)


class Context:

    def __init__(self, typ="MGX", **kwargs):

        self.env = Env().envs

        self.host = kwargs.get("host", self.env[f"{typ}_HOST"])
        self.port = kwargs.get("port", self.env[f"{typ}_PORT"])
        self.tls = kwargs.get("tls", self.env[f"{typ}_IS_TLS"])
        self.tls_verify = kwargs.get("tls_verify",
                                     self.env[f"{typ}_TLS_VERIFY"])
        self.timeout = kwargs.get("timeout", self.env[f"{typ}_HTTP_TIMEOUT"])
        self.api_key = kwargs.get("api_key", self.env[f"{typ}_X_API_KEY"])

        self.api_version = kwargs.get("api_version", "/api/v1")

        if self.tls_verify == "n":
            self.api_tls_verify = False
        else:
            self.api_tls_verify = True

        self.api_proto = (lambda x: 'http'
                          if x == 'n' else str('https'))(self.tls)
        self.api_url = f"{self.api_proto}://{self.host}:{self.port}{self.api_version}"

        self.token = kwargs.get("token", "")

        # update tzinfo
        self.tzname = kwargs.get("tzname", get_localzone_name())

        self.update_headers()

        self.cluster = kwargs.get("cluster", "")
        self.ns = kwargs.get("ns", "")
        self.login = kwargs.get("login", None)
        self.path = kwargs.get("path", None)

        self.loglevel = kwargs.get("loglevel", self.env["LOGLEVEL"])

        self.async_endpoint = kwargs.get("async_endpoint")

        # async pool by default
        if typ == "MGX":
            if self.async_endpoint is None:
                self.async_endpoint = True
        else:
            self.async_endpoint = False

    def update_headers(self):
        self.headers = {
            "Content-type":
            "application/json",
            "X-API-KEY":
            self.api_key,
            "TZ":
            self.tzname,
            "Authorization":
            "{} ".format(self.env["MGX_GW_JWT_HEADER"]) + self.token
        }

    def update_host(self, host):
        self.host = host
        self.api_url = f"{self.api_proto}://{self.host}:{self.port}{self.api_version}"
