import logging as log

import pkgutil
import mgx_libs.store as stores
from importlib import import_module
import inspect

NAMESPACESKIP = [
    "Namespaces", "ClusterPermissions", "PluginPermissions", "UserSessions",
    "Params"
]


def clear_ns_objects(ctx):

    for classz in NAMESPACESKIP[1:]:
        log.debug("start delete all from ns: %s", classz)
        del_objects(ctx, "aaa", classz)


def is_namespace_not_empty(ctx, module=None, classz=None):

    if module is None:
        mods = get_models()
    else:
        mods = [module]

    exists, err = False, None

    for mod in mods:
        exists, err = get_objects(ctx, mod, classz)

        if exists:
            break

    return exists, err


def get_models():

    log.info("load modules")

    models = []

    for _, modname, _ in pkgutil.iter_modules(stores.__path__):

        if modname in ["connection", "models", "aaaevents"]:
            continue

        log.debug("import module %s", modname)

        models.append(modname)

    return models


def del_objects(ctx, modname, classz):

    log.debug("import module %s", modname)
    log.debug("import ctx %s", ctx)

    mod = import_module(f"mgx_libs.store.{modname}")

    for name, obj in inspect.getmembers(mod):
        if inspect.isclass(obj):
            # initiate class

            if classz != name:
                continue

            log.info("class %s", obj)

            objz = obj.objects.filter(
                **{
                    "ctx_cluster": ctx.get("ctx_cluster", ctx.get("cluster")),
                    "ctx_ns": ctx.get("ctx_ns", ctx.get("ns"))
                })
            objz.delete()


def get_objects(ctx, modname, classz):

    # if modname is None return
    if modname is None:
        return False, None

    log.debug("import module %s", modname)

    mod = import_module(f"mgx_libs.store.{modname}")

    for name, obj in inspect.getmembers(mod):
        if inspect.isclass(obj):
            # initiate class
            if name == "BaseModel" or \
                    (modname == "aaa" and name in NAMESPACESKIP):
                continue

            if classz is not None and classz != name:
                continue

            log.info("class %s %s", obj, name)

            instances = obj.ctx(**ctx).filter(**{})

            log.debug("instances: %s", instances)

            if len(instances) > 0:
                return True, "Found objects {} {} in namespace".format(
                    modname, name)

    return False, None
