from mgx_libs.apis.request import (
    Request,
    Context,
)

from mgx_libs.configs.flows import (
    Flow, )
from mgx_libs.configs.env import Env
import yaml
import json
from mgx_libs.types.validation import open_spec, unwrap_reference
import logging as log

CONTEXT_OPERATORS = [
    "In", "NotIn", "Contains", "NotContains", "InDict", "NotInDict",
    "StartsWith", "NotStartsWith"
]


def compareStartsWitn(val, exp):

    # if val is list iterate
    if isinstance(val, list):
        for v in val:
            if v.startswith(exp):
                return True
        return False

    if val.startswith(exp):
        return True

    return False


def evalExpression(expr, data):

    log.debug("evalExpression: expr: %s data: %s key: %s", expr, data,
              expr['key'])

    val = data.get(expr["key"])

    log.debug("evalExpression: value %s / values %s", val, expr['values'])

    if val is None:
        return True

    if expr["operator"] == "InDict":
        for exp in expr["values"]:
            tokens = exp.split(".")

            for t in tokens:
                if val.get(t) is None:
                    return False

                val = val.get(t)
            return True

    elif expr["operator"] == "NotInDict":
        for exp in expr["values"]:
            tokens = exp.split(".")

            for t in tokens:
                if val.get(t) is None:
                    return True
                val = val.get(t)
            if val is None:
                return True
            return False

    elif expr["operator"] == "StartsWith":
        for exp in expr["values"]:
            if compareStartsWitn(val, exp):
                return True
        return False

    elif expr["operator"] == "NotStartsWith":
        for exp in expr["values"]:
            if not compareStartsWitn(val, exp):
                continue
            return False
        return True

    elif expr["operator"] == "In":
        if val in expr["values"]:
            return True
        return False

    elif expr["operator"] == "NotIn":
        if val not in expr["values"]:
            return True
        return False

    elif expr["operator"] == "Contains":
        if set(expr["values"]).issubset(set(val)):
            return True
        return False

    elif expr["operator"] == "NotContains":
        if not set(expr["values"]).issubset(set(val)):
            return True
        return False

    return False


def get_event_operation(method, path, data):

    is_exists, cmd_map = open_spec(Env().envs["MGX_GW_TMP"])

    if not is_exists:
        return None

    cmd_map = cmd_map.get("cmd_map", {})

    log.debug("get_event_operation: cmd_map: %s", cmd_map)

    verbs = []

    log.debug("get_event_operation: method: %s path: %s data: %s", method,
              path, data)

    if path.find("/plugins/") > 0 and method == "PUT":
        plugin_id = path.split("/")[-1]
        op = data.get("context", {}).get("op", "")
        verbs = [plugin_id] + op.split("_")

    else:
        # cluster
        cmds = get_subcommands(path[8:])
        verb = resolve_method(method.lower(), path)
        verbs = cmds + [verb]

    log.debug("get_event_operation: verbs: %s", verbs)

    d = cmd_map.get(verbs[0], {})

    log.debug("get_event_operation: before: %s", d)

    for v in verbs[1:]:
        log.debug("get_event_operation: op: %s", v)
        if d.get(v) is not None:
            d = d.get(v)

    log.debug("get_event_operation: final %s", d)

    if isinstance(d, (tuple, list)):
        return d[2].strip()

    return None


def build_tree(counts, parts, value):

    branch = counts
    for part in parts[0:-1]:
        branch = branch.setdefault(part, {})
    branch[parts[-1]] = value

    return counts


def get_subcommands(url):
    return [x for x in url.split("/") if not x.startswith("{")]


def build_tree_from_url(url, value):

    paths = get_subcommands(url)

    return build_tree({}, paths, value)


def resolve_method(method, p):
    if method == "get":
        if p.endswith('}'):
            return "show"

        return "list"

    if method == "post":
        return "add"
    if method == "delete":
        return "del"
    if method == "put":
        return "update"

    return None


def merge(a, b, path=None):
    "merges b into a"
    if path is None:
        path = []

    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge(a[key], b[key], path + [str(key)])
            elif a[key] == b[key]:
                pass  # same leaf value
            else:
                raise Exception('Conflict at %s' % '.'.join(path + [str(key)]))
        else:
            a[key] = b[key]
    return a


