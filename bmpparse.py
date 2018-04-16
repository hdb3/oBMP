# bmpparse.py
#
# take a message which is allegedly BMP and parse it into an object wih plausible attributes
#

import struct
import sys
import os
import time
import bgppeel
def eprint(s):
    sys.stderr.write(s+'\n')
    sys.stderr.flush()


BMP_Route_Monitoring = 0
BMP_Statistics_Report = 1
BMP_Peer_Down_Notification = 2
BMP_Peer_Up_Notification = 3
BMP_Initiation_Message = 4
BMP_Termination_Message = 5
BMP_Route_Mirroring_Message = 6

BMP_Init_type_sysDescr = 1
BMP_Init_type_sysName = 2
BMP_Term_type_reason = 1
BMP_Term_type_string = 0


def _get_tlv(msg):
    assert len(msg)>= 4
    t = struct.unpack_from('!H', msg, offset=0)[0]
    l = struct.unpack_from('!H', msg, offset=2)[0]
    assert len(msg) >= l + 4
    v = msg[4:4+l]
    return (t,l,v)

def _get_tlvs(msg):
    tlvs = []
    while 0 < len(msg):
        t,l,v = _get_tlv(msg)
        tlvs.append((t,l,v))
        msg = msg[4+l:]
        tlv_dict = {}
        for (t,l,v) in tlvs:
            tlv_dict[t] = v
    return tlv_dict

