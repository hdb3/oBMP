# bgpparse.py
#
# take a message which is allegedly BGP and parse it into an object wih plausible attributes
#

import struct
import sys
from binascii import hexlify
from ipaddress import ip_address
from pprint import pformat
def eprint(s):
    sys.stderr.write(s+'\n')

BGP_marker = struct.pack('!QQ',0xffffffffffffffff,0xffffffffffffffff)
BGP_OPEN = 1
BGP_UPDATE = 2
BGP_NOTIFICATION = 3
BGP_KEEPALIVE = 4

# for unknown attributes use https://www.iana.org/assignments/bgp-parameters/bgp-parameters.xhtml
# or dump into wireshark!

BGP_TYPE_CODE_ORIGIN = 1
BGP_TYPE_CODE_AS_PATH = 2
BGP_TYPE_CODE_NEXT_HOP = 3
BGP_TYPE_CODE_MULTI_EXIT_DISC = 4
BGP_TYPE_CODE_LOCAL_PREF = 5
BGP_TYPE_CODE_ATOMIC_AGGREGATE = 6
BGP_TYPE_CODE_AGGREGATOR = 7
BGP_TYPE_CODE_COMMUNITIES = 8
BGP_TYPE_CODE_MP_REACH_NLRI = 14
BGP_TYPE_CODE_MP_UNREACH_NLRI = 15
BGP_TYPE_CODE_AS4_PATH = 17
BGP_TYPE_CODE_AS4_AGGREGATOR = 18
BGP_TYPE_CODE_LARGE_COMMUNITY = 32
BGP_Attribute_Flags_Optional = 0x80 # 1 << 7
BGP_Attribute_Flags_Transitive = 0x40 # 1 << 6
BGP_Attribute_Flags_Partial = 0x20 # 1 << 5
BGP_Attribute_Flags_Extended_Length = 0x10 # 1 << 4


