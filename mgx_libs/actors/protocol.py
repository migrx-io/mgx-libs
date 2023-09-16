# Protol

import traceback
from .api import API
from .system.router import SystemRouter
import logging as log
import json


def handle(router, req, api, is_stream=False):
    """handle request
    """
    # add ctx
    ctx = {}

    try:

        log.debug("handle req: %s", req)

        # parse string
        req = api.parse_request(req)

        if isinstance(req, dict):
            ctx = req.get("context", {})

        if ctx.get("system_call") is not None:
            router = SystemRouter()

        # validate request
        if not is_stream:
            api.validate_request(req)

        params, handle_map = router.state(), router.selector()

        # check default get_op method
        if not hasattr(router, "get_op"):
            op = ctx.get("op")
        else:
            op = router.get_op(req)

        # find func
        handler_cls = handle_map.get(op, None)
        if not handler_cls:
            raise Exception(f"invalid operation: {op}")

        # init class
        handler = handler_cls(params)

        # call
        res = getattr(handler, op)(req)

        if res is None:
            return None

        if not is_stream:
            return api.parse_response({"context": ctx, "data": res})

        return api.parse_response(res)

    except Exception as e:
        log.error(traceback.format_exc())
        return api.parse_response({"context": ctx, "error": str(e)})


def stdio(router, **kwargs):

    api = API(**kwargs)

    while 1:
        msg_id, msg = api.unwrap_raw_message(api.read())

        log.debug("get message: %s", msg)

        res = handle(router, msg, api)

        api.send(api.wrap_raw_message(msg_id, res))

        log.debug("message send: %s", res)


def stdin(queue, **kwargs):

    api = API(**kwargs)
    while 1:
        msg = api.read()

        log.debug("get raw message: %s", msg)
        msg_id, _ = api.unwrap_raw_message(msg)

        log.debug("get message: %s", msg)
        queue.put(msg)

        if api.nowait and msg.find("_nowait_") >= 0:
            api.send(api.wrap_raw_message(msg_id, "ok"))


def stdout(router, queue, **kwargs):

    api = API(**kwargs)

    while 1:

        raw_msg = queue.get()

        msg_id, msg = api.unwrap_raw_message(raw_msg)

        log.debug("get message: %s", msg)

        res = handle(router, msg, api)

        api.send(api.wrap_raw_message(msg_id, res))

        if kwargs.get("ack_queue"):
            router.ack_queue.pop(raw_msg, None)

        log.debug("message send: %s", res)


def stream(router, start_msg, queue, **kwargs):

    api = API(**kwargs)

    if kwargs.get("ack_queue"):
        setattr(router, 'ack_queue', {})

    while 1:

        res = handle(router, json.dumps(start_msg), api, True)

        if queue is not None:

            if kwargs.get("ack_queue"):
                if router.ack_queue.get(res) is None:
                    router.ack_queue[res] = True
                    queue.put(res)
            else:
                queue.put(res)

        else:
            api.send(res)

        log.debug("message send: %s", res)
