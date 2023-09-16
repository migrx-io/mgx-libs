"""
Test cases for PermLoader

"""

import allure
from mgx_libs.apis.spec import (
    PermissionLoader,
    unwrap_print,
)

import os
import logging as log


@allure.feature("mgx-libs")
class TestAPIS():

    def setup_class(self):

        os.environ["MGX_GW_TMP"] = "./tests/data/apispec.json"

    def teardown_class(self):
        pass

    def test_unwrap_permission(self):

        perms = PermissionLoader()
        res = perms.unwrap_permission({"cluster": ["add", "del"]})

        assert res[0]["method"] == 'POST'
        assert res[0]["path"] == '/cluster/{cluster}'

    def test_unwrap_permission_plugin(self):

        perms = PermissionLoader()
        res = perms.unwrap_permission({"aaa": {"namespace": ["add", "del"]}})

        assert res[0]["method"] == 'PLUGIN'
        assert res[0]["path"] == ['aaa', 'namespace_add']

        assert res[1]["method"] == 'PUT'
        assert res[1]["path"] == "/cluster/{cluster}/plugins/{plugin}"

    def test_unwrap_permission_plugin_with_ctx(self):

        perms = PermissionLoader()

        res = perms.unwrap_permission({
            "cluster": ["add", "del"],
            "aaa": {
                "role": [{
                    "add": [{
                        "matchTerm": {
                            "role": {
                                "matchExpressions": [{
                                    "key": "role",
                                    "operator": "In",
                                    "values": ["superuser"]
                                }]
                            },
                            "object": {
                                "matchExpressions": [{
                                    "key":
                                    "perm_groups",
                                    "operator":
                                    "In",
                                    "values": ["cluster_add_del_list"]
                                }]
                            }
                        }
                    }, {
                        "matchTerm": {
                            "object": {
                                "matchExpressions": [{
                                    "key":
                                    "perm_groups",
                                    "operator":
                                    "NotIn",
                                    "values": ["cluster_add_del_list"]
                                }]
                            }
                        }
                    }]
                }, "del"]
            }
        })

        log.debug(res)

        assert res[2]["method"] == 'PLUGIN'
        assert res[2]["path"] == ['aaa', 'role_add']

    def test_unwrap_permission_all(self):

        perms = PermissionLoader()
        res = perms.unwrap_permission({
            "aaa": {
                "namespace": ["add", "del"]
            },
            "cluster": ["add"]
        })

        assert res[0]["method"] == 'PLUGIN'
        assert res[0]["path"] == ['aaa', 'namespace_add']

    def test_unwrap_print(self):

        res = "".join(unwrap_print({}))
        log.debug("unwrap_print: %s", res)

        assert res == ""

    def test_permission_loader(self):

        perms = PermissionLoader()
        res = perms.desc_permissions()
        assert res != ""

    def test_permission_loader_with_filter(self):

        perms = PermissionLoader()
        res = perms.desc_permissions("cluster2")
        log.debug(res)

        assert res == ""
