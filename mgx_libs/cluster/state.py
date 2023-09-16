from mgx_libs.configs.env import Env
import json
import logging as log
import sqlite3
import time
from mgx_libs.cluster.sql import (
    SQL_CLUSTER_FREE_NODES,
    SQL_CLUSTER_SRV_LIST,
    SQL_CLUSTER_NODE_LIST,
    SQL_CLUSTER_DEL_FREE_NODES,
    SQL_CLUSTER_DELETE,
    SQL_CLUSTER_NODE_DELETE,
    SQL_CLUSTER_CREATE,
    SQL_CLUSTER_VIP,
    SQL_CLUSTER_NODE_CREATE,
    SQL_CLUSTER_VIP_UPDATE,
    SQL_CLUSTER_LIST,
    SQL_CLUSTER_CURRENT_NODE,
    SQL_IS_CLUSTER_GROUP,
    SQL_CLUSTER_NODE_STATS,
    SQL_CLUSTER_POOL_SYS_STATS,
    SQL_CLUSTER_POOL_MSG_STATS,
)


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


class SQLite():

    def __init__(self, file):
        log.debug("open db file %s", file)
        self.file = file

    def __enter__(self):
        self.conn = sqlite3.connect(self.file)
        self.conn.row_factory = dict_factory
        return self.conn.cursor()

    def __exit__(self, typ, value, traceback):
        self.conn.commit()
        self.conn.close()


def parse_cluster_details(data):

    detail = {}
    try:
        detail = json.loads(data)
    except Exception as e:
        log.error("parse_cluster_details: %s", e)

    return detail


