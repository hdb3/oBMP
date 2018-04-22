# bgpupdate.py
#
# parse and build a representation of a BGP UPDATE message
# the exposed methods are parse, deparse and new
# parse and new create new message objects
# deparse takes an object and creates a corresponding wire-format message
#


import sys
import traceback
import struct
from ipaddress import IPv4Network,AddressValueError
#from bgpmsg import BGP_message

logfile=sys.stderr
def eprint(s):
    logfile.write(s+'\n')
    logfile.flush()
    return

def b(x):
    return bytearray([x])

def w(x):
    return struct.pack('!H',x)

def l(x):
    return struct.pack('!I',x)


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

attribute_flags = dict([
    (BGP_TYPE_CODE_ORIGIN, BGP_Attribute_Flags_Transitive), \
    (BGP_TYPE_CODE_AS_PATH, BGP_Attribute_Flags_Transitive), \
    (BGP_TYPE_CODE_NEXT_HOP, BGP_Attribute_Flags_Transitive), \
    (BGP_TYPE_CODE_MULTI_EXIT_DISC, BGP_Attribute_Flags_Optional), \
    (BGP_TYPE_CODE_LOCAL_PREF, BGP_Attribute_Flags_Transitive), \
    (BGP_TYPE_CODE_ATOMIC_AGGREGATE, BGP_Attribute_Flags_Transitive), \
    (BGP_TYPE_CODE_AGGREGATOR, BGP_Attribute_Flags_Transitive | BGP_Attribute_Flags_Optional), \
    (BGP_TYPE_CODE_COMMUNITIES, BGP_Attribute_Flags_Transitive | BGP_Attribute_Flags_Optional), \
    (BGP_TYPE_CODE_MP_REACH_NLRI, BGP_Attribute_Flags_Optional), \
    (BGP_TYPE_CODE_MP_UNREACH_NLRI, BGP_Attribute_Flags_Optional), \
    (BGP_TYPE_CODE_EXTENDED_COMMUNITIES, BGP_Attribute_Flags_Transitive | BGP_Attribute_Flags_Optional), \
    (BGP_TYPE_CODE_AS4_PATH, BGP_Attribute_Flags_Optional), \
    (BGP_TYPE_CODE_AS4_AGGREGATOR, BGP_Attribute_Flags_Optional), \
    (BGP_TYPE_CODE_CONNECTOR, BGP_Attribute_Flags_Transitive | BGP_Attribute_Flags_Optional), \
    (BGP_TYPE_CODE_AS_PATHLIMIT, BGP_Attribute_Flags_Transitive | BGP_Attribute_Flags_Optional), \
    (BGP_TYPE_CODE_LARGE_COMMUNITY, BGP_Attribute_Flags_Transitive | BGP_Attribute_Flags_Optional), \
    (BGP_TYPE_CODE_ATTR_SET, BGP_Attribute_Flags_Transitive | BGP_Attribute_Flags_Optional)
])

def get_flags(code):
    return attribute_flags[code]

def show_flags(flags):
    if bool(flags & BGP_Attribute_Flags_Optional):
        s = 'O'
    else:
        s = 'o'
    if bool(flags & BGP_Attribute_Flags_Transitive):
        return s + 'T'
    else:
        return s + 't'

def check_flags(code,flags):
    assert (flags & (BGP_Attribute_Flags_Optional | BGP_Attribute_Flags_Transitive) ) == attribute_flags[code] , \
        "flag check failed for attribute %d, flags %s:%s" % (code, show_flags(flags), show_flags(attribute_flags[code]))

