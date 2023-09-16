#
# Router for internal actor handlers
#
from .handlers import Meta
import logging as log


class SystemRouter:

    def __init__(self):
        pass

    def state(self):
        return self

    def selector(self):
        return {
            'get_actor_meta': Meta,
        }

    def get_op(self, msg):
        log.debug("get_op: %s", msg)
        return msg["context"]["op"]
