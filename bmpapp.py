#
#

import struct
import sys
import bmpparse
import bgpmsg
#import BGPribdb
import pprint
import capabilitycodes
import time
from ipaddress import IPv4Address


logfile=sys.stdout

class BmpContext():

    def log(self,s):
        logfile.write('-- BMPAPP - ID:' + self.name + ' - ' + s + '\n')
        #logfile.flush()
        return


    def __init__(self,peer):
        self.name = str(peer)
        self.peer = peer
        ts = str(time.time())
        self.dump_file = open("dump/" + self.name + "-bmp-context-except-" + ts + ".bmp","wb")
        self.peers = {}
        self.msg_stats = {}

    def _update_peer(self,msg):
        peer_hash = msg.bmp_ppc_fixed_hash
        assert peer_hash in self.peers
        assert msg.msg_type == bmpparse.BMP_Peer_Up_Notification
        peer_up = {}
        peer_up['local_address'] = IPv4Address(msg.bmp_peer_up_local_address)
        peer_up['local_port'] = msg.bmp_peer_up_local_port
        peer_up['remote_port'] =  msg.bmp_peer_up_remote_port
        peer_up['sent_open'] = msg.bmp_peer_up_sent_open
        peer_up['rcvd_open'] = msg.bmp_peer_up_rcvd_open
        

        if hasattr(msg,'bmp_peer_up_information'):
            peer_up['information'] = msg.bmp_peer_up_information

        self.peers[peer_hash]['Peer_Up_data'] = peer_up

    def update_peer(self,msg):
        self.log("updating peer record from Peer Up Notification message")
        self._update_peer(msg)

    def new_peer(self,msg):
        peer_hash = msg.bmp_ppc_fixed_hash
        assert peer_hash not in self.peers
        ph = {}
        ph['name']     = self.name
        ph['remote_IPv4_address'] = IPv4Address(msg.bmp_ppc_IP4_Peer_Address)
        ph['remote_AS']           = msg.bmp_ppc_Peer_AS
        ph['Peer_Type']           = msg.bmp_ppc_Peer_Type
        ph['Peer_Flags']          = msg.bmp_ppc_Peer_Flags
        ph['Peer_Distinguisher']  = msg.bmp_ppc_Peer_Distinguisher 
        ph['Peer_BGPID']          = IPv4Address(msg.bmp_ppc_Peer_BGPID)

        ###ph['rib'] = BGPribdb.BGPribdb(ph['name'], ph['remote_IPv4_address'], ph['remote_AS'], ph['Peer_BGPID'])

        self.peers[peer_hash] = ph

        if msg.msg_type == bmpparse.BMP_Peer_Up_Notification:
            self.log("creating peer record from Peer Up Notification message")
            self._update_peer(msg)
        else:
            self.log("creating peer record from other (non-Peer Up) BMP message")

    def parse(self,msg):
        try:
            self.dump_file.write(msg.msg)
            self.dump_file.flush()
            if msg.msg_type == bmpparse.BMP_Initiation_Message:
                self.msg_stats['BMP_init'] += 1
                self.log("BMP Initiation Message rcvd")
                return (msg.msg_type, None)
            elif msg.msg_type == bmpparse.BMP_Termination_Message:
                self.msg_stats['BMP_termination'] += 1
                self.log("BMP Termination Message rcvd")
                return (msg.msg_type, None)
            else:
                peer_hash = msg.bmp_ppc_fixed_hash
                new_peer_flag = (peer_hash not in self.peers)
                if new_peer_flag:
                    self.new_peer(msg)
                    self.log("new peer recognised")
                def _log (s):
                    self.log("%s -- peer: AS%d:%s" % ( s, self.peers[peer_hash]['remote_AS'], self.peers[peer_hash]['remote_IPv4_address']))

                if msg.msg_type == bmpparse.BMP_Peer_Down_Notification:
                    self.msg_stats['BMP_peer_down'] += 1
                    _log("BMP Peer Down rcvd")
    
                    if new_peer_flag:
                        _log("BMP Peer Down rcvd for new peer")
                    return (msg.msg_type, None)

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
                    return (msg.msg_type, None)

                elif msg.msg_type == bmpparse.BMP_Statistics_Report:
                    self.msg_stats['BMP_statistics'] += 1
                    _log("BMP stats report rcvd")
                    return (msg.msg_type, None)
                elif msg.msg_type == bmpparse.BMP_Route_Monitoring:
                    self.msg_stats['BMP_route_monitoring'] += 1
                    if new_peer_flag:
                        _log("route monitoring rcvd for new peer")
                    return (msg.msg_type, msg.bmp_RM_bgp_message)
                    #parsed_bgp_message = bgpmsg.BGP_message(msg.bmp_RM_bgp_message)
                    #update = parsed_bgp_message.parse()
                    #if update.end_of_rib:
                            #self.log("End-of-RIB received")
                    #if update.except_flag:
                        #self.log("except during parsing message")
                else:
                    self.msg_stats['BMP_other'] += 1
                    self.log("BMP non RM rcvd, BMP msg type was %d, length %d\n" % (msg.msg_type,msg.length))
        except KeyError as ke:
            kes = str(ke).strip("'")
            if kes.startswith('BMP_'):
                self.msg_stats[kes] = 1
                #print("handled [%s]" % kes)
            else:
                raise ke
