"""
Request data validation

    Match data types from yaml declaration

"""
import yaml
import re
import os
import logging as log
import ipaddress
import json
import string

from mgx_libs.helpers.memory import MEM_DIMS

EMAIL_REGEXP = re.compile(
    r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')
PATH_REGEXP = re.compile(r'^\/[a-zA-Z0-9_\/-]*[^\/]$')

#
# Type validations
#

def memstr(data):

    _, dim = data[:-2], data[-2:]
    if dim not in MEM_DIMS:
        raise Exception('Unsupported dimension {}/ avaliable {}'.format(
            dim, MEM_DIMS))


def jsonstr(data):
    try:
        json.loads(data)
    except Exception:
        raise Exception("Invalid JSON")


def email(data):
    log.debug("validate email: %s", data)
    if not re.fullmatch(EMAIL_REGEXP, data):
        raise Exception("Invalid email format")


def path(data):
    log.debug("validate path: %s", data)
    if not re.fullmatch(PATH_REGEXP, data) and data != "/":
        raise Exception("Invalid path format")


def validate_type(data_raw, typ):

    all_data = []
    if not isinstance(data_raw, list):
        all_data.append(data_raw)
    elif isinstance(data_raw, list):
        all_data = data_raw

    for data in all_data:
        if typ == "int":
            int(data)
        elif typ == "float":
            float(data)
        elif typ == "email":
            email(data)
        elif typ == "jsonstr":
            jsonstr(data)
        elif typ == "memstr":
            memstr(data)
        elif typ == "path":
            path(data)

#
# Class request validation
#


def unwrap_reference(msg, model):

    unwrapped_msg = {}

    log.debug("model: %s", model)
    log.debug("msg: %s", msg)

    for k, v in msg.items():
        if isinstance(v, str) and v.startswith("${"):
            item = v[2:-1]

            unwrapped_msg[k] = model.get(item)
        else:
            unwrapped_msg[k] = v

    log.debug("unwrapped: %s", unwrapped_msg)

    return unwrapped_msg


def open_spec(desc):

    log.debug("open spec %s", desc)

    is_desc = False
    data = {}
    if desc is not None and os.path.isfile(desc):
        is_desc = True
        with open(desc, encoding="utf-8") as f:
            data = yaml.safe_load(f.read())

    return is_desc, data


class PluginRequestValidation():

    def __init__(self, desc):

        self.desc = desc

        self.is_desc = False
        self.ops = {}
        self.is_desc, data = open_spec(self.desc)

        if self.is_desc:
            self.ops = data.get("ops", {})
            self.models = data.get("models", {})

    def validate(self, msg):

        if not self.is_desc:
            log.debug("validatation file %s not found", self.desc)
            return True, None

        try:
            ctx = msg.get("context", {})
            data = msg.get("data", {})

            log.debug("validation ctx: %s", ctx)
            log.debug("validation data: %s", data)

            if ctx.get("op") is None:
                return True, None

            meta = self.ops.get(ctx["op"], {}).get("request", {}).get("meta")
            context_model = self.ops.get(ctx["op"], {}).get("model")

            # add context_model to request context
            ctx["perm_ctx_model"] = context_model

            # add login from current user if is_login is not provided
            if ctx.get("perm_ctx", {}).get("is_login") is False:

                if meta is not None and "login" in meta.keys():
                    log.debug("overwrite login data parameter")
                    data["login"] = ctx.get("login")

            # if user is_login but omit login parameter
            elif ctx.get("perm_ctx", {}).get("is_login") is True:

                if meta is not None and "login" in meta.keys():
                    if data.get("login") is None:
                        data["login"] = ctx.get("login")

            if meta is None:
                return True, None

            meta = unwrap_reference(meta, self.models.get(context_model))

            for k, v in meta.items():

                log.debug("validate filed: %s = %s", k, v)

                # if validation is empty -> skip
                if v is None:
                    continue

                if v.get("required") and data.get(k) is None:
                    raise Exception(f"value {k} is required")

                if v.get("choices") is not None:
                    log.debug("choises: %s", v.get("choices"))
                    if data.get(k) is not None and data.get(k) not in v.get(
                            "choices"):
                        raise Exception("value {} not in {}".format(
                            k, v.get("choices")))

                if v.get("nargs") is not None:
                    if data.get(k) is not None and not isinstance(
                            data.get(k), list):
                        raise Exception("value {} not list".format(k))

                if v.get("type") is not None:
                    if data.get(k) is not None:
                        log.debug("data/%s: %s ", data, k)
                        validate_type(data.get(k), v.get("type"))

            return True, None

        except Exception as e:
            return False, str(e)
