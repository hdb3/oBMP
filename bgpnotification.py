# bgpnotification.py
#
# parse and build a representation of a BGP NOTIFICATION message
#

class BGP_NOTIFICATION_message:

    def __init__(self):
        pass

    @classmethod
    def parse(cls,msg):
        self = cls()
        return self

    def deparse(self):
        msg = bytearray()
        return msg

    @classmethod
    def new():
        self = cls()
        return self
