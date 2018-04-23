
# bmpcontext.py

import bmpapp
from bmpparse import BMP_message, BMP_Initiation_Message, BMP_Termination_Message, BMP_Peer_Down_Notification, \
                     BMP_Peer_Up_Notification, BMP_Route_Monitoring, BMP_Statistics_Report

class BMP_peer:

    def __init__(self,peer):
        self.peer_data = peer
        self.peer_string = "AS%d:%s" % (peer['remote_AS'], peer['remote_IPv4_address'])
        print("new peer connected %s" % self.peer_string)
        self.state = "undefined"
        self.stats_count = 0
        self.RM_count = 0

            
    def consume(self,msg_type,msg):
        if msg_type == BMP_Peer_Down_Notification:
            print("peer down for %s" % self.peer_string)
            self.state = "down"
        elif msg_type == BMP_Peer_Up_Notification:
            print("peer up for %s" % self.peer_string)
            self.state = "up"
        elif msg_type == BMP_Statistics_Report:
            self.stats_count  += 1
            print("stats report %d for %s" % (self.stats_count, self.peer_string))
        elif msg_type == BMP_Route_Monitoring:
            self.RM_count  += 1
            print("RM %d for %s" % (self.RM_count, self.peer_string))

class BMP_process:
    
    def __init__(self):
        self.parser = bmpapp.BmpContext("simple")
        self.peers = {}

    def process_message(self,bmp_msg):
        ( msg_type, peer, msg ) = self.parser.parse(BMP_message(bmp_msg))
        if msg_type == BMP_Initiation_Message:
            print("BMP session start")
        elif msg_type == BMP_Termination_Message:
            print("BMP session end")
        else:
            if not peer['hash'] in self.peers:
                self.peers[peer['hash']] = BMP_peer(peer)
            self.peers[peer['hash']].consume(msg_type,bmp_msg)

    def get_next(self,msg):
        tail,bmp_msg = BMP_message.get_next(msg)
        self.process_message(bmp_msg)
        return tail
