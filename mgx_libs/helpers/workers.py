from mgx_libs.configs.env import envs
from mgx_libs.apis.request import Request, Context
import json
import logging as log
from transitions import Machine


#
# Generic plugin call
#
def call_plugin(pl, op, ctx, req, host="localhost"):

    status, data = Request(Context("MGX", host=host)).call(
        "/{}".format(pl), {
            "context": {
                "op": op,
                "cluster": ctx.get("cluster", ctx.get("ctx_cluster")),
                "ns": ctx.get("ns", ctx.get("ctx_ns")),
                "path": ctx.get("path", ctx.get("ctx_path")),
                "login": ctx.get("login", ctx.get("ctx_login"))
            },
            "data": req
        }, "POST")

    if status != 200:
        raise Exception(data)

    if status == 200:
        # check error from response
        if isinstance(data, dict):
            if data.get("error"):
                raise Exception(data.get("error"))

    return data


def notify(ctx, route, msg, to=None):

    data = {"data": json.dumps({"route": route, "to": to, "data": msg})}

    status, data = Request(Context("MGX")).call(
        "/notif", {
            "context": {
                "op": "_nowait_message_add",
                "cluster": ctx.get("cluster", ctx.get("ctx_cluster")),
                "ns": ctx.get("ns", ctx.get("ctx_ns")),
                "path": ctx.get("path", ctx.get("ctx_path")),
                "login": ctx.get("login", ctx.get("ctx_login"))
            },
            "data": data
        }, "POST")
    return status, data


def ns_list_by_cluster():

    from mgx_libs.store.aaa import Namespaces
    from mgx_libs.cluster.state import State

    # get node cluster
    state = State()
    node = state.cluster_current_node(envs["NODE_NAME"])

    # if no clusters return empty list
    if node is None:
        return []

    # Implement later. define chunks(namespaces) between nodes to improve performance

    cluster = node.get("cluster")

    # get namespace list
    ns = Namespaces.objects.all()

    return [{
        "cluster": cluster,
        "ns": x["ns"],
        "path": "/"
    } for x in ns if x["cluster"] == cluster]


def wrap_cluster_sc_node(fun, msg):

    from mgx_libs.cluster.state import State

    # get all on all nodes / node
    state = State()

    nodes = state.cluster_node_list_by_uuid(envs["NODE_NAME"])
    log.debug("nodes: %s", nodes)

    # if sc_node passed of all nodes
    node = msg.get("data", {}).get("sc_node", envs["NODE_NAME"])
    if node is None:
        node = envs["NODE_NAME"]

    for n in nodes:
        if node in ("*", n["uuid"]):

            msg = msg.copy()
            msg["data"]["sc_node"] = n["uuid"]

            fun(msg)


#
# Runner models
#


def beautify_q(data):

    if data.get("state") is not None:
        q_fields = {
            "op": data.get("op"),
            "op_request": data.get("op_request"),
            "state": data.get("state"),
            "run_error": data.get("run_error"),
            "run_retry": data.get("run_retry"),
        }
        del data["op"]
        del data["op_request"]
        del data["state"]
        del data["run_error"]
        del data["run_retry"]

        data["q_task"] = q_fields

    return data


class OpRunner:

    def __init__(self, model):
        self.model = model

    def run(self):

        if self.model.state == "FINISH":
            return

        if self.model.states is not None:
            states = json.loads(self.model.states)[self.model.op]
        else:
            raise Exception("States is not defined")

        # define next step
        idx = states.index(self.model.state)
        if self.model.run_error is not None:

            if self.model.run_retry >= 0:
                self.model.run_error = None
                idx = states.index(self.model.state) - 1
            else:
                return

        if self.model.state != "PENDING":
            states = states[idx:]

        log.debug("states: %s", states)

        machine = Machine(model=self.model, states=states, initial=states[0])
        machine.add_ordered_transitions(loop=False, conditions='condition')

        # loop over states
        while self.model.may_next_state():
            try:
                self.model.next_state()

            except Exception as e:
                log.error("run state: %s / err:  %s", self.model.state, e)

                # save error
                self.model.run_error = str(e)
                self.model.run_retry -= 1
                self.model.on_enter_ERROR()

                break
