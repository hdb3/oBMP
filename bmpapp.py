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


logfile=sys.stdout
def eprint(s):
    logfile.write(s+'\n')
    logfile.flush()
    return

class BmpContext():


    def __init__(self,name):
        self.rib = BGPribdb.BGPribdb()
        self.name = name
        ts = str(time.time())
        self.dump_file = open("dump/" + self.name + "-bmp-context-except-" + ts + ".bmp","wb")

    def parse(self,msg):
        if msg.msg_type == bmpparse.BMP_Initiation_Message:
            print("-- ID:%s - BMP Initiation Message rcvd" % self.name)
            self.dump_file.write(msg.msg)
            self.dump_file.flush()
            ##print(msg)
        elif msg.msg_type == bmpparse.BMP_Peer_Up_Notification:
            print("-- ID:%s - BMP Peer Up rcvd" % self.name)
            self.dump_file.write(msg.msg)
            self.dump_file.flush()
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
            print(self.rib)
        elif msg.msg_type == bmpparse.BMP_Route_Monitoring:
            #print("-- BMP Route Monitoring rcvd, length %d" % msg.length)
            parsed_bgp_message = bgpparse.BGP_message(msg.bmp_RM_bgp_message)
            if 0 == len(parsed_bgp_message.withdrawn_prefixes) and 0 == len(parsed_bgp_message.prefixes):
                if 0 == len(parsed_bgp_message.attribute):
                    self.dump_file.write(msg.msg)
                    self.dump_file.flush()
                    print("-- ID:%s - End-of-RIB received" % self.name)
                    print(self.rib)
                else:
                    pass
                    #~# print("-- ID:%s - empty update received" % self.name)
                    #~# if bgpparse.BGP_TYPE_CODE_AS_PATH in parsed_bgp_message.attribute:
                        #~# print("AS path: ", parsed_bgp_message.attribute[bgpparse.BGP_TYPE_CODE_AS_PATH])
                    #~# else:
                        #~# print(parsed_bgp_message.attribute)
                        #~# self.dump_file.write(msg.msg)
                        #~# self.dump_file.flush()
                ## print(parsed_bgp_message.attribute)
            if parsed_bgp_message.except_flag:
                eprint("except during parsing at message no %d" % n)
            else:
                self.rib.update(parsed_bgp_message.attribute,parsed_bgp_message.prefixes)
                self.rib.withdraw(parsed_bgp_message.withdrawn_prefixes)
        else:
            eprint("-- BMP non RM rcvd, BmP msg type was %d, length %d\n" % (msg.msg_type,msg.length))
