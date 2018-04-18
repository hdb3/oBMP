#!/usr/bin/python3
#
# unittest-bgpopen.py
#

#from capability import Capability

import bgpopen
#import capability
from ipaddress import IPv4Address
from capability import Capability

from capabilitycodes import BGP_capability_codes,AFI_IPv4,SAFI_Unicast
cc = BGP_capability_codes

    # def decode_cap(msg):

    # def display_cap(tpl):

def main():

    caps = []
    caps.append( (cc.route_refresh, None) )
    caps.append( (cc.multiprotocol,(AFI_IPv4,SAFI_Unicast)) )
    caps.append( (cc.AS4,64505) )
    caps.append( (cc.graceful_restart,(False,1000)) )

    msg = bgpopen.BGP_OPEN_message.new(64505,60,IPv4Address('10.30.65.209'),caps)

    print(msg)
    raw_msg = msg.deparse()
    print(raw_msg.hex())

    parsed_message = bgpopen.BGP_OPEN_message.parse(raw_msg)

    print("parsed message is :")
    print(parsed_message)

main()
