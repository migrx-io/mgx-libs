from mgx_libs.configs.env import Env
import json
import glob
import os


class Flow:

    def __init__(self):
        self.envs = Env().envs

    def list(self):

        flows_list = glob.glob("{}/*.json".format(self.envs["MGX_FLOWS_DIR"]))

        data = []
        for i in flows_list:
            with open(i, encoding="utf-8") as f:
                flow = json.loads(f.read())
                data.append(flow["name"])

        return data

    def desc(self, name):

        flow_file = "{}/{}.json".format(self.envs["MGX_FLOWS_DIR"], name)

        if not os.path.exists(flow_file):
            raise Exception("Flow {} not found".format(name))

        return flow_file

    def get(self, name):

        with open(self.desc(name), encoding="utf-8") as f:

            flow = json.loads(f.read())

            return {
                "name": flow["name"],
                "active": flow["active"],
                "priority": flow["priority"]
            }

    def set_status(self, name, status):

        with open(self.desc(name), "r+", encoding="utf-8") as f:
            data = json.loads(f.read())
            data["active"] = status
            f.seek(0)
            f.truncate()
            f.write(json.dumps(data, sort_keys=True, indent=4))

    def stop(self, name):
        self.set_status(name, 0)

    def start(self, name):
        self.set_status(name, 1)
