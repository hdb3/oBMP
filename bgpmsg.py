# bgpparse.py
#
# take a message which is allegedly BGP and parse it into an object wih plausible attributes
#

from struct import pack, unpack_from
import sys
#from ipaddress import IPv4Address
#from pprint import pformat
import traceback
from bgpupdate import BGP_UPDATE_message
from bgpopen import BGP_OPEN_message
from bgpnotification import BGP_NOTIFICATION_message

BGP_marker = pack('!QQ',0xffffffffffffffff,0xffffffffffffffff)
BGP_OPEN = 1
BGP_UPDATE = 2
BGP_NOTIFICATION = 3
BGP_KEEPALIVE = 4

class BGP_message:

    def __str__(self):
        from pprint import pformat
        return str(pformat(vars(self)))

    def __init__(self,msg):
        assert isinstance(msg,bytearray)
        self.except_flag = False
        msg_len  = len(msg)
        assert msg_len > 18, "BGP message too short %d" % msg_len
        bgp_marker = msg[0:16]
        assert bgp_marker == BGP_marker, "BGP message marker not present"
        bgp_length = unpack_from('!H', msg, offset=16)[0]
        assert bgp_length > 18 and bgp_length <= msg_len, "Invalid BGP message length %d/%d" % (bgp_length,msg_len)
        self.bgp_type = unpack_from('!B', msg, offset=18)[0]
        assert self.bgp_type > 0 and self.bgp_type < 5, "Invalid BGP message type %d" % self.bgp_type
        self.payload = msg[19:bgp_length]

    def parse(self):
        if self.bgp_type == BGP_UPDATE:
            # note - parsing an UPDATE may take an indication of the AS4 nature which cannot be known 
            # via this interface.
            return BGP_UPDATE_message.parse(self.payload)
        elif self.bgp_type == BGP_OPEN:
            return BGP_OPEN_message.parse(self.payload)
        elif self.bgp_type == BGP_NOTIFICATION:
            return BGP_NOTIFICATION_message.parse(self.payload)
        else:
            # KEEPALIVE has no payload
            return None

    @staticmethod
    def deparse(msg):
        if isinstance(msg,BGP_OPEN_message):
            msg_type = BGP_OPEN
            payload = BGP_OPEN_message.deparse(msg)
        elif isinstance(msg,BGP_UPDATE_message):
            msg_type = BGP_UPDATE
            payload = BGP_UPDATE_message.deparse(msg)
        elif isinstance(msg,BGP_NOTIFICATION_message):
            msg_type = BGP_NOTIFICATION
            payload = BGP_NOTIFICATION_message.deparse(msg)
        else:
            msg_type = BGP_KEEPALIVE
            payload = bytearray()
            
        raw_msg = bytearray()
        raw_msg.extend(BGP_marker)
        raw_msg.extend(pack('!H',19+len(payload)))
        raw_msg.extend(pack('!B',msg_type))
        raw_msg.extend(payload)
        return raw_msg
