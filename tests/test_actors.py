"""
Test cases for Actors

"""
import allure
import logging as log
import subprocess as sp
import os


def run_cmd(s):
    try:

        cmd = sp.Popen(s, stdout=sp.PIPE, stderr=sp.PIPE, shell=True)  # pylint: disable=R1732
        _stdout, _stderr = [i.decode('utf8') for i in cmd.communicate()]
        if cmd.returncode != 0:
            log.debug("stdout: %s / stderr: %s", _stdout, _stderr)
            return (1, _stdout)

        return (0, _stdout)

    except Exception as e:
        return (1, str(e))


@allure.feature("mgx-libs")
class TestActor():

    def test_inout(self):

        _, text = run_cmd(
            "cat './tests/data/actor.in'|{}/python ./tests/mock_actors.py simple"
            .format(os.environ["PYENV"]))

        expected = open("./tests/data/actor.out").read()  # pylint: disable=R1732,W1514

        expected = expected.split("\n")

        out = text.split("\n")
        n = 0
        for o in out:
            log.debug("n: %s", n)
            log.debug("out: %s", o)
            log.debug("expected: %s\n", expected[n])
            assert o == expected[n]
            n += 1
