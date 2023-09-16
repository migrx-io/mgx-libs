#
# Password helpers
#

import base64


class Base64Passwd():

    def __init__(self):
        pass

    def encode(self, passwd):
        return base64.b64encode(passwd.encode("utf-8")).decode("utf-8")

    def decode(self, passwd):
        return base64.b64decode(passwd).decode("utf-8")
