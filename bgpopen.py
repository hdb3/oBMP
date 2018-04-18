# bgpopen.py
#
# parse and build a representation of a BGP OPEN message
#

import struct
import sys
from binascii import hexlify
from ipaddress import IPv4Address
#from pprint import pformat
#import traceback
import bgpmsg
import capabilitycodes
from capability import Capability
#from capability import Capability

# see https://www.iana.org/assignments/capability-codes/capability-codes.xml
# for capability list coding
#

class BGP_OPEN_message:
#class BGP_OPEN_message(BGP_message):


    ## TODO
    #
    # the dtat straucture naming confuses parameters and capabilities
    # BGP OPEN can carry different parameters other than capabilities
    # however in practice only capabilities are sent in normal OPEN messages
    #
    # the datastructure should use the name capability rather than parameter
    # the datastructure does not and need not make cpabilities a member of a parameter hierarchy family, though for purity it could
    #

    @staticmethod
    def inner_tlv_parse(msg):
        c_type   = struct.unpack_from('!B', msg, offset=0)[0]
        c_length = struct.unpack_from('!B', msg, offset=1)[0]
        assert len(msg) == c_length + 2, "sanity check, comparing %d >= %d" % (len(msg), c_length + 2)
        c_value = msg[2:]
        return (c_type,c_value)

    @staticmethod
    def tlv_parse(msg):
        optional_parameters = {}
        while 2 < len(msg):
            p_type   = struct.unpack_from('!B', msg, offset=0)[0]
            p_length = struct.unpack_from('!B', msg, offset=1)[0]
            assert p_type == 2
            assert len(msg) >= p_length + 2, "sanity check, comparing %d >= %d" % (len(msg), p_length + 2)
            p_value = msg[2:2+p_length]
            msg = msg[2+p_length:]
            #c_type,c_value = BGP_message.inner_tlv_parse(p_value)
            c_type,c_value = Capability.decode_cap(p_value)
            optional_parameters[c_type] = c_value
        return optional_parameters


    def __init__(self):
        pass

    def __str__(self):
        from pprint import pformat
        return str(pformat(vars(self)))

    @classmethod
    def parse(cls,msg):
        self = cls()
        # self.version = struct.unpack_from('!B', msg, offset=0)[0]
        assert 4 == struct.unpack_from('!B', msg, offset=0)[0] # BGP IS version 4
        self.AS = struct.unpack_from('!H', msg, offset=1)[0]
        self.hold_time = struct.unpack_from('!H', msg, offset=3)[0]
        self.bgp_id = IPv4Address(struct.unpack_from('!I', msg, offset=5)[0])
        parameter_length = struct.unpack_from('!B', msg, offset=9)[0]
        self.optional_parameters = self.tlv_parse(msg[10:10+parameter_length])

    #@staticmethod
    #def deparse_capabilities(optional_parameters):
        #msg = bytearray()
        #for ( c_type,c_value ) in optional_parameters.items():
            #c_length = len(c_value)
            #msg.extend( struct.pack('!B', c_type))
            #msg.extend( struct.pack('!B', c_length))
            #msg.extend( c_value )
        #return msg

    @staticmethod
    def deparse_parameters(optional_parameters):

        p_type = 2
        msg = bytearray()
        for parameter in optional_parameters:

            p_value  = Capability.cap(parameter)
            p_length = len(p_value)
            msg.extend( struct.pack('!B', p_type))
            msg.extend( struct.pack('!B', p_length))
            msg.extend( p_value )

        return msg


    def deparse(self):
        msg = bytearray()
        msg.extend( struct.pack('!B', 4))
        msg.extend( struct.pack('!H', self.AS))
        msg.extend( struct.pack('!H', self.hold_time))
        msg.extend( self.bgp_id.packed)
        #msg.extend( struct.pack('!I', self.bgp_id))

        optional_parameters = self.deparse_parameters(self.optional_parameters)
        parameter_length = len(optional_parameters)

        msg.extend( struct.pack('!B', parameter_length))
        msg.extend( optional_parameters )

        return msg

    @classmethod
    def new(cls,AS,hold_time,bgp_id,capabilities):
        self = cls()
        self.AS = AS
        self.hold_time = hold_time
        self.bgp_id = bgp_id
        self.optional_parameters = capabilities
        return self
