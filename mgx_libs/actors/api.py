# API
#  read - receive message from world
#  send - send message to world
#  log  - logging anything

import sys
import json
import logging as log
import os
import signal
from mgx_libs.types.validation import PluginRequestValidation


def kill_actor():
    log.info("Got None msg. kill Actor..")
    os.kill(os.getpid(), signal.SIGKILL)


class API:

    def __init__(self, **kwargs):
        self.none_kill = kwargs.get("none_kill")
        self.asyncf = kwargs.get("asyncf")
        self.silent = kwargs.get("silent")
        self.nowait = kwargs.get("nowait")
        self.validation = PluginRequestValidation(kwargs.get("schema"))

    def unwrap_raw_message(self, msg):

        log.debug("unwrap_raw_message: %s", msg)

        if self.asyncf:

            # kill actor is stop received
            if msg == "":
                kill_actor()

            # get msg id
            idx = msg.find("::") + 2

            log.debug("unwrap_raw_message: idx %s", idx)

            if idx == 1:
                log.error("Not found async attribute")
                kill_actor()

            return msg[:idx], msg[idx:]

        return None, msg

    def wrap_raw_message(self, msg_id, msg):

        if msg is None:
            return None

        if self.asyncf:

            if msg_id is None:
                raise Exception("msg_id not passed")

            return f"{msg_id}{msg}"

        return msg

    def read(self):
        m = sys.stdin.readline()
        m = m.strip().replace("\tncm\t", "\n")
        return m

    def send(self, m):

        if m is None:
            return

        if not self.silent:
            sys.stdout.write("{}\n".format(m.replace("\n", "\tncm\t")))
            sys.stdout.flush()

    def parse_response(self, msg):
        return json.dumps(msg, ensure_ascii=False)

    def validate_request(self, msg):

        # validate msg
        is_valid, err = self.validation.validate(msg)
        log.debug("validation: %s / %s", is_valid, err)
        if not is_valid:
            raise Exception(err)

    def parse_request(self, msg):

        log.debug("_parse_message: %s", msg)

        # got end of line
        if msg == "" and self.none_kill:
            kill_actor()

        msg = json.loads(msg)

        return msg