class BGP_message:

    def __init__(self,msg):
        self.except_flag = False
        self.unhandled_codes = []
        self.attribute = {}
        msg_len  = len(msg)
        assert msg_len > 18, "BGP message too short %d" % msg_len
        bgp_marker = msg[0:16]
        assert bgp_marker == BGP_marker, "BGP message marker not present"
        self.bgp_length = struct.unpack_from('!H', msg, offset=16)[0]
        assert self.bgp_length > 18 and self.bgp_length <= msg_len, "Invalid BGP message length %d/%d" % (self.bgp_length,msg_len)
        self.bgp_type = struct.unpack_from('!B', msg, offset=18)[0]
        assert self.bgp_type > 0 and self.bgp_type < 5, "Invalid BGP message type %d" % self.bgp_type
        ## eprint( "++ BGP message rcvd length %d type %d" % (self.bgp_length,self.bgp_type))

        if self.bgp_type == BGP_UPDATE:
            self.parse_bgp_update(msg[19:self.bgp_length])
        elif self.bgp_type == BGP_OPEN:
            self.parse_bgp_open(msg[19:self.bgp_length])
        elif self.bgp_type == BGP_NOTIFICATION:
            self.parse_bgp_notification(msg[19:self.bgp_length])

    def __str__(self):
        return str(pformat(vars(self)))

    def parse_bgp_open(self,msg):
        self.bgp_open_version = struct.unpack_from('!B', msg, offset=0)[0]
        self.bgp_open_AS = struct.unpack_from('!H', msg, offset=1)[0]
        self.bgp_open_hold_time = struct.unpack_from('!H', msg, offset=3)[0]
        self.bgp_open_bgp_id = struct.unpack_from('!I', msg, offset=5)[0]
        parameter_length = struct.unpack_from('!B', msg, offset=9)[0]
        self.bgp_open_optional_parameters = self.tlv_parse(msg[10:(9+parameter_length)])
        pass

    def tlv_parsemsg(self):
        pass

    def parse_bgp_update(self,msg):
        lm = len(msg)
        withdrawn_routes_length = struct.unpack_from('!H', msg, offset=0)[0]
        assert lm > withdrawn_routes_length + 3
        self.process_withdrawn_routes(msg[2:2+withdrawn_routes_length])
        path_attribute_length = struct.unpack_from('!H', msg, offset=withdrawn_routes_length+2)[0]
        assert lm > withdrawn_routes_length + 3 + path_attribute_length
        self.process_NLRI(msg[ withdrawn_routes_length + 4 + path_attribute_length:])
        self.process_path_attributes(msg[withdrawn_routes_length + 4 : withdrawn_routes_length + 4 + path_attribute_length])

    def process_withdrawn_routes(self,prefix_list):
        self.withdrawn_prefixes = self.get_prefixes(prefix_list)

    def process_NLRI(self,prefix_list):
        self.prefixes = self.get_prefixes(prefix_list)

    def get_prefixes(self,prefix_list):
    # BGP compresses routes by using the minimum number of bytes needed
    # for the prefix length, i.e. a /24 needs 3 bytes but a /8 needs only 1
    # whether the parser or the application should unpack it is a matter of taste
    # however this library should provide the mechanism in either case.
    # For now, it is done early, whilst parsing....

        prefix_list_length = len(prefix_list)
        offset = 0
        prefixes = []
        while offset < prefix_list_length:
            prefix_length = struct.unpack_from('!B', prefix_list, offset=offset)[0]
            if prefix_length > 24:
                prefix_byte_length = 4
            elif prefix_length > 16:
                prefix_byte_length = 3
            elif prefix_length > 8:
                prefix_byte_length = 2
            elif prefix_length > 0:
                prefix_byte_length = 1
            else:
                prefix_byte_length = 0
            assert prefix_byte_length + offset < prefix_list_length

            prefix = 0
            if prefix_byte_length > 0:
                prefix = struct.unpack_from('!B', prefix_list, offset=offset+1)[0] << 24
            if prefix_byte_length > 1:
                prefix |= struct.unpack_from('!B', prefix_list, offset=offset+2)[0] << 16
            if prefix_byte_length > 2:
                prefix |= struct.unpack_from('!B', prefix_list, offset=offset+3)[0] << 8
            if prefix_byte_length > 3:
                prefix |= struct.unpack_from('!B', prefix_list, offset=offset+4)[0]

            prefixes.append((prefix_length,prefix))
            offset += 1 + prefix_byte_length

        return prefixes


    def process_path_attributes(self,attributes):
        
        offset = 0
        attributes_len = len(attributes)
        attr_count = 0
        while offset < attributes_len:
            attr_flags = struct.unpack_from('!B', attributes, offset=offset)[0]
            attr_type_code = struct.unpack_from('!B', attributes, offset=offset+1)[0]

            extended_length = bool(attr_flags & BGP_Attribute_Flags_Extended_Length)
            if extended_length:
                length = struct.unpack_from('!H', attributes, offset=offset+2)[0]
                quantum = 4
            else:
                length = struct.unpack_from('!B', attributes, offset=offset+2)[0]
                quantum = 3

            attribute = attributes[offset+quantum:offset+length+quantum]

            attr_count += 1
            try:
                self.parse_attribute(attr_flags,attr_type_code,attribute)
            except AssertionError as e:
                self.except_flag = True
                eprint("++failed to parse attribute seq %d at offset %d/length %d, flags:code = (%x,%d) payload %s" \
                        % (attr_count,offset,length,attr_flags,attr_type_code,hexlify(attribute)))
                eprint("++failed to parse attribute : error: %s" % e)
                eprint("++failed to parse attribute : %d %s" % (attributes_len,hexlify(attributes)))
            offset += length+quantum

    def parse_attribute_communities(self,attr,code):

        assert 0 == len(attr) % 4, "BGP community string length not multiple of 4 (%d)" % len(attr)

        community_list = []
        offset = 0
        while offset < len(attr):
            community_list.append(struct.unpack_from('!HH', attr, offset=offset)[0])
            offset += 4

        self.attribute[code] = community_list

    def parse_attribute_large_community(self,attr,code):

        assert 0 == len(attr) % 12, "BGP large community string length not multiple of 12 (%d)" % len(attr)

        community_list = []
        offset = 0
        while offset < len(attr):
            community_list.append(struct.unpack_from('!III', attr, offset=offset)[0])
            offset += 12

        self.attribute[code] = community_list

    def parse_attribute_AS_path(self,attr,as4=False):

    # an AS path attribute has 1 or more AS segments
    # each segment is represented by 1 byte segment type + 1 byte segment length + variable number of AS
    # the 1 byte segment length is a count of AS, not bytes
    # the ASes are 2 or 4 byte values depending on AS/AS4 attribute nature
    #
    # thus the code loops over multiple segments, consuming the attribute payload, only stopping when it runs out of data
    # each segment is processed by an inner loop, loop count based on the number of ASes in the segment AS count header
    #
    # the result is a list of segments, each segment is a tuple (segment type, AS list)
    #

        if as4:
            as_size = 4
            fmt = '!I'
            code = BGP_TYPE_CODE_AS4_PATH
        else:
            as_size = 2
            fmt = '!H'
            code = BGP_TYPE_CODE_AS_PATH

        segment_list = []
        attribute_offset = 0
        attribute_length = len(attr)
        while attribute_offset < attribute_length:
            assert attribute_length - attribute_offset >= 4, \
                    "minimum segment length check length %d offset %d" % (attribute_length,attribute_offset) 

            path_segment_type = struct.unpack_from('!B', attr, offset=attribute_offset)[0]
            assert path_segment_type == 1 or path_segment_type == 2, \
                    "check valid AS segment type (SEQUENCE or SET, 1/2) (%d)" % path_segment_type

            path_segment_length = struct.unpack_from('!B', attr, offset=attribute_offset+1)[0]
            calculated_segment_byte_size = 2 + as_size*path_segment_length
            remaining_bytes_in_segment = attribute_length - attribute_offset
            assert remaining_bytes_in_segment >= calculated_segment_byte_size , \
                    "AS Path attribute length check: remaining_bytes_in_segment >= calculated_segment_byte_size (%d,%d)" % (remaining_bytes_in_segment, calculated_segment_byte_size)

            as_segment = attr[attribute_offset+2:attribute_offset+2+as_size*path_segment_length]
            as_list = []
            for i in range(path_segment_length):
                as_list.append(struct.unpack_from(fmt, as_segment, offset=i*as_size)[0])

            if as_list:
                segment_list.append((path_segment_type,as_list))

            attribute_offset += calculated_segment_byte_size

        if segment_list:
            self.attribute[code] = segment_list

    def parse_attribute_4b_4b(self,code,attr):
            assert len(attr) == 8
            self.attribute[code] = (struct.unpack_from('!I', attr, offset=0)[0],struct.unpack_from('!I', attr, offset=2)[0])

    def parse_attribute_2b_4b(self,code,attr):
            assert len(attr) == 6
            self.attribute[code] = (struct.unpack_from('!H', attr, offset=0)[0],struct.unpack_from('!I', attr, offset=2)[0])

    def parse_attribute_32bits(self,code,attr):
            assert len(attr) == 4
            self.attribute[code] = struct.unpack_from('!I', attr, offset=0)[0]

    def parse_attribute_8bits(self,code,attr):
            assert len(attr) == 1
            self.attribute[code] = struct.unpack_from('!B', attr, offset=0)[0]

    def parse_attribute_0_length(self,code,attr):
        assert len(attr) == 0
        self.attribute[code] = True

    def parse_attribute_unhandled(self,code,attr):
            self.attribute[code] = attr
            self.unhandled_codes.append(code)

    def parse_attribute(self,flags,code,attr):

        if (code==BGP_TYPE_CODE_ORIGIN):
            self.parse_attribute_8bits(code,attr)

        elif (code==BGP_TYPE_CODE_AS_PATH):
            self.parse_attribute_AS_path(attr)

        elif (code==BGP_TYPE_CODE_NEXT_HOP):
            self.parse_attribute_32bits(code,attr)

        elif (code==BGP_TYPE_CODE_MULTI_EXIT_DISC):
            self.parse_attribute_32bits(code,attr)

        elif (code==BGP_TYPE_CODE_LOCAL_PREF):
            self.parse_attribute_32bits(code,attr)

        elif (code==BGP_TYPE_CODE_ATOMIC_AGGREGATE):
            self.parse_attribute_0_length(code,attr)

        elif (code==BGP_TYPE_CODE_AGGREGATOR):
            self.parse_attribute_2b_4b(code,attr)

        elif (code==BGP_TYPE_CODE_COMMUNITIES):
            self.parse_attribute_communities(attr,code)

        elif (code==BGP_TYPE_CODE_AS4_PATH):
            self.parse_attribute_AS_path(attr,as4=True)

        elif (code==BGP_TYPE_CODE_AS4_AGGREGATOR):
            self.parse_attribute_4b_4b(code,attr)

        elif (code==BGP_TYPE_CODE_MP_REACH_NLRI or code == BGP_TYPE_CODE_MP_UNREACH_NLRI):
            self.parse_attribute_unhandled(code,attr)

        elif (code==BGP_TYPE_CODE_LARGE_COMMUNITY):
            self.parse_attribute_large_community(attr,code)

        else:
            assert False , "Unknown BGP path attribuite type %d" % code

    def parse_bgp_notification(self,msg):
        pass
