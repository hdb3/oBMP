# bgpparse.py
#
# take a message which is allegedly BGP and parse it into an object wih plausible attributes
#

import struct
import sys
from binascii import hexlify
from ipaddress import ip_address
#from pprint import pformat
import traceback

def eprint(s):
    sys.stderr.write(s+'\n')
    sys.stderr.flush()

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
BGP_TYPE_CODE_EXTENDED_COMMUNITIES = 16
BGP_TYPE_CODE_AS4_PATH = 17
BGP_TYPE_CODE_AS4_AGGREGATOR = 18
BGP_TYPE_CODE_CONNECTOR = 20
BGP_TYPE_CODE_AS_PATHLIMIT = 21
BGP_TYPE_CODE_LARGE_COMMUNITY = 32
BGP_TYPE_CODE_ATTR_SET = 128
BGP_Attribute_Flags_Optional = 0x80 # 1 << 7
BGP_Attribute_Flags_Transitive = 0x40 # 1 << 6
BGP_Attribute_Flags_Partial = 0x20 # 1 << 5
BGP_Attribute_Flags_Extended_Length = 0x10 # 1 << 4


class BGP_message:

    def __str__(self):
        from pprint import pformat
        return str(pformat(vars(self)))

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

        if self.bgp_type == BGP_UPDATE:
            self.parse_bgp_update(msg[19:self.bgp_length])
        elif self.bgp_type == BGP_OPEN:
            self.parse_bgp_open(msg[19:self.bgp_length])
        elif self.bgp_type == BGP_NOTIFICATION:
            self.parse_bgp_notification(msg[19:self.bgp_length])

    def __str__(self):
        from pprint import pformat
        return str(pformat(vars(self)))


    @staticmethod
    def deparse(msg_type,msg):
        assert msg_type > 0 and msg_type < 5, "Invalid BGP message type %d" % msg_type
        raw_msg = bytearray()
        raw_msg.extend(BGP_marker)
        raw_msg.extend(struct.pack('!H',len(msg)))
        raw_msg.extend(struct.pack('!B',msg_type))
        raw_msg.extend(msg)
        return raw_msg


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
            c_type,c_value = BGP_message.inner_tlv_parse(p_value)
            optional_parameters[c_type] = c_value
        return optional_parameters

    def parse_bgp_open(self,msg):
        self.bgp_open_version = struct.unpack_from('!B', msg, offset=0)[0]
        self.bgp_open_AS = struct.unpack_from('!H', msg, offset=1)[0]
        self.bgp_open_hold_time = struct.unpack_from('!H', msg, offset=3)[0]
        self.bgp_open_bgp_id = struct.unpack_from('!I', msg, offset=5)[0]
        parameter_length = struct.unpack_from('!B', msg, offset=9)[0]
        self.bgp_open_optional_parameters = self.tlv_parse(msg[10:10+parameter_length])
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
                eprint("++failed to parse attribute  : error: %s" % e)
                eprint("++failed to parse attributes : %d %s" % (attributes_len,hexlify(attributes)))
                traceback.print_tb( sys.exc_info()[2])
                exit()
            offset += length+quantum

        
        if len(self.prefixes) > 0:

            if BGP_TYPE_CODE_ORIGIN not in self.attribute:
                eprint("mandatory attribute BGP_TYPE_CODE_ORIGIN missing")
                self.except_flag = True
            if BGP_TYPE_CODE_AS_PATH not in self.attribute:
                eprint("mandatory attribute BGP_TYPE_CODE_AS_PATH missing")
                self.except_flag = True
            if BGP_TYPE_CODE_NEXT_HOP not in self.attribute:
                eprint("mandatory attribute BGP_TYPE_CODE_NEXT_HOP missing")
                self.except_flag = True
        else:
            assert len(self.prefixes) == 0, "check for processing NLRI before attributes failed"
        

    def parse_attribute_communities(self,code,attr):

        assert 0 == len(attr) % 4, "BGP community string length not multiple of 4 (%d)" % len(attr)

        community_list = []
        offset = 0
        while offset < len(attr):
            community_list.append(struct.unpack_from('!HH', attr, offset=offset)[0])
            offset += 4

        self.attribute[code] = community_list

    def parse_attribute_attribute_set(self,code,attr):

        assert 4 < len(attr), "BGP  attribute set length less than 4 (%d)" % len(attr)

        self.attribute[code] = ((struct.unpack_from('!I', attr, offset=0)[0],attr[4:]))

    def parse_attribute_extended_communities(self,code,attr):

        assert 0 == len(attr) % 8, "BGP extended community string length not multiple of 8 (%d)" % len(attr)

        extended_community_list = []

        for offset in range(0,len(attr),8):
            extended_community_list.append((struct.unpack_from('!H', attr, offset=offset)[0],attr[offset+2:offset+8]))

        self.attribute[code] = extended_community_list

    def parse_attribute_large_community(self,code,attr):

        assert 0 == len(attr) % 12, "BGP large community string length not multiple of 12 (%d)" % len(attr)

        community_list = []
        offset = 0
        while offset < len(attr):
            community_list.append(struct.unpack_from('!III', attr, offset=offset)[0])
            offset += 12

        self.attribute[code] = community_list

    def parse_attribute_as_pathlimit(self,code,attr):
            assert len(attr) == 5
            self.attribute[code] = (struct.unpack_from('!B', attr, offset=0)[0],struct.unpack_from('!I', attr, offset=1)[0])
            ##eprint("parse_attribute_as_pathlimit found, value %d from AS %d" % (self.attribute[code]))

    def parse_attribute_connector(self,code,attr):
        # see https://tools.ietf.org/html/draft-nalawade-l3vpn-bgp-connector-00

            assert len(attr) >4
            self.attribute[code] = attr
            ##eprint("parse_attribute_connector: value %s" % attr.hex())


    def parse_attribute_AS_path(self,code,attr,as4=False):

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
    # NB!:
    # AS paths can hold AS4 or AS2 and there is no way to know based on just the BGP message which is present
    # ..... however.....
    # it is exceedingly unlikely  that a valid path in one format is also valid in the other!
    # So, attempting to parse as AS4 first is the right thing to do

    
        def getb_at(msg,pos):
            assert isinstance(msg,bytearray)
            assert 0 < len(msg)
            return struct.unpack_from('!B', msg, offset=pos)[0]
    
        def getw_at(msg,pos):
            assert isinstance(msg,bytearray)
            assert 0 < len(msg)
            return struct.unpack_from('!H', msg, offset=pos)[0]
    
        def getl_at(msg,pos):
            assert isinstance(msg,bytearray)
            assert 0 < len(msg)
            return struct.unpack_from('!I', msg, offset=pos)[0]
    
        def get_segment(msg,as4):
    
            if as4:
                get_asn_at = getl_at
                asn_len = 4
                asn_shift = lambda n : n << 2
            else:
                get_asn_at = getw_at
                asn_len = 2
                asn_shift = lambda n : n << 1
    
            assert len(msg) >= 4
    
            segment_type = getb_at(msg,0)
            assert segment_type == 1 or segment_type == 2
    
            segment_length = getb_at(msg,1)
            assert len(msg) >= 2 + asn_shift(segment_length)
    
            as_list = []
            for offset in range(0,segment_length,asn_len):
                as_list.append(get_asn_at(msg, offset))
    
            return (segment_type,as_list,msg[2 + asn_shift(segment_length):])
    
        def get_segments(msg,as4):
            segments=[]
            while msg:
                segment_type,as_list,msg = get_segment(msg,as4)
                segments.append((segment_type,as_list))
            return segments
    
        segments = []
        try:
            segments = get_segments(attr,True)
        except AssertionError as ae:
            try:
                segments = get_segments(attr,False)
            except AssertionError as ae:
                eprint("could not read AS path as AS2 or AS4")
    
        if segments:
            self.attribute[code] = segments

    def parse_attribute_aggregator(self,code,attr):
    # depending on AS4 nature this is either 8 bytes or 6 bytes
            if len(attr) == 8:
                self.parse_attribute_4b_4b(code,attr)
            elif len(attr) == 6:
                self.parse_attribute_2b_4b(code,attr)
            else:
                assert len(attr) == 6 or len(attr) == 8

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
            self.parse_attribute_AS_path(code,attr)

        elif (code==BGP_TYPE_CODE_NEXT_HOP):
            self.parse_attribute_32bits(code,attr)

        elif (code==BGP_TYPE_CODE_MULTI_EXIT_DISC):
            self.parse_attribute_32bits(code,attr)

        elif (code==BGP_TYPE_CODE_LOCAL_PREF):
            self.parse_attribute_32bits(code,attr)

        elif (code==BGP_TYPE_CODE_ATOMIC_AGGREGATE):
            self.parse_attribute_0_length(code,attr)

        elif (code==BGP_TYPE_CODE_AGGREGATOR):
            self.parse_attribute_aggregator(code,attr)

        elif (code==BGP_TYPE_CODE_COMMUNITIES):
            self.parse_attribute_communities(code,attr)

        elif (code==BGP_TYPE_CODE_EXTENDED_COMMUNITIES):
            self.parse_attribute_extended_communities(code,attr)

        elif (code==BGP_TYPE_CODE_AS4_PATH):
            self.parse_attribute_AS_path(code,attr,as4=True)

        elif (code==BGP_TYPE_CODE_AS4_AGGREGATOR):
            self.parse_attribute_4b_4b(code,attr)

        elif (code==BGP_TYPE_CODE_MP_REACH_NLRI or code == BGP_TYPE_CODE_MP_UNREACH_NLRI):
            self.parse_attribute_unhandled(code,attr)

        elif (code==BGP_TYPE_CODE_LARGE_COMMUNITY):
            self.parse_attribute_large_community(code,attr)

        elif (code==BGP_TYPE_CODE_ATTR_SET):
            self.parse_attribute_attribute_set(code,attr)

        elif (code==BGP_TYPE_CODE_AS_PATHLIMIT):
            self.parse_attribute_as_pathlimit(code,attr)

        elif (code==BGP_TYPE_CODE_CONNECTOR):
            self.parse_attribute_connector(code,attr)

        else:
            assert False , "Unknown BGP path attribute type %d" % code

    def parse_bgp_notification(self,msg):
        pass
