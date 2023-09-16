"""
    Object mapper for cassandra db

    1. Create schema and apply to cassandra

        CREATE TABLE IF NOT EXISTS aaa_namespaces (

                ctx_cluster text,
                ctx_ns text,
                ctx_path text,

                ---------- object specific data
                cluster text,
                ns text,
                dirs text,
                descr text,
                ----------

                ctx_pathz set<text>,
                ctx_prop text,

                PRIMARY KEY ((ctx_cluster, ctx_ns), ctx_path,
                            cluster, ns)

        );


    2. Define model in your code

        class Namespaces(BaseModel):
            __table_name__ = "aaa_namespaces"
            # __options__ = {'default_time_to_live': 20}

            cluster = columns.Text(required=True, primary_key=True)
            ns = columns.Text(required=True, primary_key=True)
            dirs = columns.Text()
            descr = columns.Text()


"""
from datetime import datetime, timezone
from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model
from cassandra.cqlengine.query import BatchQuery
# from cassandra.cqlengine.query import BatchType
import json
from cassandra.cqlengine.query import LWTException
from mgx_libs.apis.spec import evalExpression

from mgx_libs.helpers.workers import notify

import copy
import pytz

import logging as log


def check_perm_rule(rule, model, role, user):

    log.debug("check_perm_rule:\n rule: %s\n model: %s\nrole: %s\nuser: %s",
              rule, model, role, user)

    # role
    if rule.get("role") is not None:

        checks = [
            evalExpression(x, role)
            for x in rule.get("role", {}).get("matchExpressions", [])
        ]

        log.debug("role checks: %s", checks)

        if not all(checks):
            return False

    # user
    if rule.get("user") is not None:

        checks = [
            evalExpression(x, user)
            for x in rule.get("user", {}).get("matchExpressions", [])
        ]

        log.debug("user checks: %s", checks)

        if not all(checks):
            return False

    # object
    if rule.get("object") is not None and model is not None:

        checks = [
            evalExpression(x, model)
            for x in rule.get("object", {}).get("matchExpressions", [])
        ]

        log.debug("object checks: %s", checks)

        if not all(checks):
            return False

    return True


def parse_obj_from_permission(obj_name, model_name, obj):

    if model_name == "Permissions":

        if obj_name == "ClusterPermissions":

            path = obj.get("path", "")

            # skip when plugin call
            if obj.get(
                    "method"
            ) == 'PUT' and path == '/cluster/{cluster}/plugins/{plugin}':
                return False, None

            obj = {
                "data":
                ".".join([
                    x for x in path.split("/")
                    if not x.startswith("{") and x != ""
                ])
            }
            return True, obj

        if obj_name == "PluginPermissions":

            plugin = obj.get("plugin", "")
            cmd = obj.get("op", "")

            obj = {"data": ".".join([plugin] + cmd.split("_"))}
            return True, obj

        return False, None

    return False, None


def parse_perm_rules(ctx, obj_name, obj):

    log.debug("ctx: %s", ctx)
    log.debug("obj: %s", obj)
    log.debug("obj_name: %s", obj_name)

    ctx = ctx.copy()

    model_name = ctx.get("ctx_perm_ctx_model")

    if model_name is None:
        return True

    log.debug("model_name: %s", model_name)
    # check current model and context model
    if obj_name.lower() != model_name.lower() and model_name != "Permissions":
        return True

    ok, data = parse_obj_from_permission(obj_name, model_name, obj)
    if ok:
        obj = data

    # get context
    rules = ctx.get("ctx_perm_ctx")
    if rules is None:
        return True

    rules = json.loads(rules.get("context"))

    role = ctx.get("ctx_perm_ctx", {}).get("role")
    user = ctx.get("ctx_perm_ctx", {}).get("user")
    model = obj

    log.debug("rules: %s", rules)

    # if no rules - no checks
    if rules is None:
        return True

    for r in rules:
        rule = r.get("matchTerm", {})
        log.debug("rule: %s", rule)
        if check_perm_rule(rule, model, role, user):
            return True

    return False


def split_path_to_chunks(path):

    acc = ""
    arr = set()
    for p in path.split("/"):
        if acc == "/":
            acc = ""
        acc = f"{acc}/{p}"
        arr.add(acc)

    return arr


