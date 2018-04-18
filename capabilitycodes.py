
# ref https://www.iana.org/assignments/capability-codes/capability-codes.xml

from enum import IntEnum
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

AFI_IPv4 = 1
SAFI_Unicast = 1
