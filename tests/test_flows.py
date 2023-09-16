"""
Test cases for Flows state

"""
import allure
from mgx_libs.configs.flows import (
    Flow, )

import os
import logging as log


def revert_data():
    import shutil
    filename = "{}/mgx-plgn-cmd-exec.json".format(os.environ["MGX_FLOWS_DIR"])
    shutil.copyfile(filename + ".bk", filename)


@allure.feature("mgx-libs")
class TestContext():

    def setup_class(self):
        os.environ["MGX_FLOWS_DIR"] = "./tests/data/flows"

    def teardown_class(self):
        pass

    def test_flow_list(self):

        revert_data()

        flow = Flow()
        flows = flow.list()

        log.debug("flow list: %s", flows)
        assert sorted(flows) == sorted(
            ['mgx-plgn-dr', 'mgx-plgn-cmd-exec', 'mgx-plgn-aaa'])

    def test_flow_desc(self):

        revert_data()

        flow = Flow()
        flows = flow.get("mgx-plgn-cmd-exec")

        log.debug("flow: %s", flows)
        assert flows == {
            'name': 'mgx-plgn-cmd-exec',
            'active': 1,
            'priority': 0
        }

    def test_flow_stop(self):

        revert_data()

        flow = Flow()
        flow.stop("mgx-plgn-cmd-exec")
        flows = flow.get("mgx-plgn-cmd-exec")

        log.debug("flow: %s", flows)
        assert flows == {
            'name': 'mgx-plgn-cmd-exec',
            'active': 0,
            'priority': 0
        }

    def test_flow_start(self):

        revert_data()

        flow = Flow()

        flow.stop("mgx-plgn-cmd-exec")
        flow.start("mgx-plgn-cmd-exec")

        flows = flow.get("mgx-plgn-cmd-exec")

        log.debug("flow: %s", flows)
        assert flows == {
            'name': 'mgx-plgn-cmd-exec',
            'active': 1,
            'priority': 0
        }