def build_from_body(example):

    msg = {}
    for k, v in example.items():
        if isinstance(v, list):
            msg[k] = {"required": True, "nargs": "*"}
        elif isinstance(v, dict):
            msg[k] = {"required": True}
        elif v.isnumeric():
            msg[k] = {"required": True, "type": "int"}
        elif v.find("|") > 0:
            msg[k] = {"required": True, "choices": v.split("|")}
        else:
            msg[k] = {"required": True}

    return msg


def build_request(params):

    msg = {}
    for p in params.get("parameters", []):
        if p["in"] in ["path", "query"]:
            msg[p["name"]] = {"required": p.get("required", False)}
        elif p["in"] == "body":
            msg.update(build_from_body(p["schema"].get("example", {})))

    return msg


def add_help_cmd(subcmd, cmd, desc):

    cmd_help = "\n"
    n = 1
    cmds = subcmd + [cmd]

    for c in cmds:
        if len(cmds) > n:
            cmd_help += "{}{}\n".format(" " * (n + 1), c)
        else:
            cmd_help += "{}{} - {}\n".format(" " * (n + 1), c, desc)
        n += 1

    return cmd_help


def build_plugin_meta(plugin, data):

    result = {"cmd_map": {}, "cmd_docs": {}}

    # generate docs
    result["cmd_docs"][plugin] = f"{data['desc']}"

    cmd_map = {}
    add_helps = ""

    # generate cmd map
    for p, v in data["ops"].items():

        final_cmds = {}

        tokens = [plugin] + p.split("_")

        msg = v.get("request", {}).get("meta", {})

        context_model = data.get("models", {}).get(v.get("model"), {})
        msg = unwrap_reference(msg, context_model)

        # unwrap reference if exists

        desc = v.get("desc").replace("\n", "")

        cmd_name = tokens[-1]

        final_cmds[cmd_name] = (('PLUGIN', (plugin, p)), msg, desc,
                                context_model)

        merge(cmd_map, build_tree({}, tokens[:len(tokens) - 1], final_cmds))

        add_helps += add_help_cmd(tokens[:len(tokens) - 1], cmd_name, desc)

    result["cmd_docs"][plugin] += add_helps
    result["cmd_map"] = cmd_map

    return result


def build_cluster_meta(data):

    result = {"cmd_map": {}, "cmd_docs": {}}

    # generate docs
    result["cmd_docs"] = {
        "cluster": f"{data['info']['description']} {data['info']['version']}"
    }

    cmd_map = {}
    add_helps = ""

    # generate cmd map
    for p, v in data["paths"].items():

        # skip auth
        if p.find("/auth") > 0:
            continue

        final_cmds = {}

        for c, params in v.items():

            # skip plugin call and resource cmds
            if p.find("/plugins") > 0 and c == "put":
                continue

            msg = build_request(params)

            cmd_name = resolve_method(c, p)
            desc = params.get("description").replace("<br/>", "")

            final_cmds[cmd_name] = ((c.upper(), p[7:]), msg, desc)

        merge(cmd_map, build_tree_from_url(p[8:], final_cmds))

        add_helps += add_help_cmd(get_subcommands(p[8:]), cmd_name, desc)

    result["cmd_docs"]["cluster"] += add_helps
    result["cmd_map"] = cmd_map

    return result


class PluginSpec():

    def __init__(self, plugin_spec=None):
        self.plugin_spec = plugin_spec
        self.plugin_list = Flow().list()

    def get(self):

        meta = {}

        for spec in self.plugin_list:

            if self.plugin_spec is None:

                # if name contain "-" -> skip and don't load spec
                if spec[9:].find("-") >= 0:
                    continue

                status, data = Request(Context("mgx")).call(
                    "/{}".format(spec[9:]), {
                        "context": {
                            "op": "get_actor_meta",
                            "system_call": True,
                            "plugin_name": spec
                        }
                    }, "POST")

            else:

                is_exists, data = open_spec(self.plugin_spec.format(spec))

                if is_exists:
                    status = 200

            if status == 200:
                plugin_name = spec[9:]
                merge(meta,
                      build_plugin_meta(plugin_name, data.get("data", data)))

        return meta


