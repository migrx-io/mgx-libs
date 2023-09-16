from cassandra.auth import PlainTextAuthProvider
from cassandra.policies import DCAwareRoundRobinPolicy
from cassandra import ConsistencyLevel
from cassandra.cqlengine import connection

from mgx_libs.configs.env import Env

from mgx_libs.cluster.state import (
    State, )

import logging as log


class CassandraConnection():

    def __init__(self, node_name=None, **kwargs):
        self.envs = Env().envs
        self.is_connected = False

        if kwargs.get("consistency") is None:
            self.consistency = ConsistencyLevel.LOCAL_QUORUM
        else:
            self.consistency = kwargs.get("consistency")

        if node_name is None:
            node_name = self.envs["NODE_NAME"]

        # get hosts by current node
        state = State()
        cluster_list = state.cluster_node_list_by_uuid(node_name)

        self.cass_hosts = [x["ip"] for x in cluster_list]

        cass_creds = self.envs["MGX_CASS_CREDS"].split(":")
        self.cass_user = cass_creds[0]
        self.cass_passwd = cass_creds[1]

        self.init()

    def init(self):

        if not self.is_connected:
            # init connections
            log.error("Not connected to cassandra..trying to connect %s",
                      self.cass_hosts)
            try:
                connection.setup(
                    hosts=self.cass_hosts,
                    load_balancing_policy=DCAwareRoundRobinPolicy(),
                    auth_provider=PlainTextAuthProvider(
                        username=self.cass_user, password=self.cass_passwd),
                    default_keyspace=self.envs["MGX_DC_NAME"],
                    protocol_version=3,
                    consistency=ConsistencyLevel.LOCAL_QUORUM,
                    retry_connect=False)

                self.is_connected = True
            except Exception as e:
                log.error(e)
                self.is_connected = False
