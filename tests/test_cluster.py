"""
Test cases for Cluster state

"""
import allure
from mgx_libs.cluster.state import (
    State, )

import os
import logging as log


def revert_data():
    import shutil
    filename = os.environ["MGX_DB_NAME"]
    shutil.copyfile(filename + ".bk", filename)


@allure.feature("mgx-libs")
class TestContext():

    def setup_class(self):
        os.environ["MGX_DB_NAME"] = "./tests/data/test.db"

    def teardown_class(self):
        pass

    def test_cluster_node_stats(self):

        revert_data()

        state = State()

        stats = state.cluster_node_stats(99999999)

        log.debug("stats: %s", stats)
        assert True

    def test_cluster_pool_stats(self):

        revert_data()

        state = State()

        stats = state.cluster_pool_stats(99999999)

        log.debug("stats: %s", stats)
        assert True

    # @unittest.skip
    def test_cluster_node_create(self):

        revert_data()

        state = State()

        state.cluster_delete("main")

        cluster_list = state.cluster_list()
        log.debug("nodes: %s", cluster_list)
        assert len(cluster_list) == 0

        node_id = "1"
        state.cluster_node_create("main", node_id)

        cluster_list = state.cluster_node_list("main")
        log.debug("nodes: %s", cluster_list)
        assert len(cluster_list) == 1

        node_id = "2"
        state.cluster_node_create("main", node_id)

        cluster_list = state.cluster_node_list("main")
        log.debug("nodes: %s", cluster_list)
        assert len(cluster_list) == 2

    def test_cluster_node_delete(self):

        revert_data()

        state = State()

        cluster_list = state.cluster_list()
        log.debug("nodes: %s", cluster_list)
        assert len(cluster_list) == 1

        node_id = "1"
        state.cluster_node_delete("main", node_id)

        cluster_list = state.cluster_node_list("main")
        log.debug("nodes: %s", cluster_list)
        assert len(cluster_list) == 2

        node_id = "2"
        state.cluster_node_delete("main", node_id)

        cluster_list = state.cluster_node_list("main")
        log.debug("nodes: %s", cluster_list)
        assert len(cluster_list) == 1

    def test_cluster_freenode_delete(self):
        revert_data()

        state = State()

        state.cluster_freenode_delete()

        cluster_list = state.cluster_node_list("main")
        log.debug("nodes: %s", cluster_list)
        assert len(cluster_list) == 3

        cluster_list = state.cluster_freenode_list()
        log.debug("nodes: %s", cluster_list)
        assert len(cluster_list) == 0

    def test_cluster_vip_by_uuid(self):

        revert_data()

        state = State()

        res = state.cluster_vip_by_uuid("ad750b9e-b870-4cbc-afa9-9efaa48c608a")

        log.debug("res: %s", res)

        assert res[0] is False
        assert res[1] == "10.1.128.195"
        assert res[2] == "10.1.128.162"

        res = state.cluster_vip_by_uuid("b18462fa-d089-41fc-a4da-4138e14aba0a")

        log.debug("res: %s", res)

        assert res[0] is True
        assert res[1] == "10.1.128.195"
        assert res[2] == "10.1.128.162"

    def test_cluster_freenode_list(self):
        revert_data()

        state = State()

        state.cluster_delete("main")

        cluster_list = state.cluster_freenode_list()
        log.debug("nodes: %s", cluster_list)
        assert len(cluster_list) == 3

    def test_cluster_create(self):

        revert_data()

        state = State()

        state.cluster_delete("main")

        cluster_list = state.cluster_list()
        log.debug("nodes: %s", cluster_list)
        assert len(cluster_list) == 0

        node_ids = ['1', '2']
        state.cluster_create("main", node_ids, "192.168.1.1")

        cluster_list = state.cluster_node_list("main")
        log.debug("nodes: %s", cluster_list)
        assert len(cluster_list) == 2

    def test_cluster_create2(self):

        revert_data()

        state = State()

        state.cluster_delete("main")

        cluster_list = state.cluster_list()
        log.debug("nodes: %s", cluster_list)
        assert len(cluster_list) == 0

        node_ids = ['*']
        state.cluster_create("main", node_ids, "192.168.1.1")

        cluster_list = state.cluster_node_list("main")
        log.debug("nodes: %s", cluster_list)
        assert len(cluster_list) == 3

    def test_cluster_delete(self):

        revert_data()

        state = State()

        state.cluster_delete("main")

        cluster_list = state.cluster_list()
        log.debug("nodes: %s", cluster_list)
        assert len(cluster_list) == 0

    def test_cluster_list(self):

        revert_data()

        state = State()

        cluster_list = state.cluster_list()
        log.debug("nodes: %s", cluster_list)
        assert len(cluster_list) == 1

        cluster_vip = cluster_list[0].get("vip_host")
        assert cluster_vip.get(
            "uuid") == "b18462fa-d089-41fc-a4da-4138e14aba0a"

    def test_cluster_current_node(self):

        revert_data()

        state = State()

        cluster_list = state.cluster_current_node(
            "b18462fa-d089-41fc-a4da-4138e14aba0a")
        log.debug("node: %s", cluster_list)
        assert cluster_list["cluster"] == "main"

    def test_cluster_is_group_exists(self):

        revert_data()

        state = State()

        res = state.cluster_is_group_exists("main")
        assert res is True

        res = state.cluster_is_group_exists("noexistsmain")
        assert res is False

    def test_cluster_service_list(self):

        revert_data()

        state = State()

        cluster_list = state.cluster_service_list("main")
        log.debug("nodes: %s", cluster_list)
        assert len(cluster_list) == 4

    def test_cluster_node_list_by_uuid(self):

        revert_data()

        state = State()

        cluster_list = state.cluster_node_list_by_uuid(
            "b18462fa-d089-41fc-a4da-4138e14aba0a")
        log.debug("nodes: %s", cluster_list)
        assert len(cluster_list) == 3

        cluster_name = cluster_list[0].get("cluster")
        assert cluster_name == "main"

    def test_cluster_node_list(self):

        revert_data()

        state = State()

        cluster_list = state.cluster_node_list("main")
        log.debug("nodes: %s", cluster_list)
        assert len(cluster_list) == 3

        cluster_name = cluster_list[0].get("cluster")
        assert cluster_name == "main"

    def test_cluster_vip_change(self):

        revert_data()

        state = State()
        state.cluster_vip_change("main", "10.1.128.196")

        cluster_list = state.cluster_list()

        log.debug("nodes: %s", cluster_list)
        assert len(cluster_list) == 1

        cluster_vip = cluster_list[0].get("vip_host")
        assert cluster_vip.get("vip") == "10.1.128.196"