class BMP_message:

    def __str__(self):
        from pprint import pformat
        return str(pformat(vars(self)))

    def __init__(self,msg):

        def parse_route_monitoring(msg):
            self.bmp_RM_bgp_message = msg

        def parse_statistics(msg):
            stats_count = struct.unpack_from('!I', msg, offset=0)[0]
            tlvs = _get_tlvs(msg[4:])
            assert stats_count == len(tlvs)
            self.bmp_stats = {}
            for sr in tlvs.items():
                sr_type = sr[0]
                sr_val  = sr[1]
                if 4 == len(sr_val):
                    self.bmp_stats[sr_type] = struct.unpack_from('!I', sr_val, offset=0)[0]
                elif 8 == len(sr_val):
                    self.bmp_stats[sr_type] = struct.unpack_from('!L', sr_val, offset=0)[0]
                else:
                    assert False, "len(sr) = %d" % len(sr_val)

        def parse_peer_down(msg):
            reason = struct.unpack_from('!B', msg, offset=0)[0]
            if 1 == len(msg):
                self.bmp_peer_down = (reason,bytearray())
            else:
                self.bmp_peer_down = (reason,msg[1:])

        def parse_peer_up(msg):
            self.bmp_peer_up_local_address  = struct.unpack_from('!I', msg, offset=12)[0]
            self.bmp_peer_up_local_port     = struct.unpack_from('!H', msg, offset=16)[0]
            self.bmp_peer_up_remote_port    = struct.unpack_from('!H', msg, offset=18)[0]
            sent_msg_type,self.bmp_peer_up_sent_open,tail = bgppeel.peel(msg[20:])
            assert sent_msg_type == 1 # BGP OPEN type code
            rcvd_msg_type,self.bmp_peer_up_rcvd_open,tail = bgppeel.peel(tail)
            assert rcvd_msg_type == 1 # BGP OPEN type code
            if 0 < len(tail):
                tlvs = _get_tlvs(tail)
                self.bmp_peer_up_information = tlvs

        def parse_initiation(msg):
            tlvs = _get_tlvs(msg)
            assert len(tlvs) > 1
            assert BMP_Init_type_sysDescr in tlvs
            assert BMP_Init_type_sysName in tlvs
            self.bmp_init_tlvs = tlvs

        def parse_termination(msg):
            tlvs = _get_tlvs(msg)
            assert len(tlvs) > 0
            assert BMP_Term_type_reason in tlvs
            eprint("reason: %d" % tlvs[BMP_Term_type_reason].decode('ascii'))
            if BMP_Term_type_string in tlvs:
                eprint("string: %s" % tlvs[BMP_Term_type_string].decode('ascii'))
            self.bmp_term_tlvs = tlvs

        def parse_route_mirroring(msg):
            assert False, "parse_route_mirroring NOT IMPLEMENTED"

        # save the original binary message for diagnostics later
        self.msg = msg
        # parse the common header (CH)
        self.version  = struct.unpack_from('!B', msg, offset=0)[0]
        assert 3 == self.version
        self.length   = struct.unpack_from('!I', msg, offset=1)[0]
        self.msg_type = struct.unpack_from('!B', msg, offset=5)[0]
        msg_len  = len(msg)
        assert msg_len == self.length
        assert self.msg_type <= BMP_Route_Mirroring_Message, "msg_type out of range %d" % self.msg_type

        if (self.msg_type == BMP_Initiation_Message or self.msg_type == BMP_Termination_Message):
            pass # there is no PPC header in these messages
        else:
            assert msg_len > 47
            self.bmp_ppc_fixed_hash = hash(str(msg[6:40]))
            self.bmp_ppc_Peer_Type = struct.unpack_from('!B', msg, offset=6)[0]               # 1 byte index 6
            self.bmp_ppc_Peer_Flags = struct.unpack_from('!B', msg, offset=7)[0]              # 1 byte index 7
            self.bmp_ppc_Peer_Distinguisher  = struct.unpack_from('!Q', msg, offset=8)[0]     # 8 bytes index 8
            # 16 byte field to accomodate IPv6, however I assume IPv4 here!
            self.bmp_ppc_IP6_Peer_Address = struct.unpack_from('!QQ', msg, offset=16)[0]           # 16 bytes index 16
            self.bmp_ppc_IP4_Peer_Address = struct.unpack_from('!I', msg, offset=28)[0]           # 16 bytes index 16
            self.bmp_ppc_Peer_AS = struct.unpack_from('!I', msg, offset=32)[0]                # 4 bytes index 32
            self.bmp_ppc_Peer_BGPID = struct.unpack_from('!I', msg, offset=36)[0]             # 4 bytes index 36
            self.bmp_ppc_Timestamp_Seconds = struct.unpack_from('!I', msg, offset=40)[0]      # 4 bytes index 40
            self.bmp_ppc_Timestamp_Microseconds = struct.unpack_from('!I', msg, offset=44)[0] # 4 bytes index 44


        if (self.msg_type == BMP_Route_Monitoring):
            parse_route_monitoring(msg[48:])
        elif (self.msg_type == BMP_Statistics_Report):
            parse_statistics(msg[48:])
        elif (self.msg_type == BMP_Peer_Down_Notification):
            parse_peer_down(msg[48:])
        elif (self.msg_type == BMP_Peer_Up_Notification):
            parse_peer_up(msg[48:])
        elif (self.msg_type == BMP_Initiation_Message):
            parse_initiation(msg[6:])
        elif (self.msg_type == BMP_Termination_Message):
            parse_termination(msg[6:])
        elif (self.msg_type == BMP_Route_Mirroring_Message):
            parse_route_mirroring(msg[48:])

            
    @classmethod
    def get_next_parsed(cls,msg):
        msg,bmp_msg = cls.get_next(msg)
        return (msg,BMP_message(bmp_msg))

    @classmethod
    def get_next(cls,msg):
        if len(msg) < 6:
            return (msg,bytearray())
        version  = struct.unpack_from('!B', msg, offset=0)[0]
        length   = struct.unpack_from('!I', msg, offset=1)[0]
        msg_type = struct.unpack_from('!B', msg, offset=5)[0]
        assert 3 == version, "failed version check, expected 3 got %x offset %d+%d" % (version,self.bytes_processed,offset)
        assert msg_type < 7, "failed message type check, expected < 7, got %x" % msg_type
        if len(msg) < length:
            return (msg,bytearray())
        else:
            return (msg[length:],msg[:length])
