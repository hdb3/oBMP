# bgppeel.py
#
# peel a single BGP message from the front of a bytearray,
# and return the message and its BGP message type
# returns None if it could not parse it at the basic message level
# the full return value is two byte arrays - the BGP message, the remaining message, and the BGP message type
#

import struct
import sys

BGP_marker = struct.pack('!QQ',0xffffffffffffffff,0xffffffffffffffff)

def peel(msg,strict=True):
    try:

        assert isinstance(msg,bytearray)

        if len(msg) < 18:
            # we could not read enough to parse the header, so return until more data is available
            print("bgppeel.peel short read (%d)" % len(msg), file=sys.stderr)
            return (0,bytearray(),msg)


        ## actual_msg_length = len(msg)

        bgp_length  = struct.unpack_from('!H', msg, offset=16)[0]
        if bgp_length > len(msg):
            ##-## print("bgppeel.peel shortish read (%d/%d)" % (len(msg),bgp_length), file=sys.stderr)
            # we could not read enough to return the entire message, so return until more data is available
            return (0,bytearray(),msg)

        assert msg[0:16] == BGP_marker, "BGP message marker not present"

        bgp_type    = struct.unpack_from('!B', msg, offset=18)[0]
        assert bgp_type > 0 and bgp_type < 5, "Invalid BGP message type %d" % bgp_type

    except AssertionError as ae:
        if strict:
            ##-## print(ae,file=sys.stderr)
            ##-## print(msg.hex(),file=sys.stderr)
            raise ae
        else:
            print("error parsing the message stream - it makes no sense to continue reading the stream any further after this message", ae, file=sys.stderr)
            return None
    else:
        ##-## print("bgppeel.peel - read success %d" % bgp_type,file=sys.stderr)
        ##-## print(msg[:bgp_length].hex(),file=sys.stderr)
        ##-## print(msg[bgp_length:].hex(),file=sys.stderr)
        return (bgp_type,msg[:bgp_length],msg[bgp_length:])
        ## if bgp_length == actual_msg_length:
            ## return (bgp_type,msg,bytearray())
        ## else:
            ## return (bgp_type,msg[:bgp_length],msg[bgp_length:])
