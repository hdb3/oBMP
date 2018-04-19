# bgpupdate.py
#
# parse and build a representation of a BGP UPDATE message
# the exposed methods are parse, deparse and new
# parse and new create new message objects
# deparse takes an object and creates a corresponding wire-format message
#

import struct
from ipaddress import IPv4Address

class BGP_UPDATE_message:

    @classmethod
    def parse(cls,msg):
        self = cls()
        return self

    def deparse(self):
        msg = bytearray()
        return msg

    @classmethod
    def new(cls,AS,hold_time,bgp_id,capabilities):
        self = cls()

        return self
