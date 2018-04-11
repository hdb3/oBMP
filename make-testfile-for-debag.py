#!/usr/bin/python3
import struct
import sys
import zlib
import random

_msg_marker = struct.pack('!Q',0x9a9a9a9a9a9a9a9a)


def delimit(msg):
    assert isinstance(msg,bytearray)
    delimited_message = bytearray(_msg_marker + struct.pack('!I',len(msg)) + struct.pack('!I',zlib.crc32(msg)))
    #print("header %s" % delimited_message.hex(),file=sys.stderr)
    #print("msg %s" % msg.hex(),file=sys.stderr)
    delimited_message.extend(msg) 
    #print("delimited_message %s" % delimited_message.hex(),file=sys.stderr)
    return delimited_message

if len(sys.argv) > 1:
    length = int(sys.argv[1])
else:
    length = 100

rand = open('/dev/urandom','rb')

# # chunk = bytearray(_msg_marker)
# # delimited_chunk = delimit(chunk)
# # #print("delimited_message %s" % delimited_chunk.hex(),file=sys.stderr)
# # sys.stdout.buffer.write(delimited_chunk)
# # sys.stdout.buffer.flush()
# # sys.stdout.close()
# # exit()

for n in range(length):
    chunk = bytearray(rand.read(random.randrange(4096)))
    sys.stdout.buffer.write(delimit(chunk))