class GWSpec():

    def __init__(self, api_spec=None):
        self.api_spec = api_spec

    def get(self):

        if self.api_spec is None:
            ctx = Context("MGX_GW")
            status, text = Request(ctx).call("/apidocs/apispec_1.json", {},
                                             "GET")
        else:

            # read from file
            is_exists, text = open_spec(self.api_spec)
            if is_exists:
                status = 200
            else:
                status = 500

        if status != 200:
            raise Exception(text)

        meta = build_cluster_meta(text)

        return meta


class APISpec():

    def __init__(self, api_spec=None, plugin_spec=None):
        self.api_spec = api_spec
        self.plugin_spec = plugin_spec

    def get(self):
        cluster_meta = GWSpec(self.api_spec).get()
        plugin_meta = PluginSpec(self.plugin_spec).get()

        meta = merge(cluster_meta, plugin_meta)

        return meta


def unwrap_context(data, spaces):
    model_str = ""
    model_str += "{}object\n".format(" " * spaces)
    for k, v in data.items():
        model_str += "{}{} - {}\n".format(" " * (spaces + 2), k,
                                          v.get("desc", ""))
    return model_str


def unwrap_print(val, desc_str=None, cnt=0):

    if desc_str is None:
        desc_str = []

    if isinstance(val, dict):
        for k, v in val.items():
            desc_str.append("\n{}{}".format(" " * cnt, k))
            unwrap_print(v, desc_str, cnt + 2)
        return desc_str

    desc_str[-1] += " - {}\n".format(val[2])
    if len(val) > 3:
        desc_str.append("{}\n{}".format(" " * (cnt + 2),
                                        unwrap_context(val[3], cnt + 4)))
    return desc_str


def unwrap_event_print(val, desc_str=None, cnt=0):

    if desc_str is None:
        desc_str = []

    if isinstance(val, dict):
        for k, v in val.items():
            desc_str.append("\n{}{}".format(" " * cnt, k))
            unwrap_event_print(v, desc_str, cnt + 2)
        return desc_str

    desc_str[-1] += " - {}".format(val[2])

    return desc_str


def validate_context(verb, context, cmd_map, user_model, role_model):

    model = cmd_map.get(verb)
    if model is None:
        raise Exception(f"Verb {verb} not found")

    # if exists context model use it for validation
    if len(model) == 4:
        model = model[3]
    else:
        model = model[1]

    log.debug("context: %s", context)

    if not isinstance(context, list):
        raise Exception("Context must be array of matchTerm(s)")

    for item in context:

        ctx = item.get("matchTerm")

        for obj in [("object", model), ("user", user_model),
                    ("role", role_model)]:

            # check context rules
            for expr in ctx.get(obj[0], {}).get("matchExpressions", []):
                if expr["key"] not in obj[1].keys():
                    raise Exception(
                        "Ivalid context rule key {} for {} verb {}".format(
                            expr["key"], obj[0], verb))

                if expr["operator"] not in CONTEXT_OPERATORS:
                    raise Exception(
                        "Invalid context rule operator {} for {} verb {}".
                        format(expr["operator"], obj[0], verb))


def unwrap_permission(val, cmd_map, desc_str, user_model, role_model):

    if isinstance(val, dict):
        for k, v in val.items():
            unwrap_permission(v, cmd_map.get(k), desc_str, user_model,
                              role_model)
        return desc_str

    if cmd_map is None:
        return []
    # list
    for v in val:
        verb, ctx = v, None

        if isinstance(verb, dict):
            for k, vctx in v.items():
                verb, ctx = k, vctx
                # validate rule if exists
                validate_context(verb, ctx, cmd_map, user_model, role_model)

        data = cmd_map.get(verb)

        if data is None:
            raise Exception(f"Verb {verb} not found")

        perm = {
            "method": data[0][0],
            "path": data[0][1],
            "descr": data[2],
            "prop": ctx
        }

        desc_str.append(perm)

        # check if PLUGIN add PUT cluster permission
        if perm["method"] == "PLUGIN":
            desc_str.append({
                "method": "PUT",
                "path": "/cluster/{cluster}/plugins/{plugin}",
                "descr": "Plugin call",
                "prop": None
            })

    return desc_str