class BGP_UPDATE_message:

    def __init__(self):
        self.except_flag = False
        self.as4_flag = None
        self.unhandled_codes = []
        self.path_attributes = {}
        self.partial_flags = {}

    def as4_check(self,as4_flag):
        if self.as4_flag is None:
            self.as4_flag = as4_flag
        else:
            assert self.as4_flag == as4_flag


    def __str__(self):
        from pprint import pformat
        return str(pformat(vars(self)))

    @classmethod
    def new(cls,updates,withdrawn,paths):
        return cls._new(map(IPv4Network,updates),map(IPv4Network,withdrawn),paths)

    @classmethod
    def _new(cls,updates,withdrawn,paths):
        self = cls()
        for attribute in paths:
            code,attribute = attribute.value()
            self.path_attributes[code] = attribute
        self.withdrawn_prefixes = withdrawn
        self.prefixes = updates
        return self

    @classmethod
    def parse(cls,msg):
        self = cls()
        lm = len(msg)
        withdrawn_routes_length = struct.unpack_from('!H', msg, offset=0)[0]
        assert lm > withdrawn_routes_length + 3
        self.process_withdrawn_routes(msg[2:2+withdrawn_routes_length])
        path_attribute_length = struct.unpack_from('!H', msg, offset=withdrawn_routes_length+2)[0]
        assert lm > withdrawn_routes_length + 3 + path_attribute_length
        self.process_NLRI(msg[ withdrawn_routes_length + 4 + path_attribute_length:])
        self.process_path_attributes(msg[withdrawn_routes_length + 4 : withdrawn_routes_length + 4 + path_attribute_length])
        self.end_of_rib = ( 0 == len(self.withdrawn_prefixes)) \
                      and ( 0 == len(self.prefixes)) \
                      and ( 0 == len(self.path_attributes))
        return self

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

            prefixes.append(IPv4Network((prefix,prefix_length)))
            offset += 1 + prefix_byte_length

        return prefixes


    def process_path_attributes(self,attributes):

        offset = 0
        attributes_len = len(attributes)
        attr_count = 0
        while offset < attributes_len:
            attr_flags = struct.unpack_from('!B', attributes, offset=offset)[0]
            attr_type_code = struct.unpack_from('!B', attributes, offset=offset+1)[0]

            check_flags(attr_type_code,attr_flags)
            if attr_flags & BGP_Attribute_Flags_Partial:
                self.partial_flags[attr_type_code] = None

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
                        % (attr_count,offset,length,attr_flags,attr_type_code,attribute.hex()))
                eprint("++failed to parse attribute  : error: %s" % e)
                eprint("++failed to parse attributes : %d %s" % (attributes_len,attributes.hex()))
                traceback.print_tb( sys.exc_info()[2])
                exit()
            offset += length+quantum


        if len(self.prefixes) > 0:

            if BGP_TYPE_CODE_ORIGIN not in self.path_attributes:
                eprint("mandatory attribute BGP_TYPE_CODE_ORIGIN missing")
                self.except_flag = True
            if BGP_TYPE_CODE_AS_PATH not in self.path_attributes:
                eprint("mandatory attribute BGP_TYPE_CODE_AS_PATH missing")
                self.except_flag = True
            if BGP_TYPE_CODE_NEXT_HOP not in self.path_attributes:
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

        self.path_attributes[code] = community_list

    def parse_attribute_attribute_set(self,code,attr):

        assert 4 < len(attr), "BGP  attribute set length less than 4 (%d)" % len(attr)

        self.path_attributes[code] = ((struct.unpack_from('!I', attr, offset=0)[0],attr[4:]))

    def parse_attribute_extended_communities(self,code,attr):

        assert 0 == len(attr) % 8, "BGP extended community string length not multiple of 8 (%d)" % len(attr)

        extended_community_list = []

        for offset in range(0,len(attr),8):
            extended_community_list.append((struct.unpack_from('!H', attr, offset=offset)[0],attr[offset+2:offset+8]))

        self.path_attributes[code] = extended_community_list

    def parse_attribute_large_community(self,code,attr):

        assert 0 == len(attr) % 12, "BGP large community string length not multiple of 12 (%d)" % len(attr)

        community_list = []
        offset = 0
        while offset < len(attr):
            community_list.append(attr[offset:offset+12])
            offset += 12

        self.path_attributes[code] = community_list

    def parse_attribute_as_pathlimit(self,code,attr):
            assert len(attr) == 5
            self.path_attributes[code] = (struct.unpack_from('!B', attr, offset=0)[0],struct.unpack_from('!I', attr, offset=1)[0])
            ##eprint("parse_attribute_as_pathlimit found, value %d from AS %d" % (self.path_attributes[code]))

    def parse_attribute_connector(self,code,attr):
        # see https://tools.ietf.org/html/draft-nalawade-l3vpn-bgp-connector-00

            assert len(attr) >4
            self.path_attributes[code] = attr
            ##eprint("parse_attribute_connector: value %s" % attr.hex())



    # an AS path attribute has 1 or more AS segments
    # each segment is represented by 1 byte segment type + 1 byte segment length + variable number of AS
    # the 1 byte segment length is a count of AS, not bytes
    # the ASes are 2 or 4 byte values depending on AS/AS4 attribute nature
    #
    # if the AS4 state is unknown thene the parser tries both
    # in the unlikley event both views are valid it will select AS4
    # but not very likely i think
    # ( update - it really does happen!!!!! )

    def parse_attribute_AS_path(self,code,attr,as4=False):

        def getb_at(msg,pos):
            return struct.unpack_from('!B', msg, offset=pos)[0]

        def getw_at(msg,pos):
            return struct.unpack_from('!H', msg, offset=pos)[0]

        def getl_at(msg,pos):
            return struct.unpack_from('!I', msg, offset=pos)[0]

        def get_segments(msg,siz):

            if msg is None:
                return (False, "(0) - null msg")
                
            if not isinstance(msg,bytearray):
                return (False, "(1) - invalid msg type %s" % str(type(msg)))
                
            if len(msg) == 0:
                return (False, "(3) - empty msg")
                
            if siz not in (2,4):
                return (False, "(4) - invalid size %d" % siz)

            offset = 0
            segments = []
            while offset < len(msg):
                if len(msg) - offset < 2 + siz:
                    return (False, "(5) - short segment")
                t = getb_at(msg,offset)
                if t not in (1,2):
                    return (False, "(6) - invalid segment type %d" % t)
                l = getb_at(msg,offset+1)
                if l == 0:
                    return (False, "(7) - zero segment length")
                pathbytelength = l * siz
                if len(msg) < offset+2+pathbytelength:
                    return (False, "(8) - short segment length %d < %d" % (len(msg),offset+2+pathbytelength))
                path = []
                for ix in range(offset+2,offset+2+pathbytelength,siz):
                    if siz == 2:
                        path.append(getw_at(msg,ix))
                    else:
                        path.append(getl_at(msg,ix))
                segments.append((t,path))
                offset += 2 + pathbytelength
            return (True,segments)

        if len(attr) == 0:
            # an empty AS path is perfectly valid for iBGP
            self.path_attributes[code] = []
        else:
            if self.as4_flag is None:
                path_as4 = get_segments(attr,4)
                path_as2 = get_segments(attr,2)
                if path_as4[0] and path_as2[0]:
                    eprint("ambiguous AS path can be read as AS2 or AS4 - choosing AS4")
                    self.as4_flag = True
                    segments = path_as4[1]
                    self.except_flag = True
                elif path_as4[0]:
                    self.as4_flag = True
                    segments = path_as4[1]
                elif path_as2[0]:
                    self.as4_flag = False
                    segments = path_as2[1]
                else:
                    eprint("invalid AS path can not be read as AS2 or AS4")
                    eprint("AS4 error parse msg: %s" % path_as4[1])
                    eprint("AS2 error parse msg: %s" % path_as2[1])
                    segments = None
                    self.except_flag = True
            else:
                if self.as4_flag:
                    path = get_segments(attr,4)
                else:
                    path = get_segments(attr,2)
    
                if path[0]:
                    segments = path[1]
                else:
                    eprint("invalid AS path")
                    eprint("error parse msg: %s" % path[1])
                    segments = None
                    self.except_flag = True

            if segments:
                self.path_attributes[code] = segments

    def parse_attribute_aggregator(self,code,attr):
    # depending on AS4 nature this is either 8 bytes or 6 bytes
            if len(attr) == 8:
                self.as4_check(True)
                self.parse_attribute_4b_4b(code,attr)
            elif len(attr) == 6:
                self.as4_check(False)
                self.parse_attribute_2b_4b(code,attr)
            else:
                assert len(attr) == 6 or len(attr) == 8

    def parse_attribute_4b_4b(self,code,attr):
            assert len(attr) == 8
            self.path_attributes[code] = (struct.unpack_from('!I', attr, offset=0)[0],struct.unpack_from('!I', attr, offset=2)[0])

    def parse_attribute_2b_4b(self,code,attr):
            assert len(attr) == 6
            self.path_attributes[code] = (struct.unpack_from('!H', attr, offset=0)[0],struct.unpack_from('!I', attr, offset=2)[0])

    def parse_attribute_32bits(self,code,attr):
            assert len(attr) == 4
            self.path_attributes[code] = struct.unpack_from('!I', attr, offset=0)[0]

    def parse_attribute_8bits(self,code,attr):
            assert len(attr) == 1
            self.path_attributes[code] = struct.unpack_from('!B', attr, offset=0)[0]

    def parse_attribute_0_length(self,code,attr):
        assert len(attr) == 0
        self.path_attributes[code] = None

    def parse_attribute_unhandled(self,code,attr):
            self.path_attributes[code] = attr
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


