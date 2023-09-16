"""
    Cluster state SQL

"""

SQL_CLUSTER_LIST = """
SELECT s.group0, s.uuid, s.detail, s.node
FROM node_world s
WHERE s.group0 != 'None'
  AND s.detail LIKE '%is_vip\": 1%'
  AND s.active = 1
GROUP BY s.group0
"""

SQL_CLUSTER_VIP = """
SELECT detail, node
FROM node_world
WHERE group0 = '{0}'
LIMIT 1
"""

SQL_CLUSTER_VIP_UPDATE = """
UPDATE node_world
SET detail = '{1}',
date = CURRENT_TIMESTAMP
WHERE
group0 = '{0}'
"""

SQL_CLUSTER_CREATE = """
UPDATE node_world
SET group0 = '{0}',
    detail = '{2}',
    date = CURRENT_TIMESTAMP
WHERE group0 != '{0}'
  AND uuid IN ({1})
"""

SQL_CLUSTER_NODE_LIST = """
SELECT uuid, node, hostname, active, date, group0, detail
FROM node_world s
WHERE s.group0 = '{0}'
ORDER BY uuid desc
"""

SQL_CLUSTER_SRV_LIST = """
SELECT detail
FROM node_world s
WHERE s.group0 = '{0}'
LIMIT 1
"""

SQL_CLUSTER_DELETE = """
UPDATE node_world
SET group0 = 'None',
    detail = '{1}',
    date = CURRENT_TIMESTAMP
WHERE group0 = '{0}'
"""

SQL_CLUSTER_NODE_CREATE = """
UPDATE node_world
SET group0 = '{1}',
    detail = '{2}',
    date = CURRENT_TIMESTAMP
WHERE uuid = '{0}'
"""

SQL_CLUSTER_NODE_DELETE = """
UPDATE node_world
SET group0 = 'None',
    detail = '{2}',
    date = CURRENT_TIMESTAMP
WHERE group0 = '{1}'
  AND uuid = '{0}'
"""

SQL_CLUSTER_FREE_NODES = """
SELECT uuid, node, hostname, active, date, group0, detail
FROM node_world s
WHERE s.group0 = 'None'
ORDER BY uuid DESC
"""

SQL_CLUSTER_DEL_FREE_NODES = """
DELETE
FROM node_world
WHERE group0 = 'None'
"""

SQL_CLUSTER_CURRENT_NODE = """
SELECT uuid, node, group0 as cluster, detail
FROM node_world
WHERE uuid = '{0}'
"""

SQL_IS_CLUSTER_GROUP = """
SELECT 1
FROM node_world s
WHERE s.group0 = '{0}'
"""

SQL_CLUSTER_NODE_STATS = """
SELECT s.node, s.cpu_count, s.ram_count,
  s.disk_count, MAX(s.date) as date, AVG(s.cpu_percent) as cpu_per,
  AVG(s.ram_percent) as ram_per, AVG(s.disk_percent) as disk_per,
  AVG(s.net_count) as net_count

FROM node_stat s left join (select node, active, MAX(date) from node_list) l
   on s.node = l.node
WHERE s.date > DATETIME('NOW', '-{0} minutes')

GROUP BY s.node
"""

SQL_CLUSTER_POOL_SYS_STATS = """
SELECT s.node, s.name, l.ram_count as ram,
      s.date, AVG(s.count) as count, AVG(s.cpu_percent) as cpu_per,
      AVG(s.ram_percent) as ram_per

FROM ppool_stat s left join (select node, ram_count, MAX(date)
                                   from node_stat group by node) l
       on s.node = l.node

WHERE s.date > DATETIME('NOW', '-{0} minutes')

GROUP BY s.node, s.name
"""

SQL_CLUSTER_POOL_MSG_STATS = """
SELECT node, name, MAX(date) as date, MAX(error) as error, MAX(timeout) as timeout,
    MIN(running) as running, MAX(ok) as ok,
    round(MAX(elapsed)/1000,2) as max,  round(AVG(elapsed)/1000,2) as avg,
    round(MAX(error) + MAX(timeout) + SUM(nomore),2) as common,
    SUM(nomore) as nomore

FROM ppool_list

WHERE date > DATETIME('NOW', '-{0} minutes')
  AND date < DATETIME('NOW')

GROUP BY node, name
"""
