"""
Test cases for Store

"""
import allure
import logging as log
import os
import time

from mgx_libs.store.connection import (
    CassandraConnection, )

from cassandra import ConsistencyLevel
from cassandra.cqlengine.management import sync_table, drop_table

#
# Test model
#
from mgx_libs.store.models import BaseModel
from cassandra.cqlengine import columns
from mgx_libs.helpers.workers import OpRunner

TEST_OP_SLEEP = 0.1


class QueueModel(BaseModel):

    __table_name__ = "test_queue"

    # queue fileds
    states = columns.Text(
        default='{"create": ["PENDING", "A", "B", "C", "FINISH"],'
        '"update": ["PENDING", "A", "D", "FINISH"]}')

    op = columns.Text(default="create")
    state = columns.Text(default="PENDING")
    run_error = columns.Text()
    run_retry = columns.Integer()
    # ---

    task = columns.Text(required=True, primary_key=True)
    data = columns.Integer()

    def push_to_runner(self, op):

        self.op = op
        self.state = "PENDING"
        self.run_error = None
        self.run_retry = 2

        self.data = 0

        self.store()

    def on_enter_ERROR(self):
        log.debug("complete states ERROR!")
        # save current state
        log.debug("save current: %s", self.run_error)
        self.store()
        time.sleep(TEST_OP_SLEEP)

    def on_enter_FINISH(self):
        log.debug("complete states FINISH!")

        # save current state
        log.debug("save current: %s", self.run_error)
        self.store()
        time.sleep(TEST_OP_SLEEP)

    # implement condition for steps

    @property
    def condition(self):
        # before switch to next state
        log.debug("check confition state: %s / data: %s", self.state,
                  self.data)

        if self.state == "C":
            if self.data < 10:
                return False
            return True

        return True

    # implement all steps for model

    def on_enter_A(self):

        log.debug("model op: %s", self.op)
        log.debug("model state: %s", self.state)
        # do all works
        self.data += 1
        log.debug("model data: %s", self.data)
        time.sleep(TEST_OP_SLEEP)

        # save current state
        log.debug("save current: %s", self.state)

        self.store()

    def on_enter_B(self):

        log.debug("model op: %s", self.op)
        log.debug("model state: %s", self.state)
        # do all works
        self.data += 1
        log.debug("model data: %s", self.data)
        time.sleep(TEST_OP_SLEEP)

        if self.data == 1:
            raise Exception("Error")

        # save current state
        log.debug("save current: %s", self.state)

        self.store()

    def on_enter_C(self):

        log.debug("model op: %s", self.op)
        log.debug("model state: %s", self.state)
        # do all works
        self.data += 1
        log.debug("model data: %s", self.data)
        time.sleep(TEST_OP_SLEEP)
        # raise Exception("ER!!!")
        # save current state
        log.debug("save current: %s", self.state)

        self.store()

    def on_enter_D(self):

        log.debug("model op: %s", self.op)
        log.debug("model state: %s", self.state)
        # do all works
        self.data += 1
        log.debug("model data: %s", self.data)
        time.sleep(TEST_OP_SLEEP)
        # raise Exception("ER!!!")
        # save current state
        log.debug("save current: %s", self.state)

        self.store()


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
        drop_table(QueueModel)
        sync_table(QueueModel, keyspaces=keyspaces, connections=conns)

    def teardown_class(self):
        pass
        # drop_table(QueueModel)

    def test_model_runner(self):

        ctx = {"cluster": "cl1", "ns": "ns1", "path": "/"}

        task = QueueModel.ctx(**ctx)
        try:
            task.insert(**{"task": "test", "data": 0})
        except Exception:
            pass

        task = QueueModel.ctx(**ctx).filter(**{"task": "test"}).get()

        assert task.task == "test"
        assert task.op == "create"

    def test_A_B_C(self):

        ctx = {"cluster": "cl1", "ns": "ns1", "path": "/"}

        task = QueueModel.ctx(**ctx).filter(**{"task": "test"}).get()

        # run task
        OpRunner(task).run()

        task = QueueModel.ctx(**ctx).filter(**{"task": "test"}).get()

        assert task.state == "C"
        assert task.data == 3

        # update data and try again
        task.data = 11
        task.store()

        # run task
        OpRunner(task).run()

        assert task.state == "FINISH"

        # run new op

        task.push_to_runner("update")
        task = QueueModel.ctx(**ctx).filter(**{"task": "test"}).get()

        # run task
        OpRunner(task).run()
        assert task.state == "FINISH"

        # run with err
        task = QueueModel.ctx(**ctx).filter(**{"task": "test"}).get()
        task.push_to_runner("create")
        task = QueueModel.ctx(**ctx).filter(**{"task": "test"}).get()

        log.debug("task before error: state %s", task.state)

        task.data = -1
        # run task
        OpRunner(task).run()

        assert task.state == "B"
        assert task.run_error == "Error"

        # run task and retry

        task = QueueModel.ctx(**ctx).filter(**{"task": "test"}).get()
        task.data = 11

        OpRunner(task).run()

        assert task.state == "FINISH"
