#
# Store models
#

from mgx_libs.store.models import BaseModel
from cassandra.cqlengine import columns


class Ldaps(BaseModel):
    __table_name__ = "aaa_ldaps"

    name = columns.Text(required=True, primary_key=True)
    url = columns.Text()
    user = columns.Text()
    passwd = columns.Text()
    base_dn = columns.Text()
    query_group = columns.Text()
    query_user = columns.Text()
    query_active_users = columns.Text()
    user_map = columns.Text()
    group_map = columns.Text()
    default_path = columns.Text()


class Params(BaseModel):
    __table_name__ = "aaa_params"

    auth_type = columns.Text(default="BASIC")
    cert = columns.Text(default="")
    ldap = columns.Text()
    ldap_sync = columns.Text(default="no")
    validation_ip = columns.Text(default="no")
    acc_delete_days = columns.Integer(default=45)
    acc_block_unused_days = columns.Integer(default=45)
    acc_block_try_cnt = columns.Integer(default=3)
    acc_block_try_timeout_sec = columns.Integer(default=5 * 60)
    acc_block_try_suspend_sec = columns.Integer(default=60 * 60)
    sessions_max_cnt = columns.Integer(default=2)
    sessions_timeout_sec = columns.Integer(default=3 * 60)
    password_pattern = columns.Text(
        default=
        r"(?=^.{8,}$)(?=.*\d)(?=.*[!@#$%^&*]+)(?![.\n])(?=.*[A-Z])(?=.*[a-z]).*$"
    )
    password_diff_cnt = columns.Integer(default=4)
    password_min_change = columns.Integer(default=2)
    password_min_exp_days = columns.Integer(default=10)
    password_exp_days = columns.Integer(default=60)
    whitelist_networks = columns.List(value_type=columns.Text)
    password_salt = columns.Text(default="")
    tfa_client = columns.Text(default="EMAIL")
    tfa_wait_sec = columns.Integer(default=60)
    notif_route = columns.Text()
    ns_owner_access = columns.Text(default="yes")


class Namespaces(BaseModel):
    __table_name__ = "aaa_namespaces"

    cluster = columns.Text(required=True, primary_key=True)
    ns = columns.Text(required=True, primary_key=True)
    paths = columns.Text()
    descr = columns.Text()


class UserSessions(BaseModel):
    __table_name__ = "aaa_user_sessions"

    uuid = columns.Text(required=True, primary_key=True)
    login = columns.Text()
    cluster_to = columns.Text()
    ns_to = columns.Text()
    date_create = columns.DateTime()
    date_update = columns.DateTime()
    prop = columns.Text()


class Roles(BaseModel):
    __table_name__ = "aaa_roles"

    role = columns.Text(required=True, primary_key=True)
    type = columns.Text(required=True, primary_key=True, default="USER_ROLE")
    descr = columns.Text()
    perm_groups = columns.List(value_type=columns.Text)
    prop = columns.Text()


class Users(BaseModel):
    __table_name__ = "aaa_users"

    login = columns.Text(required=True, primary_key=True)
    path = columns.Text(default="/")
    email = columns.Text()
    whitelist_networks = columns.List(value_type=columns.Text)
    source = columns.Text(default="LOCAL")
    descr = columns.Text()
    passwd = columns.Text()
    passwd_old = columns.List(value_type=columns.Text)
    tried = columns.List(value_type=columns.Text)
    roles = columns.List(value_type=columns.Text)
    date_create = columns.DateTime()
    date_login = columns.DateTime()
    date_passwd = columns.DateTime()
    date_delete = columns.DateTime()
    status = columns.Text()
    code = columns.Text()
    otp_code = columns.Text()
    prop = columns.Text()


class ClusterPermissions(BaseModel):
    __table_name__ = "aaa_cluster_permissions"

    method = columns.Text(required=True, primary_key=True)
    path = columns.Text(required=True, primary_key=True)
    role = columns.Text(required=True, primary_key=True)
    prop = columns.Text()
    descr = columns.Text()


class PluginPermissions(BaseModel):
    __table_name__ = "aaa_plugin_permissions"

    plugin = columns.Text(required=True, primary_key=True)
    op = columns.Text(required=True, primary_key=True)
    role = columns.Text(required=True, primary_key=True)
    prop = columns.Text()
    descr = columns.Text()
