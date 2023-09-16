#
# Store models
#

from mgx_libs.store.models import BaseModel
from cassandra.cqlengine import columns


class Systemds(BaseModel):
    __table_name__ = "services_systemd"

    name = columns.Text(required=True, primary_key=True)
    code = columns.Text()
    state = columns.Text()
    descr = columns.Text()
