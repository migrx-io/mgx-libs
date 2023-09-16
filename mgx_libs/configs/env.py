import os
import random
import string


class Env:

    def __init__(self):
        self.envs = {}
        self.is_rpm = self.is_centos()
        self.read()

    def is_centos(self):
        with open("/etc/os-release", encoding="utf-8") as f:
            dist = f.read().lower()
            if dist.find("centos") >= 0:
                return True
            return False

    def iif(self, rpm, deb):
        if self.is_rpm:
            return rpm
        return deb

    def read(self):

        # common
        self.envs["LOGLEVEL"] = os.environ.get("LOGLEVEL", "INFO")
        self.envs["NODE_NAME"] = os.environ.get("NODE_NAME")

        # Plugin test env
        self.envs["ASYNC_DISABLE"] = os.environ.get("ASYNC_DISABLE", "n")

        # Core parameter

        self.envs["MGX_IS_MCAST"] = os.environ.get("MGX_IS_MCAST")
        self.envs["MGX_IFACE"] = os.environ.get("MGX_IFACE")
        self.envs["MGX_VIP_STRGY"] = os.environ.get("MGX_VIP_STRGY")
        self.envs["MGX_IS_SCHEDULER_CHECK"] = os.environ.get(
            "MGX_IS_SCHEDULER_CHECK")

        self.envs["MGX_HOST"] = "localhost"
        self.envs["MGX_PORT"] = int(os.environ.get("MGX_PORT", "8081"))
        self.envs["MGX_IS_TLS"] = os.environ.get("MGX_IS_TLS", "n")
        self.envs["MGX_TLS_VERIFY"] = os.environ.get("MGX_TLS_VERIFY", "n")
        self.envs["MGX_HTTP_TIMEOUT"] = int(
            os.environ.get("MGX_HTTP_TIMEOUT", "30"))
        self.envs["MGX_X_API_KEY"] = os.environ.get("MGX_X_API_KEY", "")

        self.envs["MGX_DB_NAME"] = os.environ.get(
            "MGX_DB_NAME", "/var/lib/migrx/db/node_collector.db")
        self.envs["MGX_FLOWS_DIR"] = os.environ.get("MGX_FLOWS_DIR",
                                                    "/var/lib/migrx/flows")
        self.envs["MGX_LOGS_DIR"] = os.environ.get("MGX_LOGS_DIR",
                                                   "/var/lib/migrx/logs")
        self.envs["MGX_REPO"] = os.environ.get("MGX_REPO", "mgx-main")

        self.envs["MGX_CASS_CREDS"] = os.environ.get("MGX_CASS_CREDS")
        self.envs["MGX_DC_NAME"] = os.environ.get("MGX_DC_NAME")

        self.envs["MGX_RPM_VER"] = self.iif(
            "rpm -qa|grep \"^mgx-\"|sort|sha1sum",
            "apt list 2> /dev/null|grep \"^mgx-\"|sort|sha1sum")

        self.envs["MGX_MOD_VER"] = self.iif(
            "rpm -qa|grep \"^{}\"|sort|sha1sum",
            "apt list 2> /dev/null|grep \"^{}\"|sort|sha1sum")

        self.envs["MGX_SPEC_VER"] = os.environ.get(
            "MGX_SPEC_VER", "cat {}/* 2> /dev/null| sort|sha1sum".format(
                self.envs["MGX_FLOWS_DIR"]))

        self.envs["MGX_RPM_REPO"] = self.iif(
            "yum search --disablerepo '*' --enablerepo='{}' mgx-plgn".format(
                self.envs["MGX_REPO"]),
            "sudo apt update -o Dir::Etc::sourcelist=\"sources.list.d/{}.list\" > /dev/null 2>&1"
            " && apt list 2> /dev/null|grep \"^mgx-plgn\"|awk '{{print $1 \" \" $2\". \"}}'"
            .format(self.envs["MGX_REPO"]))

        self.envs["MGX_RPM_INSTALLED"] = self.iif(
            "rpm -qa|grep \"^mgx-plgn\"",
            "apt list --installed 2> /dev/null|grep \"^mgx-plgn\"|awk '{{print $1 \" \" $2\". \"}}'"
        )

        self.envs["MGX_RPM_INSTALL_CMD"] = self.iif(
            "sudo yum install -y {} > /dev/null && echo \"ok\"",
            "sudo apt update 1> /dev/null 2> /dev/null \
                && sudo apt install -y {} > /dev/null 2>&1 && echo \"ok\"",
        )

        self.envs["MGX_RPM_REMOVE_CMD"] = self.iif(
            "sudo yum erase -y {} > /dev/null && echo \"ok\"",
            "sudo apt remove -y {} > /dev/null 2>&1 && echo \"ok\"")

        self.envs["MGX_SRV_STATUS"] = os.environ.get(
            "MGX_SRV_STATUS", "systemctl status {}|grep 'Active:'")

        self.envs["MGX_SRV_START"] = os.environ.get(
            "MGX_SRV_START", "sudo systemctl start {} && echo \"ok\"")

        self.envs["MGX_SRV_STOP"] = os.environ.get(
            "MGX_SRV_STOP", "sudo systemctl stop {} && echo \"ok\"")

        self.envs["MGX_PLUGIN_SPEC"] = os.environ.get(
            "MGX_PLUGIN_SPEC", "/opt/mgx-plgn-{}/actor.yaml")

        # GW parameters

        self.envs["MGX_GW_HOST"] = "localhost"
        self.envs["MGX_GW_PORT"] = int(os.environ.get("MGX_GW_PORT", "8082"))
        self.envs["MGX_GW_IS_TLS"] = os.environ.get("MGX_GW_IS_TLS", "n")
        self.envs["MGX_GW_TLS_VERIFY"] = os.environ.get(
            "MGX_GW_TLS_VERIFY", "n")
        self.envs["MGX_GW_HTTP_TIMEOUT"] = int(
            os.environ.get("MGX_GW_HTTP_TIMEOUT", "30"))
        self.envs["MGX_GW_X_API_KEY"] = os.environ.get("MGX_GW_X_API_KEY", "")

        self.envs["MGX_GW_JWT_EXP"] = int(
            os.environ.get("MGX_GW_JWT_EXP", "31536000"))
        self.envs["MGX_GW_JWT_SECRET_KEY"] = "".join(
            random.choices(string.ascii_lowercase + string.digits, k=20))
        self.envs["MGX_GW_JWT_HEADER"] = os.environ.get(
            "MGX_GW_JWT_HEADER", "JWT")

        self.envs["MGX_GW_ADMIN_PASSWD"] = os.environ.get(
            "MGX_GW_ADMIN_PASSWD", "admin123")
        self.envs["MGX_GW_ADMIN_DISABLE"] = os.environ.get(
            "MGX_GW_ADMIN_DISABLE", "n")

        self.envs["MGX_GW_PWORKERS"] = int(
            os.environ.get("MGX_GW_PWORKERS", "1"))
        self.envs["MGX_GW_TMP"] = os.environ.get("MGX_GW_TMP",
                                                 "/tmp/apispec.json")

        self.envs["MGX_GW_PWORKERS_SLEEP"] = int(
            os.environ.get("MGX_GW_PWORKERS_SLEEP", "20"))


envs = Env().envs
