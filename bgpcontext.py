

# bgpcontext.py

from BGPribdb import BGPribdb
import bgppeel
from bgpmsg import BGP_message,BGP_OPEN,BGP_KEEPALIVE,BGP_UPDATE,BGP_NOTIFICATION
from bgpopen import BGP_OPEN_message
from bgpupdate import BGP_UPDATE_message
from ipaddress import IPv4Address
from BGPribdb import BGPribdb

class BGP_context:

    def __init__(self, peer_data):
        self.peer_data = peer_data
        self.peer_string = "AS%d:%s" % (peer_data['remote_AS'], peer_data['remote_address'])
        print("BGP context: new peer connected %s" % self.peer_string)
        self.adjrib = BGPribdb(self.peer_string, peer_data['remote_address'] , peer_data['remote_AS'], peer_data['remote_address'])
            
    def consume(self, msg):
            bgp_msg = BGP_message(msg)
            msg_type = bgp_msg.bgp_type
            #bgp_payload = bgp_msg[19:]
            if msg_type == BGP_KEEPALIVE:
                print("BGP KEEPALIVE rcvd")
            elif msg_type == BGP_NOTIFICATION:
                print("BGP NOTIFY rcvd")
            elif msg_type == BGP_OPEN:
                print("BGP OPEN rcvd")
                parsed_open_msg = BGP_OPEN_message.parse(bgp_msg.payload)
                print(parsed_open_msg)
                ##self.adjrib = BGPribdb(self.name, IPv4Address(self.remote_address[0]), parsed_open_msg.AS, parsed_open_msg.bgp_id)
            elif msg_type == BGP_UPDATE:
                # print("BGP UPDATE rcvd")
                update = BGP_UPDATE_message.parse(bgp_msg.payload)
                if update.except_flag:
                    print("exception")
                    print(update)
                elif update.end_of_rib:
                    print("BGP UPDATE END_OF_RIB rcvd")
                    print(self.adjrib)
                else:
                    self.adjrib.update(update.path_attributes,update.prefixes)
                    self.adjrib.withdraw(update.withdrawn_prefixes)