class State:

    def __init__(self, db=None):
        env = Env().envs
        if db is None:
            self.db = env["MGX_DB_NAME"]
        else:
            self.db = db

    def cluster_node_stats(self, last=1):

        stats = {"system": []}
        # get current state
        with SQLite(self.db) as db:
            cur = db.execute(SQL_CLUSTER_NODE_STATS.format(last))
            for i in cur.fetchall():

                uuid, ip = i["node"].split("@")
                i["uuid"] = uuid
                i["ip"] = ip
                del i["node"]

                log.debug("fetched: %s", i)
                stats["system"].append(i)

        return stats

    def cluster_pool_stats(self, last=1):

        stats = {"system": [], "metrics": []}
        # get current state
        with SQLite(self.db) as db:
            cur = db.execute(SQL_CLUSTER_POOL_SYS_STATS.format(last))
            for i in cur.fetchall():

                uuid, ip = i["node"].split("@")
                i["uuid"] = uuid
                i["ip"] = ip
                del i["node"]

                log.debug("fetched: %s", i)
                stats["system"].append(i)

        # get pool metrics
        with SQLite(self.db) as db:
            cur = db.execute(SQL_CLUSTER_POOL_MSG_STATS.format(last))
            for i in cur.fetchall():

                uuid, ip = i["node"].split("@")
                i["uuid"] = uuid
                i["ip"] = ip
                del i["node"]

                log.debug("fetched: %s", i)
                stats["metrics"].append(i)

        return stats

    def cluster_current_node(self, uuid):

        log.debug("cluster current node %s", uuid)

        node = None
        # get current state
        with SQLite(self.db) as db:
            cur = db.execute(SQL_CLUSTER_CURRENT_NODE.format(uuid))
            for i in cur.fetchall():
                log.debug("fetched: %s", i)
                node = i
                node["detail"] = parse_cluster_details(i["detail"])

        return node

    def cluster_is_group_exists(self, name):

        log.debug("cluster group exists %s", name)
        # get current state
        with SQLite(self.db) as db:
            cur = db.execute(SQL_IS_CLUSTER_GROUP.format(name))
            for _ in cur.fetchall():
                return True

        return False

    def cluster_freenode_list(self):

        res = []
        n = 0

        with SQLite(self.db) as db:
            cur = db.execute(SQL_CLUSTER_FREE_NODES)

            for i in cur.fetchall():
                n += 1
                log.debug("fetched node: %s", i)
                res.append({
                    "uid": n,
                    "uuid": i["uuid"],
                    "ip": i["node"].split("@")[1],
                    "hostname": i["hostname"],
                    "created": i["date"]
                })

        return res

    def cluster_service_list(self, name):

        res = []
        with SQLite(self.db) as db:
            cur = db.execute(SQL_CLUSTER_SRV_LIST.format(name))

            for i in cur.fetchall():
                log.debug("fetched node: %s", i)

                detail = parse_cluster_details(i["detail"])

                for k in detail.get("service", {}).keys():
                    res.append(k)

        return res

    def cluster_node_list_by_uuid(self, uuid):
        # get cluster name
        node = self.cluster_current_node(uuid)
        log.debug("current node: %s", node)

        if node is not None:
            return self.cluster_node_list(node["cluster"])

        return []

    def cluster_vip_by_uuid(self, uuid):

        # get cluster name
        node = self.cluster_current_node(uuid)
        log.debug("current node: %s", node)
        if node is not None:

            cluster_list = self.cluster_list()
            vip_node = [
                x for x in cluster_list if x["cluster"] == node["cluster"]
            ]

            log.debug("vip_node: %s", vip_node)

            if len(vip_node) > 0:

                vip_node = vip_node[0]

                return uuid == vip_node["vip_host"].get("uuid"), \
                    vip_node["vip_host"].get("vip"), \
                    vip_node["vip_host"].get("ip")

        return None, False, None

    def cluster_node_list(self, name):

        if not self.cluster_is_group_exists(name):
            if name == "None":
                raise Exception("Free nodes are not found")

            raise Exception(f"Cluster {name} is not found")

        res = []
        n = 0

        with SQLite(self.db) as db:
            cur = db.execute(SQL_CLUSTER_NODE_LIST.format(name))

            for i in cur.fetchall():
                n += 1
                log.debug("fetched node: %s", i)

                res.append({
                    "uid":
                    n,
                    "uuid":
                    i["uuid"],
                    "node":
                    i["node"],
                    "ip":
                    i["node"].split("@")[1],
                    "hostname":
                    i["hostname"],
                    "status":
                    (lambda x: x == 1 and "UP" or "DOWN")(i["active"]),
                    "created":
                    i["date"],
                    "cluster":
                    i["group0"]
                })

        return res

    def cluster_freenode_delete(self):

        log.debug("delete freenode cluster")

        with SQLite(self.db) as db:
            db.execute(SQL_CLUSTER_DEL_FREE_NODES)

    def cluster_delete(self, name):

        # check if exist
        if not self.cluster_is_group_exists(name):
            raise Exception(f"Cluster {name} not exists")

        log.debug("delete cluster %s", name)

        with SQLite(self.db) as db:
            db.execute(
                SQL_CLUSTER_DELETE.format(
                    name,
                    json.dumps({
                        "vip": "127.0.0.1",
                        "timestamp": time.time()
                    })))

    def cluster_node_delete(self, name, nid):

        # get nodes from free
        cluster_list = self.cluster_node_list(name)
        node = None
        for n in cluster_list:
            log.debug("cluster_list: n: %s == %s", n, nid)
            if str(n["uid"]) == str(nid):
                node = n["uuid"]

        if node is None:
            raise Exception(f"Node {nid} not exists in cluster {name}")

        log.debug("delete cluster node %s", node)

        with SQLite(self.db) as db:
            db.execute(
                SQL_CLUSTER_NODE_DELETE.format(
                    node, name,
                    json.dumps({
                        "vip": "127.0.0.1",
                        "timestamp": time.time()
                    })))

    def cluster_create(self, name, node_ids, vip):

        # check if exist
        if self.cluster_is_group_exists(name):
            raise Exception(f"Cluster {name} already exists")

        # get nodes from free
        free_list = self.cluster_freenode_list()
        node_uuids = []
        for n in free_list:
            if str(n["uid"]) in node_ids or node_ids == ['*']:
                node_uuids.append(n["uuid"])

        if len(node_uuids) == 0:
            raise Exception("Node IDs not exists")

        log.debug("create cluster %s / node_uuids: %s/ vip: %s", name,
                  node_uuids, vip)

        sql = SQL_CLUSTER_CREATE.format(
            name, ','.join(['?'] * len(node_uuids)),
            json.dumps({
                "vip": vip,
                "timestamp": time.time()
            }))
        # update
        with SQLite(self.db) as db:
            db.execute(sql, node_uuids)

    def cluster_node_create(self, name, nid):

        # get nodes from free
        free_list = self.cluster_freenode_list()
        node = None
        for n in free_list:
            log.debug("create node %s == %s", n, nid)
            if str(n["uid"]) == str(nid):
                node = n["uuid"]

        if node is None:
            raise Exception(f"Node {nid} not exists in free nodes")

        log.debug("cluster node create %s / %s", node, name)

        detail = {}

        # get current state
        with SQLite(self.db) as db:
            cur = db.execute(SQL_CLUSTER_VIP.format(name))
            for i in cur.fetchall():
                log.debug("fetched: %s", i)

                detail = parse_cluster_details(i["detail"])

        log.debug("detail: %s", detail)

        # update
        with SQLite(self.db) as db:
            db.execute(
                SQL_CLUSTER_NODE_CREATE.format(node, name, json.dumps(detail)))

    def cluster_vip_change(self, name, vip):

        log.debug("change vip to %s", vip)

        detail = {}

        # get current state
        with SQLite(self.db) as db:
            cur = db.execute(SQL_CLUSTER_VIP.format(name))
            for i in cur.fetchall():
                log.debug("fetched: %s", i)

                detail = parse_cluster_details(i["detail"])
                detail["vip"] = vip

        log.debug("new detail: %s", detail)

        # update
        with SQLite(self.db) as db:
            db.execute(SQL_CLUSTER_VIP_UPDATE.format(name, json.dumps(detail)))

    def cluster_service_change(self, name, service, code, check):

        log.debug("change service state %s / %s", service, code)

        detail = {}
        # get current state
        with SQLite(self.db) as db:
            cur = db.execute(SQL_CLUSTER_VIP.format(name))
            for i in cur.fetchall():
                log.debug("fetched: %s", i)
                detail = parse_cluster_details(i["detail"])

        service_list = detail.get("service", {})
        service_list[service] = {"code": code, "check": check}
        detail["service"] = service_list

        log.debug("new detail: %s", detail)

        # update
        with SQLite(self.db) as db:
            db.execute(SQL_CLUSTER_VIP_UPDATE.format(name, json.dumps(detail)))

    def cluster_list(self):

        res = []
        with SQLite(self.db) as db:
            cur = db.execute(SQL_CLUSTER_LIST)
            for i in cur.fetchall():
                log.debug("fetched node: %s", i)

                detail = parse_cluster_details(i["detail"])

                res.append({
                    "cluster": i["group0"],
                    "vip_host": {
                        "uuid": i["uuid"],
                        "ip": i["node"].split("@")[1],
                        "vip": detail.get("vip")
                    }
                })

        return res
