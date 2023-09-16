"""
Test cases for TestActor

"""
import allure

from mgx_libs.actors.mock_actor import (
    MockActor, )


@allure.feature("mgx-libs")
class TestTestActor():

    def test_inout(self):

        actor = MockActor("./tests/mock_actors.py plugin_echo",
                          "./tests/data/actor.yaml")
        actor.test_inout()

        assert True