class BaseModel(Model):
    __abstract__ = True

    context = {}
    req = {}

    ctx_cluster = columns.Text(required=True,
                               primary_key=True,
                               partition_key=True)
    ctx_ns = columns.Text(required=True, primary_key=True, partition_key=True)
    ctx_path = columns.Text(required=True,
                            primary_key=True,
                            partition_key=False)

    ctx_pathz = columns.Set(value_type=columns.Text)
    ctx_prop = columns.Text()

    ctx_is_changed = columns.Boolean()

    @classmethod
    def ctx(cls, **kwargs):

        cls.context = {}

        # rename to ctx_{key}
        kwargs = {f"ctx_{k}": v for k, v in kwargs.items()}
        kwargs["ctx_pathz"] = split_path_to_chunks(kwargs.get("ctx_path", "/"))
        cls.context = kwargs

        return cls

    @classmethod
    def insert(cls, ttl=None, **kwargs):

        # remove None if exists to not override default
        kwargs = {k: v for k, v in kwargs.items() if v is not None}

        # check context rules before insert
        if not parse_perm_rules(cls.context, cls.__name__, kwargs):
            raise Exception("Not authorized (context rules)")

        obj = None

        for p in cls.context["ctx_pathz"]:

            kwargs.update(cls.context)
            kwargs["ctx_path"] = p

            kwargs["ctx_is_changed"] = True

            try:
                if ttl is not None:
                    obj = cls.ttl(ttl).if_not_exists().create(**kwargs)
                else:
                    obj = cls.if_not_exists().create(**kwargs)

            except LWTException:
                raise Exception("Object already exists")

    @classmethod
    def filter(cls, *args, **kwargs):

        kwargs["ctx_cluster"] = cls.context.get("ctx_cluster")
        kwargs["ctx_ns"] = cls.context.get("ctx_ns")
        kwargs["ctx_path"] = cls.context.get("ctx_path")
        cls.req = kwargs

        return cls.objects.filter(*args, **kwargs)

    def store(self):

        classz = self.__class__
        req = classz.req
        changed_values = [
            x for x in self.get_changed_columns() if x not in req
        ]

        req["ctx_path"] = "/"
        obj = classz.objects.filter(**req).get()

        # check context rules before update
        if not parse_perm_rules(classz.context, classz.__name__, obj.json()):
            raise Exception("Not authorized (context rules)")

        for v in changed_values:
            obj[v] = self[v]

        # add flags for identify change
        if len(changed_values) != 0:
            obj["ctx_is_changed"] = True
            self.ctx_is_changed = True

        # check context rules before update. new state
        if not parse_perm_rules(classz.context, classz.__name__, obj.json()):
            raise Exception("Not authorized (context rules for new state)")

        with BatchQuery() as b:
            for p in self.ctx_pathz:
                obj["ctx_path"] = p
                obj.batch(b).save()

    def remove(self):

        classz = self.__class__
        req = classz.req

        req["ctx_path"] = "/"
        obj = classz.objects.filter(**req).get()

        # check context rules before update
        if not parse_perm_rules(classz.context, classz.__name__, obj.json()):
            raise Exception("Not authorized (context rules)")

        with BatchQuery() as b:
            for p in self.ctx_pathz:
                obj["ctx_path"] = p
                obj.batch(b).delete()

    def movep(self, newp):

        classz = self.__class__
        req = classz.req

        req["ctx_path"] = "/"
        uobj = classz.objects.filter(**req).get()

        e_data = dict(uobj)

        # delete old
        with BatchQuery() as b:
            for p in self.ctx_pathz:
                if p != "/":
                    uobj["ctx_path"] = p
                    uobj.batch(b).delete()

        # insert with new path and pathz
        kwargs = {
            k: v
            for k, v in e_data.items()
            if not k.startswith("ctx_") and v is not None
        }

        path_chunks = split_path_to_chunks(newp)
        for p in path_chunks:
            if p != "/":
                kwargs.update(classz.context)
                kwargs["ctx_path"] = p
                kwargs["ctx_is_changed"] = True
                classz.if_not_exists().create(**kwargs)

        # update
        uobj.path = newp
        uobj.ctx_pathz = path_chunks
        uobj.store()

    def json(self, keys=None, notkeys=None):

        if notkeys is None:
            notkeys = []

        json_dict = dict(self)
        if keys is None:
            json_dict = {
                k: v
                for k, v in json_dict.items()
                if not k.startswith("ctx_") and k not in notkeys
            }
        else:
            json_dict = {k: v for k, v in json_dict.items() if k in keys}

        return json.loads(
            json.dumps(json_dict, default=set_dafault_with_cxt(self.context)))


def set_dafault_with_cxt(ctx):

    def set_default(obj):
        if isinstance(obj, set):
            return list(obj)
        if isinstance(obj, datetime):
            if ctx.get("ctx_tzname") is not None:
                return obj.astimezone(pytz.timezone(
                    ctx.get("ctx_tzname"))).isoformat()
            return obj.isoformat()

        raise TypeError

    return set_default
