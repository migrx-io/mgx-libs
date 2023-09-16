"""
Test cases for helpers

"""
import allure
import logging as log
import os
# import pytest
import time

from mgx_libs.helpers.passwd import Base64Passwd
from mgx_libs.helpers.workers import ns_list_by_cluster

from mgx_libs.store.connection import (
    CassandraConnection, )
from cassandra import ConsistencyLevel


@allure.feature("mgx-libs")
class TestCase():

    def setup_class(self):

        os.environ["MGX_CASS_CREDS"] = "dba:super"
        os.environ["NODE_NAME"] = "bb486ffe-25ac-46c0-8db8-d09029fbdc21"
        os.environ["MGX_DC_NAME"] = "dc1"
        os.environ["MGX_DB_NAME"] = "./tests/data/test.db.local"

        conn = CassandraConnection(consistency=ConsistencyLevel.ALL)
        conn.init()

    def teardown_class(self):

        gpg = GPG()

        keys_before = gpg.list_sub_keys_fp()

        for k in keys_before:
            gpg.delete_sub_key(k)

    def test_base64passwd(self):

        pass_encoded = Base64Passwd().encode("test")

        assert Base64Passwd().decode(pass_encoded) == "test"

    def test_ns_list_by_cluster(self):

        ns = ns_list_by_cluster()

        assert [] == ns
