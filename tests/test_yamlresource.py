"""
Test cases for YAML resources

"""

import allure
from mgx_libs.apis.spec import (
    PluginYAMLResourceRequest, )

import os
import logging as log


@allure.feature("mgx-libs")
class TestYAMLResource():

    def setup_class(self):

        os.environ["MGX_GW_TMP"] = "./tests/data/apispec.json"

    def teardown_class(self):
        pass

    def test_apply_resource(self):

        yaml_req = PluginYAMLResourceRequest()

        ctx = {"cluster": "main", "ns": "ns1", "path": "/"}
        data = open("./tests/data/namespace_resource.yaml").read()  # pylint: disable=R1732,W1514

        log.debug("read yaml %s", data)

        results = yaml_req.apply_resource(ctx, data)

        log.debug("read results %s", results)

        assert True

    def test_apply_resource1(self):

        yaml_req = PluginYAMLResourceRequest()

        ctx = {"cluster": "main", "ns": "ns1", "path": "/"}
        data = open("./tests/data/namespace_resource1.yaml").read()  # pylint: disable=R1732,W1514

        log.debug("read yaml %s", data)

        results = yaml_req.apply_resource(ctx, data)

        log.debug("read results %s", results)

        assert True
