#
#

import sys
import bgplib.bmpparse as bmpparse
import time
from ipaddress import IPv4Address
from logger import *


class BmpContext():

    def log(self,s):
        info(s)

    def __log(self,s):
        logfile.write('-- BMPAPP - ID:' + self.name + ' - ' + s + '\n')
        #logfile.flush()
        return


    def __init__(self,peer):
        self.name = str(peer)
        self.peer = peer
        ts = str(time.time())
        self.peers = {}
        self.msg_stats = {}

    def _update_peer(self,msg):
        peer_hash = msg.bmp_ppc_fixed_hash
        assert peer_hash in self.peers
        assert msg.msg_type == bmpparse.BMP_Peer_Up_Notification
        peer_up = {}
        peer_up['local_address'] = ip_address(msg.bmp_peer_up_local_address)
        peer_up['local_port'] = msg.bmp_peer_up_local_port
        peer_up['remote_port'] =  msg.bmp_peer_up_remote_port
        peer_up['sent_open'] = msg.bmp_peer_up_sent_open
        peer_up['rcvd_open'] = msg.bmp_peer_up_rcvd_open
        

        if hasattr(msg,'bmp_peer_up_information'):
            peer_up['information'] = msg.bmp_peer_up_information

        self.peers[peer_hash]['Peer_Up_data'] = peer_up

    def update_peer(self,msg):
        show("updating peer record from Peer Up Notification message")
        self._update_peer(msg)

    def new_peer(self,msg):
        peer_hash = msg.bmp_ppc_fixed_hash
        assert peer_hash not in self.peers
        ph = {}
        ph['name']     = self.name
        ph['hash']     = peer_hash
        ph['remote_address']      = msg.bmp_ppc_Peer_Address
        ph['remote_AS']           = msg.bmp_ppc_Peer_AS
        ph['Peer_Type']           = msg.bmp_ppc_Peer_Type
        ph['AS4_flag']          = msg.bmp_ppc_Peer_Flags_AS4
        ph['IPv6_flag']          = msg.bmp_ppc_Peer_Flags_IPv6
        ph['Peer_Distinguisher']  = msg.bmp_ppc_Peer_Distinguisher 
        ph['Peer_BGPID']          = IPv4Address(msg.bmp_ppc_Peer_BGPID)

        self.peers[peer_hash] = ph

        if msg.msg_type == bmpparse.BMP_Peer_Up_Notification:
            show("creating peer record from Peer Up Notification message")
            self._update_peer(msg)
        else:
            show("creating peer record from other (non-Peer Up) BMP message")

    def get_peer(self, hash):
        return self.peers[hash]

    def parse(self,msg):
        try:
            peer_hash = None
            msg_type = msg.msg_type
            rmsg = None
            if msg.msg_type == bmpparse.BMP_Initiation_Message:
                self.msg_stats['BMP_init'] += 1
                show("BMP Initiation Message rcvd")
            elif msg.msg_type == bmpparse.BMP_Termination_Message:
                self.msg_stats['BMP_termination'] += 1
                show("BMP Termination Message rcvd")
            else:
                peer_hash = msg.bmp_ppc_fixed_hash
                new_peer_flag = (peer_hash not in self.peers)
                if new_peer_flag:
                    self.new_peer(msg)
                    show("new peer recognised")

                def _log (s):
                    show("%s -- peer: AS%d:%s" % ( s, self.peers[peer_hash]['remote_AS'], self.peers[peer_hash]['remote_address']))

                def _info (s):
                    info("%s -- peer: AS%d:%s" % ( s, self.peers[peer_hash]['remote_AS'], self.peers[peer_hash]['remote_address']))

                if msg.msg_type == bmpparse.BMP_Peer_Down_Notification:
                    self.msg_stats['BMP_peer_down'] += 1
                    _log("BMP Peer Down rcvd")
    
                    if new_peer_flag:
                        _log("BMP Peer Down rcvd for new peer")

                elif msg.msg_type == bmpparse.BMP_Peer_Up_Notification:
                    self.msg_stats['BMP_peer_up'] += 1
                    peer_up_received = ('Peer_Up_data' in self.peers[peer_hash])

                    _log("BMP Peer Up rcvd")
    
                    if new_peer_flag:
                        _log("BMP Peer Up rcvd for new peer")
                        self.update_peer(msg)
                    elif peer_up_received:
                        _log("BMP Peer Up (repeat)")
                        _log("BMP Peer Up rcvd for peer configured on other data")

                elif msg.msg_type == bmpparse.BMP_Statistics_Report:
                    self.msg_stats['BMP_statistics'] += 1
                    _info("BMP stats report rcvd")

                elif msg.msg_type == bmpparse.BMP_Route_Monitoring:
                    rmsg = msg.bmp_RM_bgp_message
                    self.msg_stats['BMP_route_monitoring'] += 1
                    if new_peer_flag:
                        _log("route monitoring rcvd for new peer")

                else:
                    self.msg_stats['BMP_other'] += 1
                    self.log("BMP non RM rcvd, BMP msg type was %d, length %d\n" % (msg.msg_type,msg.length))
                    return (None, None, None)
        except KeyError as ke:
            kes = str(ke).strip("'")
            if kes.startswith('BMP_'):
                self.msg_stats[kes] = 1
                #print("handled [%s]" % kes)
            else:
                raise ke
        return (msg_type, self.get_peer(peer_hash), rmsg)
