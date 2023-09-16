'''
# Actors

Usage:

from mgx_libs.actors.actor import (
    Actor,
    ActorType
)
import logging as log
import time


# implement login in moduls


class Logic:
    def __init__(self, state):
        self.state = state

    def simple(self, msg):

        log.debug(f"simple get data: {msg}")

        msg = msg.get("data")

        return f"simple:{self.state}:{msg}"

    def sleep(self, msg):

        log.debug(f"sleep get data: {msg}")

        msg = msg.get("data")

        time.sleep(1)

        # return f"state {self.state} / msg {msg}"

        return f"sleep:{self.state}:{msg}"

    def stream(self, msg):

        log.debug(f"sleep get data: {msg}")

        time.sleep(1)

        # return f"state {self.state} / msg {msg}"

        return f"sleep:{self.state}"


# define state and func map


class Config:
    def __init__(self):
        self.db = "db"

    def state(self):
        return {"db": self.db}

    def selector(self):
        return {
            "simple": Logic,
            "sleep": Logic,
        }

    # def get_op(self, data):
    #     log.debug(f"get_op: {data}")
    #     return "sleep5"


class Config2:
    def __init__(self):
        self.db = "db2"

    def state(self):
        return {"db2": self.db}

    def selector(self):
        return {
            "simple": Logic,
            "stream": Logic,
        }

    def get_op(self, data):
        log.debug(f"get_op: {data}")
        return "stream"


class Config3:
    def __init__(self):
        self.db = "db2"

    def state(self):
        return {"db2": self.db}

    def selector(self):
        return {
            "simple": Logic,
            "sleep": Logic,
        }

    def get_op(self, data):
        log.debug(f"get_op: {data}")
        return "sleep"


def simple():
    """
    Simple sync example

    """

    conf = Config()
    Actor(actor_type=ActorType.InOut).run(conf)


def stream():
    """
    Stream example

    """

    conf = Config2()
    Actor(actor_type=ActorType.Stream, func="sleep").run(conf)


def pub_sub():
    """
    Pub sub async example

    """
    import threading
    import queue

    q = queue.Queue()

    conf = Config3()

    # pub
    threading.Thread(target=lambda conf, q: Actor(actor_type=ActorType.In,
                                                  queue=q).run(conf),
                     args=(conf, q)).start()

    # subs
    for _ in range(3):
        threading.Thread(target=lambda conf, q: Actor(actor_type=ActorType.Out,
                                                      queue=q).run(conf),
                         args=(conf, q)
                         ).start()


def pub_sub_nokill():
    """
    Pub sub async example

    """
    import threading
    import queue

    q = queue.Queue()

    conf = Config()

    # pub
    threading.Thread(target=lambda conf, q: Actor(actor_type=ActorType.In,
                                                  queue=q,
                                                  none_kill=False).run(conf),
                     args=(conf, q)).start()

    # subs
    for _ in range(3):
        threading.Thread(target=lambda conf, q: Actor(actor_type=ActorType.Out,
                                                      queue=q,
                                                      none_kill=False).run(conf),
                         args=(conf, q)
                         ).start()


def stream_sub():
    """
    stream sub async example

    """
    import threading
    import queue

    q = queue.Queue()

    conf = Config2()

    # pub
    threading.Thread(target=lambda conf, q: Actor(actor_type=ActorType.Stream,
                                                  func="sleep", queue=q).run(conf),
                     args=(conf, q)).start()

    # subs
    for _ in range(3):
        threading.Thread(target=lambda conf, q: Actor(actor_type=ActorType.Out,
                                                      queue=q).run(conf),
                         args=(conf, q)
                         ).start()


def stream_sub_silent():
    """
    stream sub silent async example

    """
    import threading
    import queue

    q = queue.Queue()

    conf = Config2()

    # pub
    threading.Thread(target=lambda conf, q: Actor(actor_type=ActorType.Stream,
                                                  func="sleep", queue=q).run(conf),
                     args=(conf, q)).start()

    # subs
    for _ in range(3):
        threading.Thread(target=lambda conf, q: Actor(actor_type=ActorType.Out,
                                                      queue=q, silent=True).run(conf),
                         args=(conf, q)
                         ).start()


if __name__ == "__main__":
    import sys
    if sys.argv[1] == "simple":
        simple()
    elif sys.argv[1] == "pub_sub":
        pub_sub()
    elif sys.argv[1] == "pub_sub_nokill":
        pub_sub_nokill()
    elif sys.argv[1] == "stream":
        stream()
    elif sys.argv[1] == "stream_sub":
        stream_sub()
    elif sys.argv[1] == "stream_sub_silent":
        stream_sub_silent()

'''
