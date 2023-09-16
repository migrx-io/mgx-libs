#
# Store models
#

from mgx_libs.store.models import BaseModel
from cassandra.cqlengine import columns


class Messages(BaseModel):
    __table_name__ = "notif_messages"

    date_create = columns.DateTime(required=True, primary_key=True)
    uuid = columns.Text(required=True, primary_key=True)
    data = columns.Text()
    date_sent = columns.DateTime()
    error = columns.Text()


class Endpoints(BaseModel):
    __table_name__ = "notif_endpoints"

    name = columns.Text(required=True, primary_key=True)
    type = columns.Text(default="SMTP")
    url = columns.Text()
    tls = columns.Text(default="no")
    user = columns.Text()
    passwd = columns.Text()
    descr = columns.Text()


class Mailings(BaseModel):
    __table_name__ = "notif_mailings"

    name = columns.Text(required=True, primary_key=True)
    addresses = columns.Set(value_type=columns.Text)
    descr = columns.Text()


class Templates(BaseModel):
    __table_name__ = "notif_templates"

    name = columns.Text(required=True, primary_key=True)
    data = columns.Text()
    descr = columns.Text()


class Routes(BaseModel):
    __table_name__ = "notif_routes"

    name = columns.Text(required=True, primary_key=True)
    endpoint = columns.Text()
    mailing = columns.Text()
    sender = columns.Text()
    subject = columns.Text()
    template = columns.Text()
    descr = columns.Text()
