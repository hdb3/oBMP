# bgppeel.py
#
# peel a single BGP message from the front of a bytearray,
# and return the message and its BGP message type
# returns None if it could not parse it at the basic message level
# the full return value is two byte arrays - the BGP message, the remaining message, and the BGP message type
#

import struct

BGP_marker = struct.pack('!QQ',0xffffffffffffffff,0xffffffffffffffff)

def peel(msg,strict=True):
    try:

        assert isinstance(msg,bytearray)

        actual_msg_length = len(msg)
        assert actual_msg_length > 18, "BGP message too short %d" % actual_msg_length

        bgp_length  = struct.unpack_from('!H', msg, offset=16)[0]
        bgp_type    = struct.unpack_from('!B', msg, offset=18)[0]
        bgp_version = struct.unpack_from('!B', msg, offset=19)[0]

        assert msg[0:16] == BGP_marker, "BGP message marker not present"
        assert 4 == bgp_version, "BGP version check failed (%d" % bgp_version
        assert bgp_type > 0 and bgp_type < 5, "Invalid BGP message type %d" % bgp_type
        assert bgp_length > 18 and bgp_length <= actual_msg_length, "Invalid BGP message length %d/%d" % (bgp_length,actual_msg_length)

    except AssertionError as ae:
        if strict:
            raise ae
        else:
            return None
    else:
        if bgp_length == actual_msg_length:
            return (bgp_type,msg,bytearray())
        else:
            return (bgp_type,msg[:bgp_length],msg[bgp_length:])
