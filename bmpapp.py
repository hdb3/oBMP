#
#

import struct
import sys
import bmpparse
import bgpparse
import BGPribdb
import pprint
import capabilitycodes
import time
from ipaddress import ip_address


logfile=sys.stdout
def eprint(s):
    logfile.write(s+'\n')
    logfile.flush()
    return

class BmpContext():


    def __init__(self,name):
        self.name = name
        ts = str(time.time())
        self.dump_file = open("dump/" + self.name + "-bmp-context-except-" + ts + ".bmp","wb")
        self.peers = {}

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

        print("BMP Peer Data")
        print('local address %s:%d' % (peer_up['local_address'], peer_up['local_port']))
        print('remote address %s:%d' % (self.peers[peer_hash]['remote_IPv4_address'], peer_up['remote_port']))
        print("BMP Peer Data - BGP OPEN Data - ## TODO ##")

    def update_peer(self,msg):
        print("updating peer record from Peer Up Notification message")
        self._update_peer(msg)

    def new_peer(self,msg):
        peer_hash = msg.bmp_ppc_fixed_hash
        assert peer_hash not in self.peers
        ph = {}
        ph['name']     = self.name
        ph['remote_IPv4_address'] = ip_address(msg.bmp_ppc_IP4_Peer_Address)
        ph['remote_AS']           = msg.bmp_ppc_Peer_AS
        ph['Peer_Type']           = msg.bmp_ppc_Peer_Type
        ph['Peer_Flags']          = msg.bmp_ppc_Peer_Flags
        ph['Peer_Distinguisher']  = msg.bmp_ppc_Peer_Distinguisher 
        ph['Peer_BGPID']          = ip_address(msg.bmp_ppc_Peer_BGPID)

        ph['rib'] = BGPribdb.BGPribdb(ph['name'], ph['remote_IPv4_address'], ph['remote_AS'], ph['Peer_BGPID'])

        self.peers[peer_hash] = ph

        if msg.msg_type == bmpparse.BMP_Peer_Up_Notification:
            print("creating peer record from Peer Up Notification message")
            self._update_peer(msg)
        else:
            print("creating peer record from other (non-Peer Up) BMP message")

    def parse(self,msg):
        self.dump_file.write(msg.msg)
        self.dump_file.flush()
        if msg.msg_type == bmpparse.BMP_Initiation_Message:
            print("-- ID:%s - BMP Initiation Message rcvd" % self.name)
        elif msg.msg_type == bmpparse.BMP_Termination_Message:
            print("-- ID:%s - BMP Termination Message rcvd" % self.name)
        else:
            peer_hash = msg.bmp_ppc_fixed_hash
            new_peer_flag = (peer_hash not in self.peers)
            if new_peer_flag:
                self.new_peer(msg)
                print("-- ID:%s - new peer recognised" % self.name)
                print("-- ID:%s - new BMP peer: remote address %s" % (self.name,ip_address(msg.bmp_ppc_IP4_Peer_Address)))
                print("-- ID:%s - new BMP peer: remote AS %d" % (self.name,msg.bmp_ppc_Peer_AS))
                print("-- ID:%s - new BMP peer: peer BGPID %s" % (self.name,ip_address(msg.bmp_ppc_Peer_BGPID)))

            if msg.msg_type == bmpparse.BMP_Peer_Up_Notification:
                peer_up_received = ('Peer_Up_data' in self.peers[peer_hash])

                print("-- ID:%s - BMP Peer Up rcvd - AS%d at %s:%d" % (self.name,msg.bmp_ppc_Peer_AS,ip_address(msg.bmp_ppc_IP4_Peer_Address), msg.bmp_peer_up_remote_port))

                if new_peer_flag:
                    print("-- ID:%s - BMP Peer Up rcvd for new peer" % self.name)
                    self.update_peer(msg)
                elif peer_up_received:
                    print("-- ID:%s - BMP Peer Up (repeat)" % self.name)
                    # could check if the peer up data has changed since the previous update....
                    # self.check_peer(msg)
                else:
                    print("-- ID:%s - BMP Peer Up rcvd for peer configured on other data" % self.name)


                ##print(msg)
                ##sent_open = bgpparse.BGP_message(msg.bmp_peer_up_sent_open)
                ##print("capability codes in sent_open")
                ##pprint.pprint(sent_open.bgp_open_optional_parameters)
                ##for p in sent_open.bgp_open_optional_parameters:
                    ##if p in capabilitycodes.BGP_optional_capability_code_strings:
                        ##print("(%d) : %s" % (p,capabilitycodes.BGP_optional_capability_code_strings[p]))
                    ##else:
                        ##print ("(%d) : unknown capability code" % p)
    
                ##print(sent_open)
                ##rcvd_open = bgpparse.BGP_message(msg.bmp_peer_up_rcvd_open)
                ##print("capability codes in rcvd_open")
                ##for p in rcvd_open.bgp_open_optional_parameters:
                    ##if p in capabilitycodes.BGP_optional_capability_code_strings:
                        ##print("(%d) : %s" % (p,capabilitycodes.BGP_optional_capability_code_strings[p]))
                    ##else:
                        ##print ("(%d) : unknown capability code" % p)
    
                ##pprint.pprint(rcvd_open.bgp_open_optional_parameters)
                ##print(rcvd_open)
            elif msg.msg_type == bmpparse.BMP_Statistics_Report:
                print("-- ID:%s - BMP stats report rcvd" % self.name)
                print(self.peers[peer_hash]['rib'])
            elif msg.msg_type == bmpparse.BMP_Route_Monitoring:
                #print("-- BMP Route Monitoring rcvd, length %d" % msg.length)
                if new_peer_flag:
                    print("-- ID:%s - route monitoring rcvd for new peer" % self.name)
                parsed_bgp_message = bgpparse.BGP_message(msg.bmp_RM_bgp_message)
                if 0 == len(parsed_bgp_message.withdrawn_prefixes) and 0 == len(parsed_bgp_message.prefixes):
                    if 0 == len(parsed_bgp_message.attribute):
                        print("-- ID:%s - End-of-RIB received" % self.name)
                        print(self.peers[peer_hash]['rib'])
                    else:
                        pass
                        #~# print("-- ID:%s - empty update received" % self.name)
                        #~# if bgpparse.BGP_TYPE_CODE_AS_PATH in parsed_bgp_message.attribute:
                            #~# print("AS path: ", parsed_bgp_message.attribute[bgpparse.BGP_TYPE_CODE_AS_PATH])
                        #~# else:
                            #~# print(parsed_bgp_message.attribute)
                    ## print(parsed_bgp_message.attribute)
                if parsed_bgp_message.except_flag:
                    eprint("except during parsing at message no %d" % n)
                else:
                    self.peers[peer_hash]['rib'].update(parsed_bgp_message.attribute,parsed_bgp_message.prefixes)
                    self.peers[peer_hash]['rib'].withdraw(parsed_bgp_message.withdrawn_prefixes)
            else:
                eprint("-- BMP non RM rcvd, BmP msg type was %d, length %d\n" % (msg.msg_type,msg.length))
