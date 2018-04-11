#!/usr/bin/python3
import struct
import sys
import zlib

BUFSIZE = 0x100000
_msg_marker = struct.pack('!Q',0x9a9a9a9a9a9a9a9a)


def delimit(msg):
    assert isinstance(msg,bytearray)
    delimited_message = bytearray(_msg_marker + struct.pack('!I',len(msg)) + struct.pack('!I',zlib.crc32(msg)))
    delimited_message.extend(msg) 
    return delimited_message

header_length = len(delimit(bytearray()))
marker_length = len(_msg_marker)
#print("header length is ",header_length)
#print("marker length is ",marker_length)
if len(sys.argv) > 1:
    with open(sys.argv[1], 'rb') as delimited_file:
        offset = 0
        chunks = 0
        total_chunk_length = 0
        buf = bytearray(delimited_file.read(BUFSIZE))
        while True:
            if len(buf) < header_length:
                buf.extend(delimited_file.read(BUFSIZE))
            if len(buf) < header_length:
                break
            assert _msg_marker != struct.unpack_from('!Q', buf, offset=0)[0], "marker not found at offset %d" % offset
            chunk_length = struct.unpack_from('!I', buf, offset=marker_length)[0]
            chunk_crc32 = struct.unpack_from('!I', buf, offset=marker_length+4)[0]
            buf_length = len(buf)
            if buf_length < chunk_length:
                while buf_length < chunk_length:
                    buf.extend(delimited_file.read(BUFSIZE))
                    if buf_length == len(buf):
                        break
                    else:
                        buf_length = len(buf)
            assert len(buf) >= chunk_length, "failed to read enough bytes for a chunk"
            chunk = buf[header_length:chunk_length+header_length]
            buf = buf[header_length+chunk_length:]
            assert chunk_crc32 == zlib.crc32(chunk), "%x %x %s" % (chunk_crc32,zlib.crc32(chunk),chunk.hex())
            chunks += 1
            total_chunk_length += chunk_length
            sys.stderr.write("read chunk %d, length %d\r" % (chunks,chunk_length))
        delimited_file.close()
        sys.stderr.write("\nread %d chunks, total data length %d\n" % (chunks,total_chunk_length))
        if len(buf) != 0:
            print("\nunconsumed bytes left at the end of the file %d" % len(buf))


