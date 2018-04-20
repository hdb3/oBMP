# bgpcodes.py
#

from enum import IntEnum

class BGP_message_types(IntEnum):
    OPEN = 1
    UPDATE = 2
    NOTIFICATION = 3
    KEEPALIVE = 4

class BGP_attribute_types(IntEnum):

    ORIGIN = 1
    AS_PATH = 2
    NEXT_HOP = 3
    MULTI_EXIT_DISC = 4
    LOCAL_PREF = 5
    ATOMIC_AGGREGATE = 6
    AGGREGATOR = 7
    COMMUNITIES = 8
    MP_REACH_NLRI = 14
    MP_UNREACH_NLRI = 15
    EXTENDED_COMMUNITIES = 16
    AS4_PATH = 17
    AS4_AGGREGATOR = 18
    CONNECTOR = 20
    AS_PATHLIMIT = 21
    LARGE_COMMUNITY = 32
    ATTR_SET = 128

class BGP_ORIGIN_codes(IntEnum):
    IGP = 0
    EGP = 1
    INCOMPLETE = 2

class BGP_AS_PATH_SEGMENT_type(IntEnum):
    AS_SET = 1
    AS_SEQUENCE = 2

class BGP_attribute_flags(IntEnum):
    Optional = 0x80 # 1 << 7
    Transitive = 0x40 # 1 << 6
    Partial = 0x20 # 1 << 5
    Extended_Length = 0x10 # 1 << 4


# ref https://www.iana.org/assignments/capability-codes/capability-codes.xml

class BGP_capability_codes(IntEnum):
    multiprotocol = 1
    route_refresh = 2
    outbound_route_filtering = 3
    multiple_routes = 4
    extended_next_hop_encoding = 5
    BGP_extended_message = 6
    BGPsec = 7
    multiple_labels = 8
    BGP_role = 9
    graceful_restart = 64
    AS4 = 65
    dynamic_capability = 67
    multisession = 68
    add_path = 69
    enhanced_route_refresh = 70
    long_lived_graceful_restart = 71
    FQDN = 73
    cisco_route_refresh = 128

class BGP_address_families(IntEnum):
    AFI_IPv4 = 1
    SAFI_Unicast = 1
valid_codes = set(BGP_capability_codes.__members__.values())
