#!/usr/bin/python3
#
#

import struct
import sys
import bmpparse
import bgpparse
import BGPribdb


def eprint(s):
    sys.stderr.write(s+'\n')
    sys.stderr.flush()
    return

class Spider():

    def __init__(self,fn,bufsiz):
        self.f = open(fn,'rb')
        self.max_rq_size = 0
        self.file_buffer = bytearray()
        self.bufsiz = bufsiz

    def get(self,size):
        if size > self.max_rq_size: 
            self.max_rq_size = size
        while size > len(self.file_buffer):
            more_data = self.f.read(self.bufsiz)
            self.file_buffer.extend(more_data)
            if len(more_data) < self.bufsiz:
                self.eof = True
                break
    
        rbuff = self.file_buffer[:size]
        self.file_buffer = self.file_buffer[size:]
        return rbuff
            
    
    def parse(self):
        
        bmp_msgs = []
        while True:
            hdr = self.get(6)
            if len(hdr) == 0:
                eprint("normal end of file")
                break
            elif len(hdr) < 6:
                eprint("unexpected end of file %d" % len(hdr))
                break
            else:
                version  = struct.unpack_from('!B', hdr, offset=0)[0]
                length   = struct.unpack_from('!I', hdr, offset=1)[0]
                msg_type = struct.unpack_from('!B', hdr, offset=5)[0]
                assert 3 == version, "failed version check, expected 3 got %x offset %d+%d" % (version,self.bytes_processed,offset)
                assert msg_type < 7, "failed message type check, expected < 7, got %x" % msg_type
                #max_length = max(max_length,length)
                payload = self.get(length-6)
                if len(payload) != length - 6:
                    eprint("unexpected end of file in payload %d/%d" % (len(payload),length))
                    break
                msg = hdr + payload 
                bmp_msg = bmpparse.BMP_message(msg)
                #bmp_msgs.append(msg)
                bmp_msgs.append(bmp_msg)
    
        return bmp_msgs

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

spider = Spider(filename,bufsiz)
msgs = spider.parse()
eprint("read %d msgs" % len(msgs))
mxl = 0
mnl = 4096

rib = BGPribdb.BGPribdb()

n=0
for bmpmsg in msgs:
    mxl = max(mxl,bmpmsg.length)
    mnl = min(mxl,bmpmsg.length)
    msg_type = bmpmsg.msg_type
    msg_length = bmpmsg.length
    if msg_type == bmpparse.BMP_Initiation_Message:
        print("-- BMP Initiation Message rcvd, length %d" % msg_length)
    elif msg_type == bmpparse.BMP_Peer_Up_Notification:
        print("-- BMP Peer Up rcvd, length %d" % msg_length)
    elif msg_type == bmpparse.BMP_Statistics_Report:
        print("-- BMP stats report rcvd, length %d" % msg_length)
        ##print(rib)
    elif msg_type == bmpparse.BMP_Route_Monitoring:
        ## print("-- BMP Route Monitoring rcvd, length %d" % msg_length)
        bgpmsg = bmpmsg.bmp_RM_bgp_message
        parsed_bgp_message = bgpparse.BGP_message(bgpmsg)
        rib.withdraw(parsed_bgp_message.withdrawn_prefixes)
        if parsed_bgp_message.except_flag:
            ##forwarder.send(bgpmsg)
            print("except during parsing at message no %d" % n)
        else:
            rib.update(parsed_bgp_message.attribute,parsed_bgp_message.prefixes)
    else:
        sys.stderr.write("-- BMP non RM rcvd, BmP msg type was %d, length %d\n" % (msg_type,msg_length))
    n += 1
    if n > limit:
        exit()

eprint("%d messages processed" % n)
eprint("max length message was %d" % mxl)
eprint("min length message was %d" % mnl)
eprint("max rq size was %d" % spider.max_rq_size)
