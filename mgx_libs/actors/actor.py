# Actor
#  OS process with stdio protol

import logging
import sys
from enum import Enum
from .protocol import stdio, stdin, stdout, stream
from mgx_libs.configs.env import Env


class ActorType(Enum):
    InOut = 1
    In = 2
    Out = 3
    Stream = 4


class Config:
    """
    Example Config
    """

    def __init__(self, data):
        self.data = data

    def state(self):
        return self.data

    def selector(self):
        return {'op': Config}

    def get_op(self, msg):
        return msg


class Actor:

    def __init__(self, **kwargs):

        envs = Env().envs

        if envs["ASYNC_DISABLE"] == "y":
            asyncf = False
        else:
            asyncf = kwargs.get("asyncf", False)

        self.actor_type = kwargs["actor_type"]
        self.queue = kwargs.get("queue")
        self.start_msg = kwargs.get("start_msg")

        self.api_kwargs = {
            "silent":
            kwargs.get("silent", False),
            "ack_queue":
            kwargs.get("ack_queue", False),
            "nowait":
            kwargs.get("nowait", False),
            "asyncf":
            asyncf,
            "none_kill":
            kwargs.get("none_kill", True),
            "schema":
            kwargs.get(
                "schema",
                envs["MGX_PLUGIN_SPEC"].format(sys.argv[0].split("/")[-1]))
        }

        logging.basicConfig(
            stream=sys.stderr,
            format='[%(asctime)s] [%(threadName)s] %(levelname)s - %(message)s',
        )
        logging.getLogger().setLevel(envs["LOGLEVEL"])

    def run(self, state):

        if self.actor_type == ActorType.InOut:
            stdio(state, **self.api_kwargs)

        elif self.actor_type == ActorType.In:
            stdin(self.queue, **self.api_kwargs)

        elif self.actor_type == ActorType.Out:
            stdout(state, self.queue, **self.api_kwargs)

        elif self.actor_type == ActorType.Stream:
            stream(state, self.start_msg, self.queue, **self.api_kwargs)
        else:
            raise Exception(f"Wrong ActorType: {self.actor_type}")