# ## ### #### ##### ###### ####### ######## ######### ########## ########### ############ #############
#
# Deparser
#
# ## ### #### ##### ###### ####### ######## ######### ########## ########### ############ #############

    def deparse_path_attributes(self):

        def encode_attribute(code,flags,attribute):

            msg = bytearray()
            if len(attribute) > 255 or code == BGP_TYPE_CODE_AS_PATH:
                # always write an AS_PATH as extended, for compatibility with e.g. quagga
                msg.extend(b(flags | BGP_Attribute_Flags_Extended_Length))
                msg.extend(b(code))
                msg.extend(w(len(attribute)))
            else:
                msg.extend(b(flags))
                msg.extend(b(code))
                msg.extend(b(len(attribute)))
            msg.extend(attribute)
            return msg

        def deparse_communities(code,attr):

            msg = bytearray()
            for community in attr:
                msg.extend(l(community))

            return msg

        def deparse_attribute_set(code,attr):

            msg = bytearray()
            msg.extend(l(attr[0]))
            msg.extend(attr[1])
            return msg

        def deparse_extended_communities(code,attr):

            msg = bytearray()
            for ec1,ec2 in attr:
                msg.extend(w(ec1))
                msg.extend(ec2)

            return msg

        def deparse_large_community(code,attr):

            msg = bytearray()
            for large_community in attr:
                assert 12 == len(large_community)
                msg.extend(large_community)

            return msg

        def deparse_as_pathlimit(code,attr):
            msg = bytearray()
            msg.extend(b(attr[0]))
            msg.extend(l(attr[1]))
            return msg

        def deparse_connector(code,attr):
            # see https://tools.ietf.org/html/draft-nalawade-l3vpn-bgp-connector-00
            return attr

        def deparse_unhandled(code,attr):
            return attr


        # an AS path attribute has 1 or more AS segments
        # each segment is represented by 1 byte segment type + 1 byte segment length + variable number of AS
        # the 1 byte segment length is a count of AS, not bytes
        # the ASes are 2 or 4 byte values depending on AS/AS4 attribute nature
        #

        def deparse_AS_path(code,attr,as4):

            msg = bytearray()

            for segment_type,as_list in attr:
                msg.extend(b(segment_type))
                msg.extend(b(len(as_list)))
                for AS in as_list:
                    if as4:
                        msg.extend(l(AS))
                    else:
                        msg.extend(w(AS))
            return msg


        # depending on AS4 nature deparse_aggregator is either 8 bytes or 6 bytes

        def deparse_aggregator(code,attr,as4):
            if as4:
                return deparse_4b_4b(code,attr)
            else:
                return deparse_2b_4b(code,attr)

        def deparse_4b_4b(code,attr):
            msg = bytearray()
            msg.extend(l(attr[0]))
            msg.extend(l(attr[1]))
            return msg

        def deparse_2b_4b(code,attr):
            msg = bytearray()
            msg.extend(w(attr[0]))
            msg.extend(l(attr[1]))
            return msg

        def deparse_32bits(code,attr):
            return l(attr)

        def deparse_8bits(code,attr):
            return b(attr)

        def deparse_0_length(code,attr):
            return bytearray()

        def deparse_path_attribute(code,attr):
            if (code==BGP_TYPE_CODE_ORIGIN):
                return deparse_8bits(code,attr)

            elif (code==BGP_TYPE_CODE_AS_PATH):
                return deparse_AS_path(code,attr,self.as4_flag)

            elif (code==BGP_TYPE_CODE_NEXT_HOP):
                return deparse_32bits(code,attr)

            elif (code==BGP_TYPE_CODE_MULTI_EXIT_DISC):
                return deparse_32bits(code,attr)

            elif (code==BGP_TYPE_CODE_LOCAL_PREF):
                return deparse_32bits(code,attr)

            elif (code==BGP_TYPE_CODE_ATOMIC_AGGREGATE):
                return deparse_0_length(code,attr)

            elif (code==BGP_TYPE_CODE_AGGREGATOR):
                return deparse_aggregator(code,attr,self.as4_flag)

            elif (code==BGP_TYPE_CODE_COMMUNITIES):
                return deparse_communities(code,attr)

            elif (code==BGP_TYPE_CODE_EXTENDED_COMMUNITIES):
                return deparse_extended_communities(code,attr)

            elif (code==BGP_TYPE_CODE_AS4_PATH):
                return deparse_AS_path(code,attr,self.as4_flag)

            elif (code==BGP_TYPE_CODE_AS4_AGGREGATOR):
                return deparse_4b_4b(code,attr)

            elif (code==BGP_TYPE_CODE_MP_REACH_NLRI or code == BGP_TYPE_CODE_MP_UNREACH_NLRI):
                return deparse_unhandled(code,attr)

            elif (code==BGP_TYPE_CODE_LARGE_COMMUNITY):
                return deparse_large_community(code,attr)

            elif (code==BGP_TYPE_CODE_ATTR_SET):
                return deparse_attribute_set(code,attr)

            elif (code==BGP_TYPE_CODE_AS_PATHLIMIT):
                return deparse_as_pathlimit(code,attr)

            elif (code==BGP_TYPE_CODE_CONNECTOR):
                return deparse_connector(code,attr)

            else:
                assert False , "Unknown BGP path attribute type %d" % code

        msg = bytearray()
        for code,attr in self.path_attributes.items():
            flags = get_flags(code)
            if code in self.partial_flags:
                flags |= BGP_Attribute_Flags_Partial
            msg.extend(encode_attribute(code,flags,deparse_path_attribute(code,attr)))
        return msg

    def deparse(self):

        def deparse_prefixes(prefix_list):

            msg = bytearray()
            for network in prefix_list:
                msg.extend(b(network.prefixlen))
                prefix_bytearray = l(int(network.network_address))
                if network.prefixlen > 24:
                    msg.extend(prefix_bytearray)
                elif network.prefixlen > 16:
                    msg.extend(prefix_bytearray[:3])
                elif network.prefixlen > 8:
                    msg.extend(prefix_bytearray[:2])
                elif network.prefixlen > 0:
                    msg.extend(prefix_bytearray[:1])
                else:
                    pass

            return msg

        msg = bytearray()

        withdrawn_routes = deparse_prefixes(self.withdrawn_prefixes)
        msg.extend(w(len(withdrawn_routes)))
        msg.extend(withdrawn_routes)

        path_attributes = self.deparse_path_attributes()
        msg.extend(w(len(path_attributes)))
        msg.extend(path_attributes)

        msg.extend(deparse_prefixes(self.prefixes))

        return msg

