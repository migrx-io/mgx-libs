"""
Test cases for Store

"""
import allure
import logging as log
import os
import random
import string
import pytest
import time

from mgx_libs.store.connection import (
    CassandraConnection, )

from cassandra import ConsistencyLevel
from cassandra.cqlengine.management import sync_table, drop_table

#
# Test model
#

from mgx_libs.store.models import BaseModel, parse_perm_rules
from cassandra.cqlengine import columns

from mgx_libs.helpers.namespace import is_namespace_not_empty, clear_ns_objects


def revert_data():
    import shutil
    filename = "./tests/data/test_file.txt"
    shutil.copyfile(filename + ".bk", filename)


class NamespaceModel(BaseModel):

    __table_name__ = "test_table"

    # __options__ = {'default_time_to_live': 20}

    cluster = columns.Text(required=True, primary_key=True)
    ns = columns.Text(required=True, primary_key=True)
    dirs = columns.Text()
    descr = columns.Text()


@allure.feature("mgx-libs")
class TestStore():

    def test_connect(self):

        os.environ["MGX_CASS_CREDS"] = "dba:super"
        os.environ["MGX_DB_NAME"] = "./tests/data/test.db.local"
        os.environ["NODE_NAME"] = "bb486ffe-25ac-46c0-8db8-d09029fbdc21"

        conn = CassandraConnection(consistency=ConsistencyLevel.ALL)
        conn.init()

        assert conn.is_connected is True


