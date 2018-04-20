
import sys
from ipaddress import IPv4Address
from bgpcodes import *

at = BGP_attribute_types

class BGP_attribute:

    def __str__(self):

        def display_path(path):
            if len(path) == 0:
                return None
            elif len(path) == 1:
                return str(path[0])
            else:
                v = str(path[0])
                for x in path[1:]:
                    v += ':' + str(x)
                return v

        v = None

        if (code==at.ORIGIN):
            v = BGP_ORIGIN_codes(self.attribute).name

        elif (code==at.AS_PATH):
            v = display_path(self.attribute)
        elif (code==at.NEXT_HOP):
            v = str(IPv4Addr(self.attribute))
        elif (code==at.MULTI_EXIT_DISC):
            v = str(self.attribute)
        elif (code==at.LOCAL_PREF):
            v = str(self.attribute)
        elif (code==at.ATOMIC_AGGREGATE):
            pass
        elif (code==at.AGGREGATOR):
            v = str(self.attribute)
        elif (code==at.COMMUNITIES):
            v = str(self.attribute)
        elif (code==at.EXTENDED_COMMUNITIES):
            v = str(self.attribute)
        elif (code==at.AS4_PATH):
            v = display_path(self.attribute)
        elif (code==at.AS4_AGGREGATOR):
            v = str(self.attribute)
        elif (code==at.MP_REACH_NLRI or code == at.MP_UNREACH_NLRI):
            pass
        elif (code==at.LARGE_COMMUNITY):
            v = str(self.attribute)
        elif (code==at.ATTR_SET):
            v = str(self.attribute)
        elif (code==at.AS_PATHLIMIT):
            v = "%d:%d" % self.attribute
        elif (code==at.CONNECTOR):
            v = str(self.attribute)
        else:
            assert False , "Unknown BGP path attribute type %d" % code

    def parse_attribute_attribute_set(self,code,attr):
        assert False, "parse_attribute_attribute_set not implemented"

    def parse_attribute_list_of_int(self,code,attr):
        assert isinstance(attr,list) and len(attr) > 0
        for x in attr:
            assert isinstance(x,int)
        self.attribute = attr

    def parse_attribute_connector(self,code,attr):
        # see https://tools.ietf.org/html/draft-nalawade-l3vpn-bgp-connector-00

            assert len(attr) >4
            self.attribute = attr

    def parse_attribute_AS_path(self,code,attr):
        # simple as paths are jsut lists of numbers
        # multiple segments are lists of tuples
        assert isinstance(attr,list)
        if len(attr) == 0:
            self.attribute = None
        elif isinstance(attr[0],int):
            self.attribute = [(BGP_AS_PATH_SEGMENT_type.AS_SEQUENCE,attr)]
        elif isinstance(attr[0],tuple) and isinstance(attr[0][0],int) and isinstance(attr[0][0],list):
            self.attribute = attr
        else:
            assert False, "could not figure out what kind os AS path it is"

    def parse_attribute_int_int(self,code,attr):
        assert isinstance(attr,tuple) and len(attr) == 2 and isinstance(attr[0],int) and isinstance(attr[1],int)
        self.attribute = attr

    def parse_attribute_32bits(self,code,attr):
        assert isinstance(attr,int)
        ## print("type",type(attr),file=sys.stderr)
        assert attr < 0x100000000
        self.attribute = attr

    def parse_attribute_8bits(self,code,attr):
        assert isinstance(attr,int) and attr < 256
        self.attribute = attr

    def parse_attribute_0_length(self,code,attr):
        assert attr is None
        self.attribute = None

    def parse_attribute_unhandled(self,code,attr):
        self.attribute = attr
        self.unhandled_codes.append(code)

    def __init__(self,code,attribute):

        self.code = code

        if (code==at.ORIGIN):
            assert attribute in BGP_ORIGIN_codes.__members__.values()
            self.parse_attribute_8bits(code,attribute)

        elif (code==at.AS_PATH):
            self.parse_attribute_AS_path(code,attribute)

        elif (code==at.NEXT_HOP):
            if isinstance(attribute,IPv4Address):
                self.parse_attribute_32bits(code,int(attribute))
            else:
                self.parse_attribute_32bits(code,attribute)

        elif (code==at.MULTI_EXIT_DISC):
            self.parse_attribute_32bits(code,attribute)

        elif (code==at.LOCAL_PREF):
            self.parse_attribute_32bits(code,attribute)

        elif (code==at.ATOMIC_AGGREGATE):
            self.parse_attribute_0_length(code,attribute)

        elif (code==at.AGGREGATOR):
            self.parse_attribute_int_int(code,attribute)

        elif (code==at.COMMUNITIES):
            self.parse_attribute_list_of_int(code,attribute)

        elif (code==at.EXTENDED_COMMUNITIES):
            self.parse_attribute_list_of_int(code,attribute)

        elif (code==at.AS4_PATH):
            self.parse_attribute_AS_path(code,attribute)

        elif (code==at.AS4_AGGREGATOR):
            self.parse_attribute_int_int(code,attribute)

        elif (code==at.MP_REACH_NLRI or code == at.MP_UNREACH_NLRI):
            self.parse_attribute_unhandled(code,attribute)

        elif (code==at.LARGE_COMMUNITY):
            self.parse_attribute_list_of_int(code,attribute)

        elif (code==at.ATTR_SET):
            self.parse_attribute_attribute_set(code,attribute)

        elif (code==at.AS_PATHLIMIT):
            self.parse_attribute_int_int(code,attribute)

        elif (code==at.CONNECTOR):
            self.parse_attribute_connector(code,attribute)

        else:
            assert False , "Unknown BGP path attribute type %d" % code

    def value(self):
        return (self.code.value,self.attribute)

    @classmethod
    def origin(cls,attribute):
        self = cls(at.ORIGIN,attribute)
        return self

    @classmethod
    def as_path(cls,attribute):
        self = cls(at.AS_PATH,attribute)
        return self

    @classmethod
    def next_hop(cls,attribute):
        self = cls(at.NEXT_HOP,IPv4Address(attribute))
        return self

origin =  BGP_attribute.origin
as_path =  BGP_attribute.as_path
next_hop =  BGP_attribute.next_hop
IGP = BGP_ORIGIN_codes.IGP
EGP = BGP_ORIGIN_codes.EGP
INCOMPLETE = BGP_ORIGIN_codes.INCOMPLETE
