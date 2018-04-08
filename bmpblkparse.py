# bmpblkparse.py
#
# unblock BMP from a message stream
#

import struct
import sys
def eprint(s):
    return
    sys.stderr.write(s+'\n')
    sys.stderr.flush()

class BMP_unblocker:

    def __init__(self,parse=False):
        self.parse = parse
        self.msg_tail = bytearray()
        self.bytes_processed = 0
        self.blocks_processed = 0

    @staticmethod
    def bmp_message_type(msg):
        return struct.unpack_from('!B', msg, offset=5)[0]

    def push(self,new_msg,parse=False):
    
        msg = self.msg_tail + new_msg
        eprint("BMP_unblocker: processing block %d bytes processed %d" % (self.blocks_processed,self.bytes_processed))
    
        msg_len  = len(msg)
        offset = 0
        bmp_msgs = []
        sub_block = 0
        while offset < msg_len - 5:
            version  = struct.unpack_from('!B', msg, offset=offset)[0]
            length   = struct.unpack_from('!I', msg, offset=offset+1)[0]
            msg_type = struct.unpack_from('!B', msg, offset=offset+5)[0]
            assert 3 == version, "failed version check, expected 3 got %x offset %d+%d" % (version,self.bytes_processed,offset)
            assert msg_type < 7, "failed message type check, expected < 7, got %x" % msg_type
    
            eprint("BMP_unblocker: processing sub-block %d in block %d BMP msg type %d BMP msg length %d offset %d" % (sub_block,self.blocks_processed,msg_type,length,offset))
    
            if msg_len >= length + offset:
                if self.parse:
                    bmp_msgs.append(BMP_message(msg[offset:offset+length]))
                else:
                    bmp_msgs.append(msg[offset:offset+length])
                offset += length
                sub_block +=1
                continue
            elif msg_len == offset + length:
                self.msg_tail = bytearray()
                eprint("BMP_unblocker: exit push with zero bytes unprocessed")
                break
            else:
                self.msg_tail = msg[offset:]
                eprint("BMP_unblocker: exit push with %d bytes unprocessed" % len(self.msg_tail) )
                break
    
        self.bytes_processed += len(new_msg)
        self.blocks_processed += 1
        eprint("BMP_unblocker: finished processing block %d, %d bytes processed, %d BMP messages returned" % (self.blocks_processed,self.bytes_processed,len(bmp_msgs)))
        return bmp_msgs
