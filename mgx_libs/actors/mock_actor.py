"""
Test cases for Actors

"""
import logging as log
import subprocess as sp
import os
import yaml
import json

log.getLogger().setLevel(log.DEBUG)


def run_cmd(s, msg):
    try:

        with sp.Popen(s, stdin=sp.PIPE, stdout=sp.PIPE, shell=True) as cmd:

            # send msg
            cmd.stdin.write(msg.encode("utf8"))
            cmd.stdin.flush()

            # read msg
            _stdout = cmd.stdout.readline()

            return (0, _stdout.decode("utf8"))

    except Exception as e:
        return (1, str(e))


def rm_s_q(msg):
    return str(msg).replace("'", "\"")


class MockActor():

    def __init__(self, cmd, desc=None):
        self.cmd = cmd
        self.desc = desc

        self.is_desc = False
        self.ops = []
        self.tests_setup = []
        self.tests_teardown = []

        log.debug("validatation check file exists %s", self.desc)
        log.debug("validatation current dir %s", os.getcwd())

        if desc is not None and os.path.isfile(self.desc):
            self.is_desc = True

            with open(self.desc, encoding="utf-8") as f:
                data = yaml.safe_load(f.read())

                self.ops = data.get("ops", [])
                self.tests_setup = data.get("tests_setup", [])
                self.tests_teardown = data.get("tests_teardown", [])

    def run_op(self, ctx_g, op, opv, func=None):

        log.debug("test_inout: op : %s", op)
        log.debug("test_inout: opv : %s", opv)

        examples_in = opv.get("request", {}).get("examples", [])
        examples_out = opv.get("response", {}).get("examples", [])

        req_text = []
        res_text = []

        if ctx_g is None:
            ctx = {"op": op}
        else:
            ctx = ctx_g
            ctx["op"] = ctx.get("op", op)

        log.debug("final ctx: %s", ctx)

        ctx = json.dumps(ctx)

        for e in examples_in:
            log.debug("test_inout: examples_in : %s", e)

            if isinstance(e, dict):
                req = json.dumps(e)
            else:
                req = rm_s_q(e)

            req_text.append('{{"context": {0}, "data": {1}}}'.format(
                rm_s_q(ctx), req))

        for e in examples_out:
            log.debug("test_inout: examples_out : %s", e)

            if isinstance(e, dict):
                if e.get("error") is not None:
                    res_text.append(
                        '{{"context": {0}, "error": "{1}"}}\n'.format(
                            rm_s_q(ctx), e.get("error")))
                else:
                    res_text.append('{{"context": {0}, "data": {1}}}\n'.format(
                        rm_s_q(ctx), rm_s_q(json.dumps(e))))

            elif isinstance(e, list):
                res_text.append('{{"context": {0}, "data": {1}}}\n'.format(
                    rm_s_q(ctx), rm_s_q(json.dumps(e))))
            else:
                res_text.append('{{"context": {0}, "data": "{1}"}}\n'.format(
                    rm_s_q(ctx), rm_s_q(e)))

        # call sync each request
        n = 0
        for r in req_text:

            log.debug("request: %s", r)

            log.debug("echo '%s\n'|%s/python %s", os.environ.get("PYENV", ""),
                      self.cmd, r)

            log.debug("test_inout:\nreq_text : %s\nres_text: %s", r,
                      res_text[n])
            _, text = run_cmd(
                "ASYNC_DISABLE=y {0}/python {1}".format(
                    os.environ.get("PYENV", ""), self.cmd), "{}\n".format(r))
            n += 1

            out_json = json.loads(text)

            if out_json.get("context", {}).get("perm_ctx_model") is not None:
                del out_json["context"]["perm_ctx_model"]
            text = "{}\n".format(json.dumps(out_json))

            log.debug("out: %s / type %s", text, type(text))
            log.debug("exp: %s / type %s", res_text[n - 1],
                      type(res_text[n - 1]))

            if func is None:
                assert text == res_text[n - 1]
            else:
                assert func(text, res_text[n - 1])

    def test_inout(self, ctx_g=None):

        if ctx_g is None:
            ctx_g = {}

        log.debug("start mock actor: desc: %s", self.desc)

        if not self.is_desc:
            return

        # run setup
        for op in self.tests_setup:
            opv = self.ops[op]
            self.run_op(ctx_g.copy(), op, opv, lambda _x, _y: True)

        # run tests
        for op, opv in [(k, v) for k, v in self.ops.items()
                        if v.get("test", False)]:
            self.run_op(ctx_g.copy(), op, opv)

        # run teardown
        for op in self.tests_teardown:
            opv = self.ops[op]
            self.run_op(ctx_g.copy(), op, opv, lambda _x, _y: True)
