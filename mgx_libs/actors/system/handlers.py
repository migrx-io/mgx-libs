import logging as log
from mgx_libs.types.validation import open_spec


class PluginSpec():

    def __init__(self, plugin_spec=None):

        if plugin_spec is None:
            self.plugin_spec = "/opt/{}/actor.yaml"
        else:
            self.plugin_spec = plugin_spec

    def get(self, spec):

        meta = {}
        is_exists, data = open_spec(self.plugin_spec.format(spec))
        if is_exists:
            meta = data
            log.debug("meta: %s", meta)

        return meta


class Meta:

    def __init__(self, state):
        self.state = state

    def get_actor_meta(self, msg):

        log.debug("get context %s", msg['context'])
        ctx = msg["context"]

        pl_spec = PluginSpec(ctx.get("plugin_spec")).get(
            ctx.get("plugin_name"))

        log.debug("plugin spec %s", pl_spec)

        return pl_spec