def unwrap_request(val, cmd_map):

    if cmd_map is None:
        raise Exception(f"plugin {val} not found")

    if isinstance(val, dict):
        for k, v in val.items():
            return unwrap_request(v, cmd_map.get(k))
    else:
        if cmd_map is None:
            return None

        data = cmd_map.get(val)
        if data is None:
            raise Exception(f"Verb {val} not found")

        return data


class PermissionLoader():

    def __init__(self):
        self.env = Env().envs

        is_exists, data = open_spec(self.env["MGX_GW_TMP"])

        if is_exists:
            self.api_spec = data
        else:
            self.api_spec = {}

    def unwrap_permission(self, data):
        cmd_map = self.api_spec.get("cmd_map")

        if cmd_map is None:
            raise Exception("Spec not found")

        # get role and user model for validation
        dump_row = [None, None, None, {}]
        user_model = cmd_map.get("aaa", {}).get("user",
                                                {}).get("add", dump_row)[3]
        role_model = cmd_map.get("aaa", {}).get("role",
                                                {}).get("add", dump_row)[3]

        return unwrap_permission(data, cmd_map, [], user_model, role_model)

    def desc_permissions(self, filtr=None):

        cmd_map = self.api_spec.get("cmd_map")

        if cmd_map is None:
            raise Exception("Spec not found")

        if filtr is not None:
            log.debug("load desc with filter %s", filtr)
            cmd_map = cmd_map.get(filtr, {})

        return "".join(unwrap_print(cmd_map, []))

    def desc_events(self, filtr=None):

        cmd_map = self.api_spec.get("cmd_map")

        if cmd_map is None:
            raise Exception("Spec not found")

        if filtr is not None:
            log.debug("load desc with filter %s", filtr)
            cmd_map = cmd_map.get(filtr, {})

        return "".join(unwrap_event_print(cmd_map, []))


def parse_response(text):

    if isinstance(text, dict):

        if text.get("error"):
            return False, text.get("error")

        return True, text.get("data", text)

    return False, text


class PluginYAMLResourceRequest():

    def __init__(self):
        self.env = Env().envs

        is_exists, data = open_spec(self.env["MGX_GW_TMP"])

        if is_exists:
            self.api_spec = data
        else:
            self.api_spec = {}

    def call_plugin(self, ctx, req, cmd_map):

        log.debug("parse request: %s", req)
        cmd_req = req.get("metadata", {}).get("plugin")
        cmd_data = req.get("spec", {})

        if cmd_req is None or cmd_map is None:
            raise Exception("Not found plugin meta")

        log.debug("cmd_req: %s", cmd_req)
        cmd_meta = unwrap_request(cmd_req, cmd_map)
        
        if cmd_meta is None:
            raise Exception("Not found plugin spec")

        pl_request = {}

        for k, v in cmd_meta[1].items():
            if v.get("type") == "jsonstr":
                if cmd_data.get(k) is not None:
                    pl_request[k] = json.dumps(cmd_data.get(k))
            else:
                pl_request[k] = cmd_data.get(k)
        
        log.debug("plugin %s ctx %s parse request: %s", cmd_meta[0], ctx,
                  pl_request)

        status, text = Request(Context("MGX_GW",
                                       **ctx)).call(cmd_meta[0][1], pl_request)

        ok, response = parse_response(text)

        if not ok:
            return {"status": 503, "text": response}

        return {"status": status, "text": response}

    def apply_resource(self, ctx, data):
        cmd_map = self.api_spec.get("cmd_map")

        if cmd_map is None:
            raise Exception("Spec not found")

        log.debug("unwrap_resource:\n %s", data)
        # iterate thru yaml and create request
        results = []
        for req in yaml.safe_load_all(data):
            results.append(self.call_plugin(ctx, req, cmd_map))

        return results
