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

class BmpBlkParser():

    def __init__(self,getter):
        self.file_buffer = bytearray()
        self.rib = BGPribdb.BGPribdb()
        self.getter = getter
        self.file_buffer.extend(getter())

    def bytes_available(self):
        return 0xffff
        ##return len(self.file_buffer)

    def peek(self,length):
        while length > len(self.file_buffer):
            msg = self.getter()
            self.file_buffer.extend(msg)
        return self.file_buffer[:length]

    def push(self,msg):
        self.file_buffer.extend(msg)

    def get(self,size):
        #eprint("get")
        while size > len(self.file_buffer):
            #eprint("get more")
            msg = self.getter()
            if 0 == len(msg):
                break
            else:
                self.file_buffer.extend(msg)
        rbuff = self.file_buffer[:size]
        self.file_buffer = self.file_buffer[size:]
        return rbuff
            
    def parse(self,msg):
        bmpmsg = bmpparse.BMP_message(msg)
        msg_type = bmpmsg.msg_type
        msg_length = bmpmsg.length
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

    
    def get_bmp_message(self):
        #eprint("get_bmp_message")
        hdr = self.get(6)
        if len(hdr) < 6:
            return bytearray()
        version  = struct.unpack_from('!B', hdr, offset=0)[0]
        length   = struct.unpack_from('!I', hdr, offset=1)[0]
        msg_type = struct.unpack_from('!B', hdr, offset=5)[0]
        assert 3 == version, "failed version check, expected 3 got %x offset %d+%d" % (version,self.bytes_processed,offset)
        assert msg_type < 7, "failed message type check, expected < 7, got %x" % msg_type
        payload = self.get(length-6)
        if len(payload) < length-6:
            return bytearray()
        hdr.extend(payload)
        return hdr

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
    parser = BmpBlkParser(lambda : f.read(4096))
    msg = parser.get_bmp_message()
    while msg:
        n += 1
        parser.parse(msg)
        msg = parser.get_bmp_message()

print("%d messages processed" % n)
print(parser.rib)
