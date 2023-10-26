"""
Test cases for APIs

"""

import allure
from tests import mock_server
from mgx_libs.apis.request import (Context, Request, ClusterRequest)
from mgx_libs.apis.spec import (
    APISpec,
    GWSpec,
    PluginSpec,
    evalExpression,
    get_event_operation,
)

import os
import time
import logging as log


@allure.feature("mgx-libs")
class TestContext():

    def setup_class(self):
        os.environ["MGX_IS_TLS"] = "y"
        os.environ["MGX_GW_IS_TLS"] = "n"

    def teardown_class(self):
        pass

    def test_tls(self):
        ctx = Context(port=8083)

        log.debug("test_tls: %s", ctx.tls)

        assert ctx.tls == "y"
        assert ctx.api_proto == "https"

    def test_gw_tls(self):
        ctx = Context("MGX_GW", port=8083)

        log.debug("test_tls: %s", ctx.tls)

        assert ctx.tls == "n"
        assert ctx.api_proto == "http"


@allure.feature("mgx-libs")
class TestAPIS():

    def setup_class(self):

        os.environ["MGX_IS_TLS"] = "n"
        os.environ["MGX_GW_IS_TLS"] = "n"

        os.environ["MGX_GW_TMP"] = "./data/apispec.json"

        self.server = mock_server.run_test_server(8083)
        self.server.daemon = True
        self.server.start()
        time.sleep(2)

    def teardown_class(self):
        self.server.do_run = False

    def test_post(self):
        ctx = Context(port=8083)
        status, text = Request(ctx).call("/post_test", {}, "POST")
        log.debug(text)
        assert status == 200
        assert text == "ok"

    def test_put(self):
        ctx = Context(port=8083)
        status, text = Request(ctx).call("/put_test", {}, "PUT")
        log.debug(text)
        assert status == 200
        assert text == "ok"

    def test_put_server_error(self):
        ctx = Context(port=8083)
        status, text = Request(ctx).call("/put_test", {"error": 1}, "PUT")
        log.debug(text)
        assert status == 503

    def test_post_bad_port(self):
        ctx = Context(port=8084)
        status, text = Request(ctx).call("/post_test", {}, "POST")
        log.debug(text)
        assert status == 503

    def test_get(self):
        ctx = Context(port=8083)
        status, text = Request(ctx).call("/get_test", {}, "GET")
        log.debug(text)
        assert status == 200
        assert text == {"ok": "ok"}

    def test_delete(self):
        ctx = Context(port=8083)
        status, text = Request(ctx).call("/get_test", {}, "DELETE")
        log.debug(text)
        assert status == 500
        assert text == {"error": "error"}

    def test_plugin(self):
        ctx = Context(port=8083)
        status, text = Request(ctx).call(("plugin_id", "op"), {})
        log.debug(text)
        assert status == 200
        assert text == "ok"

    def test_bad_method(self):
        ctx = Context(port=8083)
        status, text = Request(ctx).call("/get2_test", {}, "GET2")
        log.debug(text)
        assert status == 503

    def test_cluster_proxy_request(self):

        os.environ["MGX_DB_NAME"] = "./tests/data/test.db"

        ctx = Context(port=8083)
        res = ClusterRequest(ctx, "main2").call("/post_test", {}, "POST")

        log.debug("res: %s", res)
        assert res == {'bb486ffe-25ac-46c0-8db8-d09029fbdc20': 'ok'}

    def test_gw_spec(self):

        res = GWSpec("./tests/data/apispec_1.json").get()
        log.debug("res: %s", res)
        assert res.get("cmd_map") is not None

    def test_plugin_spec(self):

        res = PluginSpec("./tests/data/actor_aaa.yaml").get()
        log.debug("res: %s", res)
        assert res.get("cmd_map") is not None

    def test_get_spec(self):

        res = APISpec("./tests/data/apispec_1.json",
                      "./tests/data/actor_aaa.yaml").get()
        log.debug("res: %s", res)
        assert res.get("cmd_map").get("cluster") is not None

    def test_event_operation(self):

        os.environ["MGX_GW_TMP"] = "./tests/data/apispec.json"

        method = "GET"
        path = "/api/v1/cluster"
        data = b''

        op = get_event_operation(method, path, data)

        assert op == "Get clusters list"

        method = "POST"
        path = "/api/v1/cluster/main/plugins/aaa"
        data = b''

        op = get_event_operation(method, path, data)

        assert op == "Start plugin"

        method = "PUT"
        path = "/api/v1/cluster/main/plugins/aaa"
        data = {
            "context": {
                "op": "namespace_add"
            },
            "data": {
                "response": "data"
            }
        }

        op = get_event_operation(method, path, data)

        assert op == "Add new namespace to Cluster"

        method = "PUT"
        path = "/api/v1/cluster/main/plugins/aaa"
        data = {
            "context": {
                "op": "namespace_add2"
            },
            "data": {
                "response": "data"
            }
        }

        op = get_event_operation(method, path, data)

        assert op is None

    def test_evalExpression(self):

        data = {
            "name": "test1",
            "arr": ["1", "2", "3", "4"],
            "data": {
                "cluster": ["add"]
            },
            "data2": {
                "aaa": {
                    "permission": ["add", "del"]
                }
            }
        }

        # value
        expr = {"key": "name", "operator": "StartsWith", "values": ["1", "te"]}
        assert evalExpression(expr, data)

        expr = {
            "key": "name",
            "operator": "NotStartsWith",
            "values": ["xd", "asd"]
        }
        assert evalExpression(expr, data)

        # array
        expr = {"key": "arr", "operator": "StartsWith", "values": ["1", "tes"]}
        assert evalExpression(expr, data)

        expr = {
            "key": "arr",
            "operator": "NotStartsWith",
            "values": ["xd", "23"]
        }
        assert evalExpression(expr, data)

        # ----
        expr = {"key": "name", "operator": "In", "values": ["test1", "test2"]}
        assert evalExpression(expr, data)

        expr = {"key": "name", "operator": "NotIn", "values": ["test3"]}
        assert evalExpression(expr, data)

        expr = {"key": "data", "operator": "InDict", "values": ["cluster"]}
        assert evalExpression(expr, data)

        expr = {
            "key": "data",
            "operator": "NotInDict",
            "values": ["notcluster"]
        }
        assert evalExpression(expr, data)

        expr = {
            "key": "data2",
            "operator": "InDict",
            "values": ["aaa.permission"]
        }
        assert evalExpression(expr, data)

        expr = {"key": "data2", "operator": "InDict", "values": ["aaa"]}
        assert evalExpression(expr, data)

        expr = {
            "key": "data2",
            "operator": "NotInDict",
            "values": ["aaa.permission2"]
        }
        assert evalExpression(expr, data)

        expr = {"key": "arr", "operator": "Contains", "values": ["1", "4"]}
        assert evalExpression(expr, data)

        expr = {"key": "arr", "operator": "NotContains", "values": ["6", "7"]}
        assert evalExpression(expr, data)

        # not found key in model
        expr = {"key": "arr2", "operator": "NotContains", "values": ["6", "7"]}
        assert evalExpression(expr, data)

        assert True
