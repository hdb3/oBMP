#!/usr/bin/python3
#
# unittest-capability.py
#

from capability import Capability

from capabilitycodes import BGP_capability_codes,AFI_IPv4,SAFI_Unicast
cc = BGP_capability_codes

    # def decode_cap(msg):

    # def display_cap(tpl):

def main():

    print("\n######\n")
    cap = Capability.cap(cc.route_refresh)
    print("Capability.cap(route_refresh)")
    print(cap.hex())
    decap = Capability.decode_cap(cap)
    print(decap)
    display = Capability.display_cap(decap)
    print(display)
    print("\n######\n")

    cap = Capability.cap(cc.multiprotocol,(AFI_IPv4,SAFI_Unicast))
    print("Capability.cap(multiprotocol)")
    print(cap.hex())
    decap = Capability.decode_cap(cap)
    print(decap)
    display = Capability.display_cap(decap)
    print(display)
    print("\n######\n")

    cap = Capability.cap(cc.AS4,77777)
    print("Capability.cap(AS4)")
    print(cap.hex())
    decap = Capability.decode_cap(cap)
    print(decap)
    display = Capability.display_cap(decap)
    print(display)
    print("\n######\n")

    cap = Capability.cap(cc.graceful_restart,(False,1000))
    print("Capability.cap(graceful_restart)")
    print(cap.hex())
    decap = Capability.decode_cap(cap)
    print(decap)
    display = Capability.display_cap(decap)
    print(display)
    print("\n######\n")


main()
