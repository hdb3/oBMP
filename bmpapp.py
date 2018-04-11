#
#

import struct
import sys
import bmpparse
import bgpparse
import BGPribdb
import pprint
import capabilitycodes


logfile=sys.stdout
def eprint(s):
    logfile.write(s+'\n')
    logfile.flush()
    return

class BmpContext:

    def __init__(self):
        self.rib = BGPribdb.BGPribdb()

    def parse(self,msg):
        if msg.msg_type == bmpparse.BMP_Initiation_Message:
            print("-- BMP Initiation Message rcvd, length %d" % msg.length)
            ##print(msg)
        elif msg.msg_type == bmpparse.BMP_Peer_Up_Notification:
            print("-- BMP Peer Up rcvd, length %d" % msg.length)
            ##print(msg)
            sent_open = bgpparse.BGP_message(msg.bmp_peer_up_sent_open)
            print("capability codes in sent_open")
            ##pprint.pprint(sent_open.bgp_open_optional_parameters)
            for p in sent_open.bgp_open_optional_parameters:
                if p in capabilitycodes.BGP_optional_capability_code_strings:
                    print("(%d) : %s" % (p,capabilitycodes.BGP_optional_capability_code_strings[p]))
                else:
                    print ("(%d) : unknown capability code" % p)

            ##print(sent_open)
            rcvd_open = bgpparse.BGP_message(msg.bmp_peer_up_rcvd_open)
            print("capability codes in rcvd_open")
            for p in rcvd_open.bgp_open_optional_parameters:
                if p in capabilitycodes.BGP_optional_capability_code_strings:
                    print("(%d) : %s" % (p,capabilitycodes.BGP_optional_capability_code_strings[p]))
                else:
                    print ("(%d) : unknown capability code" % p)

            ##pprint.pprint(rcvd_open.bgp_open_optional_parameters)
            ##print(rcvd_open)
        elif msg.msg_type == bmpparse.BMP_Statistics_Report:
            print("-- BMP stats report rcvd, length %d" % msg.length)
            print(self.rib)
        elif msg.msg_type == bmpparse.BMP_Route_Monitoring:
            #print("-- BMP Route Monitoring rcvd, length %d" % msg.length)
            parsed_bgp_message = bgpparse.BGP_message(msg.bmp_RM_bgp_message)
            if 0 == len(parsed_bgp_message.withdrawn_prefixes) and 0 == len(parsed_bgp_message.prefixes):
                print("End-ofRIB received")
                print(self.rib)
                print(parsed_bgp_message.attribute)
            self.rib.withdraw(parsed_bgp_message.withdrawn_prefixes)
            if parsed_bgp_message.except_flag:
                eprint("except during parsing at message no %d" % n)
            else:
                self.rib.update(parsed_bgp_message.attribute,parsed_bgp_message.prefixes)
        else:
            eprint("-- BMP non RM rcvd, BmP msg type was %d, length %d\n" % (msg.msg_type,msg.length))