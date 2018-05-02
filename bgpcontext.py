

# bgpcontext.py

from ipaddress import IPv4Address
from bgplib.BGPribdb import BGPribdb
from bgplib.bgpmsg import BGP_message,BGP_OPEN,BGP_KEEPALIVE,BGP_UPDATE,BGP_NOTIFICATION
from bgplib.bgpopen import BGP_OPEN_message
from bgplib.bgpupdate import BGP_UPDATE_message

class BGP_context:

    def __init__(self, peer_data):
        self.peer_data = peer_data
        self.peer_string = "AS%d:%s" % (peer_data['remote_AS'], peer_data['remote_address'])
        show("BGP context: new peer connected %s" % self.peer_string)
        self.adjrib = BGPribdb(self.peer_string, peer_data['remote_address'] , peer_data['remote_AS'], peer_data['remote_address'])
            
    def consume(self, msg):
            bgp_msg = BGP_message(msg)
            msg_type = bgp_msg.bgp_type
            #bgp_payload = bgp_msg[19:]
            if msg_type == BGP_KEEPALIVE:
                show("BGP KEEPALIVE rcvd")
            elif msg_type == BGP_NOTIFICATION:
                show("BGP NOTIFY rcvd")
            elif msg_type == BGP_OPEN:
                show("BGP OPEN rcvd")
                parsed_open_msg = BGP_OPEN_message.parse(bgp_msg.payload)
                show(parsed_open_msg)
                ##self.adjrib = BGPribdb(self.name, IPv4Address(self.remote_address[0]), parsed_open_msg.AS, parsed_open_msg.bgp_id)
            elif msg_type == BGP_UPDATE:
                # show("BGP UPDATE rcvd")
                update = BGP_UPDATE_message.parse(bgp_msg.payload)
                if update.except_flag:
                    show("exception")
                    show(update)
                elif update.end_of_rib:
                    show("BGP UPDATE END_OF_RIB rcvd")
                    show(self.adjrib)
                else:
                    self.adjrib.update(update.path_attributes,update.prefixes)
                    self.adjrib.withdraw(update.withdrawn_prefixes)

def new_headless_context():
    peer_data = {}
    peer_data['remote_AS'] = "99999"
    peer_data['remote_address'] = IPv4Address("0.0.0.0")
    return BGP_context(peer_data)
