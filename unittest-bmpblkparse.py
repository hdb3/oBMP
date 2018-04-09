#!/usr/bin/python3

#
# collector.py
# this is a generic TCP active sender
#
import os.path
import errno
import yaml
import traceback
import sys
import socket
import threading
from time import sleep
import pprint
import bgpparse
import bmpparse
import BGPribdb
import bmpblkparse

def log(c):
    sys.stderr.write(c)
    sys.stderr.flush()

class UnitTest():

    def __init__(self,f,count):
        self.f=f
        self.count = count
        self.name = "bmpd unit-test"

    def recv(self):
        return self.f.read(self.count)

    def bmpd(self):
        rib = BGPribdb.BGPribdb()
        blkparser = bmpblkparse.BMP_unblocker(parse=False)
        i = 0
        log("Session.bmpd(%s) starting\n" % self.name)

        while True:
        #while i < self.count:
            msg = self.recv()
            if 0 == len(msg):
                break
            i += 1
            print("msg(%d) rcvd length %d" % (i,len(msg)))
            bmpmsgs = blkparser.push(msg)
            print("BMP block parser returned %d BMP messages" % len(bmpmsgs))
            #bmpmsg = bmpparse.BMP_message(msg)
            for bmpmsg in bmpmsgs:
                msg_type = blkparser.bmp_message_type(bmpmsg)
                msg_length = len(bmpmsg)
                if msg_type == bmpparse.BMP_Initiation_Message:
                    print("-- BMP Initiation Message rcvd, length %d" % msg_length)
                elif msg_type == bmpparse.BMP_Peer_Up_Notification:
                    print("-- BMP Peer Up rcvd, length %d" % msg_length)
                elif msg_type == bmpparse.BMP_Statistics_Report:
                    print("-- BMP stats report rcvd, length %d" % msg_length)
                    ##print(rib)
                elif msg_type == bmpparse.BMP_Route_Monitoring:
                    print("-- BMP Route Monitoring rcvd, length %d" % msg_length)
                    #bgpmsg = bmpmsg.bmp_RM_bgp_message
                    #parsed_bgp_message = bgpparse.BGP_message(bgpmsg)
                    ##rib.withdraw(parsed_bgp_message.withdrawn_prefixes)
                    ##if parsed_bgp_message.except_flag:
                        ##forwarder.send(bgpmsg)
                    ##else:
                        ##rib.update(parsed_bgp_message.attribute,parsed_bgp_message.prefixes)
                else:
                    sys.stderr.write("-- BMP non RM rcvd, BmP msg type was %d, length %d\n" % (msg_type,msg_length))


        log("Session.bmpd(%s) exiting\n" % self.name)

f = open(sys.argv[1],'rb')
if len(sys.argv) > 2:
    c = int(sys.argv[2])
else:
    c = 4096
run=UnitTest(f,c)
run.bmpd()
