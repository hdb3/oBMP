#!/usr/bin/python3

# unittest-bgpupdate.py
#
from bgpupdate import BGP_UPDATE_message as bu
from bgpmsg import BGP_message as bm
from bgpcodes import BGP_message_types
#from bgppathattributes import BGP_attribute as ba
from bgppathattributes import *
import sys


def test(updates,withdrawn,paths):
    update = bu.new(updates,withdrawn,paths)
    update_deparsed = update.deparse()
    msg = bm.deparse(BGP_message_types.UPDATE,update_deparsed)
    #sys.stdout.buffer.write(msg)
    print("type %s val %s" % ( str(type(msg)),msg.hex()))

#test([],[],[])
#test([],[],[as_path([100,200])])

#test([],[],[origin(IGP), as_path([100,200]), next_hop('192.168.0.1')])
test(['0.0.0.0/0'],[],[])
test(['192.168.42.0/24','192.168.0.0/16','10.0.0.0/8','10.1.1.0/25'],['172.20.0.0/14','172.26.0.0/15'],[origin(IGP), as_path([100,200]), next_hop('192.168.0.1')])
