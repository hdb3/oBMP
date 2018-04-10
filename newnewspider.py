#!/usr/bin/python3
#
#

import struct
import sys
import bmpparse
import bgpparse
import BGPribdb


logfile=sys.stdout
def eprint(s):
    logfile.write(s+'\n')
    logfile.flush()
    return

class BmpContext:

    def __init__(self):
        self.rib = BGPribdb.BGPribdb()

    def parse(self,msg):
        if bmpmsg.msg_type == bmpparse.BMP_Initiation_Message:
            print("-- BMP Initiation Message rcvd, length %d" % msg_length)
        elif bmpmsg.msg_type == bmpparse.BMP_Peer_Up_Notification:
            print("-- BMP Peer Up rcvd, length %d" % msg_length)
        elif bmpmsg.msg_type == bmpparse.BMP_Statistics_Report:
            print("-- BMP stats report rcvd, length %d" % msg_length)
        elif bmpmsg.msg_type == bmpparse.BMP_Route_Monitoring:
            #print("-- BMP Route Monitoring rcvd, length %d" % msg_length)
            parsed_bgp_message = bgpparse.BGP_message(bmpmsg.bmp_RM_bgp_message)
            self.rib.withdraw(parsed_bgp_message.withdrawn_prefixes)
            if parsed_bgp_message.except_flag:
                eprint("except during parsing at message no %d" % n)
            else:
                self.rib.update(parsed_bgp_message.attribute,parsed_bgp_message.prefixes)
        else:
            eprint("-- BMP non RM rcvd, BmP msg type was %d, length %d\n" % (msg_type,msg_length))

if len(sys.argv) > 1:
    filename = sys.argv[1]
else:
    filename = 'dump.bmp'

if len(sys.argv) > 2:
    bufsiz = int(sys.argv[2])
else:
    bufsiz = 4096

if len(sys.argv) > 3:
    limit = int(sys.argv[3])
else:
    limit = 0xffffff

n=0
with open(filename,'rb') as f:
    parser = BmpContext()
    filebuffer = bytearray(f.read(bufsiz))
    r=1
    while True:
        while True:
            #filebuffer,bmp_msg = bmpparse.BMP_message.get_next_parsed(filebuffer)
            filebuffer,bmp_msg = bmpparse.BMP_message.get_next(filebuffer)
            if bmp_msg:
                tmp = bmpparse.BMP_message(bmp_msg)
                #parser.parse(bmp_msg)
                n += 1
            else:
                break
        buf = f.read(bufsiz)
        if 0 == len(buf):
            break
        else:
            filebuffer.extend(buf)
    if 0 != len(filebuffer):
        eprint("parser left %d unconsumed bytes at end of file" % len(filebuffer))

print("%d messages processed" % n)
print("%d blocks read" % n)
print(parser.rib)