@allure.feature("mgx-libs")
class TestModelCase():

    def setup_class(self):

        os.environ["MGX_CASS_CREDS"] = "dba:super"
        os.environ["NODE_NAME"] = "bb486ffe-25ac-46c0-8db8-d09029fbdc21"
        os.environ["MGX_DC_NAME"] = "dc1"

        keyspaces = ['dc1']
        conns = ['default']

        conn = CassandraConnection(consistency=ConsistencyLevel.ALL)
        conn.init()

        # create schema and table
        # drop_table(NamespaceModel, keyspaces=keyspaces, connections=conns)
        sync_table(NamespaceModel, keyspaces=keyspaces, connections=conns)

    def teardown_class(self):

        drop_table(NamespaceModel)

        revert_data()

    def test_create(self):

        ctx = {
            "context": {
                "cluster": "cl1",
                "ns": "ns1",
                "path": "/root/dir1",
                "op": "add_namespace",
                "prop": "test"
            }
        }

        ctx2 = {
            "context": {
                "cluster": "cl1",
                "ns": "ns2",
                "path": "/root/dir1",
                "op": "add_namespace",
                "prop": "test"
            }
        }

        data = [{
            "cluster": "cl1",
            "ns": "ns1",
            "descr": "description",
            "na_col": "no col data"
        }]

        data2 = [{
            "cluster": "cl1",
            "ns": "ns2",
            "descr": "description",
            "na_col": "no col data"
        }]

        ctx = ctx.get("context")

        Ns = NamespaceModel.ctx(**ctx)
        for d in data:
            try:
                Ns.insert(**d)
            except Exception:
                pass

        ctx = ctx2.get("context")

        Ns = NamespaceModel.ctx(**ctx)
        for d in data2:
            try:
                Ns.insert(**d)
            except Exception:
                pass

    def test_filter(self):

        # self.test_create()

        req = {
            "context": {
                "cluster": "cl1",
                "ns": "ns1",
                "path": "/root/dir1",
                "op": "add_namespace"
            },
            "data": {
                "cluster": "cl1"
            }
        }

        ctx = req.get("context")
        data = req.get("data")

        cnt = NamespaceModel.ctx(**ctx).filter(**data).count()

        assert cnt == 1

    @pytest.mark.skip(reason="???")
    def test_movep(self):

        try:
            self.test_delete()
            self.test_create()
        except Exception:
            pass

        req = {
            "context": {
                "cluster": "cl1",
                "ns": "ns1",
                "path": "/",
                "op": "add_namespace"
            },
            "data": {
                "cluster": "cl1",
                "ns": "ns1"
            }
        }

        ctx = req.get("context")
        data = req.get("data")

        ns = NamespaceModel.ctx(**ctx).filter(**data).get()

        log.debug("ns before update %s", ns.descr)

        assert ns.ctx_pathz == {"/", "/root", "/root/dir1"}

        ns.movep("/root")

        time.sleep(1)

        ctx["path"] = "/root"

        ns = NamespaceModel.ctx(**ctx).filter(**data).get()

        assert ns.ctx_path == "/root"
        assert ns.ctx_pathz == {"/", "/root"}

    @pytest.mark.skip(reason="???")
    def test_update(self):

        try:
            # self.test_delete()
            self.test_create()
        except Exception:
            pass

        req = {
            "context": {
                "cluster": "cl1",
                "ns": "ns1",
                "path": "/root/dir1",
                "op": "add_namespace"
            },
            "data": {
                "cluster": "cl1",
                "ns": "ns1"
            }
        }

        ctx = req.get("context")
        data = req.get("data")

        test_desc = "".join(random.choices(string.ascii_lowercase))

        ns = NamespaceModel.ctx(**ctx).filter(**data).get()

        log.debug("ns before update %s", ns.descr)

        ns.descr = test_desc
        ns.store()

        time.sleep(1)

        ns = NamespaceModel.ctx(**ctx).filter(**data).get()

        assert ns.descr == test_desc

        # check different path
        req = {
            "context": {
                "cluster": "cl1",
                "ns": "ns1",
                "path": "/",
                "op": "add_namespace"
            },
            "data": {
                "cluster": "cl1",
                "ns": "ns1"
            }
        }

        ns = NamespaceModel.ctx(**ctx).filter(**data).get()

        log.debug("ns after update %s", ns.descr)

        assert ns.descr == test_desc

    @pytest.mark.skip(reason="???")
    def test_delete(self):

        req = {
            "context": {
                "cluster": "cl1",
                "ns": "ns1",
                "path": "/root",
                "op": "add_namespace"
            },
            "data": {
                "cluster": "cl1",
                "ns": "ns1"
            }
        }

        ctx = req.get("context")
        data = req.get("data")

        ns = NamespaceModel.ctx(**ctx).filter(**data).get()

        ns.remove()

        cnt = NamespaceModel.ctx(**ctx).filter(**data).count()

        assert cnt == 0

    def test_parse_perm_rules(self):

        ctx = {
            'op': 'role_add',
            'cluster': 'main',
            'ns': 'admins',
            'path': '/',
            'login': 'superuser',
            'ctx_perm_ctx': {
                'role': {
                    'role':
                    'superuser',
                    'descr':
                    'Superuser role for cluster wide access',
                    'perm_groups': [
                        'cluster_add_del_list', 'namespace_add_del_list_show',
                        'role_add_with_cluster_perm'
                    ]
                },
                'user': {
                    'login': 'superuser',
                    'path': '/',
                    'email': 'superuser@migrx.ru',
                    'whitelist_networks': [],
                    'checksum_profile': None,
                    'descr': 'Superuser for cluster wide access',
                    'roles': ['superuser']
                },
                'context':
                '''[{"matchTerm":
                       {"role": {"matchExpressions":
                                    [{"key": "role", "operator": "In",
                                      "values": ["superuser"]}]},
                        "object": {"matchExpressions":
                                    [{"key": "perm_groups",
                                      "operator": "Contains",
                                      "values": ["cluster_add_del_list"]}]}
                        }},
                      {"matchTerm":
                          {"object": {"matchExpressions":
                              [{"key": "perm_groups",
                                "operator": "NotContains",
                                "values": ["cluster_add_del_list"]}]}}
                              }
                      ]'''
            },
            'ctx_perm_ctx_model': 'Roles'
        }

        data = {'role': 'test3', 'perm_groups': ["cluster_add_del_list"]}

        res = parse_perm_rules(ctx, "Roles", data)

        assert res is True

    def test_parse_perm_rules_user(self):

        ctx = {
            'op': 'role_add',
            'cluster': 'main',
            'ns': 'admins',
            'path': '/',
            'login': 'superuser',
            'ctx_perm_ctx': {
                'role': {
                    'role':
                    'admin',
                    'descr':
                    'Superuser role for cluster wide access',
                    'perm_groups': [
                        'cluster_add_del_list', 'namespace_add_del_list_show',
                        'role_add_with_cluster_perm'
                    ]
                },
                'user': {
                    'login': 'superuser',
                    'path': '/',
                    'email': 'superuser@migrx.ru',
                    'whitelist_networks': [],
                    'checksum_profile': None,
                    'descr': 'Superuser for cluster wide access',
                    'roles': ['superuser']
                },
                'context':
                '''[{"matchTerm":
                         {"role": {"matchExpressions":
                                      [{"key": "role",
                                        "operator": "In",
                                        "values": ["superuser"]}]},
                          "object": {"matchExpressions":
                                      [{"key": "perm_groups",
                                        "operator": "Contains",
                                        "values": ["cluster_add_del_list"]}]}
                          }},
                        {"matchTerm":
                            {"object": {"matchExpressions":
                                [{"key": "perm_groups",
                                  "operator": "NotContains",
                                  "values": ["cluster_add_del_list"]}]}}
                                }
                        ]'''
            },
            'ctx_perm_ctx_model': 'Roles'
        }

        data = {'role': 'test3', 'perm_groups': ["cluster_add_del_list"]}

        res = parse_perm_rules(ctx, "Roles", data)

        assert res is False

        data = {'role': 'test3', 'perm_groups': ["cluster_add_del_list2"]}

        res = parse_perm_rules(ctx, "Roles", data)

        assert res is True

        data = {}

        res = parse_perm_rules(ctx, "Roles", data)

        assert res is True

    def test_namespace_delete_check(self):

        req = {
            "context": {
                "cluster": "cl1",
                "ns": "ns2",
                "path": "/"
            },
            "data": {
                "cluster": "cl1",
                "ns": "ns2"
            }
        }

        ctx = req.get("context")

        exists, err = is_namespace_not_empty(ctx)

        log.debug("exists: %s / err: %s", exists, err)
        assert exists is False

        clear_ns_objects(ctx)

        assert True
