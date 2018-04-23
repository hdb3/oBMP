
# bmpcontext.py

import os
import sys
import time
import bmpapp
from bmpparse import BMP_message, BMP_Initiation_Message, BMP_Termination_Message, BMP_Peer_Down_Notification, \
                     BMP_Peer_Up_Notification, BMP_Route_Monitoring, BMP_Statistics_Report
from bgpcontext import BGP_context


class BMP_peer:

    def __init__(self, peer):
        self.source = peer['source']
        self.peer_data = peer
        self.peer_string = "AS%d:%s" % (peer['remote_AS'], peer['remote_IPv4_address'])
        print("new peer connected %s" % self.peer_string)
        self.state = "undefined"
        self.stats_count = 0
        self.RM_count = 0
        self.bgp_context = BGP_context(self.peer_data)
        try:
            os.mkdir("dump")
        except OSError as e:
            pass
        ts = str(time.time())
        self.bmp_file = open("dump/" + self.source + "-" +self.peer_string + "-" + ts + ".bmp","wb")


    def consume(self, msg_type, msg, raw_msg):
        self.bmp_file.write(raw_msg)
        if msg_type == BMP_Peer_Down_Notification:
            print("peer down for %s" % self.peer_string)
            self.state = "down"
        elif msg_type == BMP_Peer_Up_Notification:
            print("peer up for %s" % self.peer_string)
            self.state = "up"
            ##self.bgp_context.consume(msg)
        elif msg_type == BMP_Statistics_Report:
            self.stats_count  += 1
            print("stats report %d for %s" % (self.stats_count, self.peer_string))
        elif msg_type == BMP_Route_Monitoring:
            self.RM_count  += 1
            self.bgp_context.consume(msg)

class BMP_process:
    
    def __init__(self,source):
        self.parser = bmpapp.BmpContext(source)
        self.peers = {}
        self.source = source
        self.count = 0

    def process_message(self,bmp_msg):
        self.count += 1
        sys.stderr.buffer.write(b'\rBMP_process.process_message(%d)\r' % self.count)
        ( msg_type, peer, msg ) = self.parser.parse(BMP_message(bmp_msg))
        if msg_type == BMP_Initiation_Message:
            print("BMP session start")
        elif msg_type == BMP_Termination_Message:
            print("BMP session end")
        else:
            if not peer['hash'] in self.peers:
                peer['source'] = self.source
                self.peers[peer['hash']] = BMP_peer(peer)
            self.peers[peer['hash']].consume(msg_type,msg,bmp_msg)

    def get_next(self,msg):
        tail,bmp_msg = BMP_message.get_next(msg)
        self.process_message(bmp_msg)
        return tail
