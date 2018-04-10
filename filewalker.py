#!/usr/bin/python3
#
#

import struct
import sys
import bmpparse
import bgpparse
import BGPribdb
import pprint
import capabilitycodes
import bmpapp


logfile=sys.stdout
def eprint(s):
    logfile.write(s+'\n')
    logfile.flush()
    return

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
    parser = bmpapp.BmpContext()
    filebuffer = bytearray(f.read(bufsiz))
    r=1
    while True:
        while True:
            #filebuffer,bmp_msg = bmpparse.BMP_message.get_next_parsed(filebuffer)
            filebuffer,bmp_msg = bmpparse.BMP_message.get_next(filebuffer)
            if bmp_msg:
                tmp = bmpparse.BMP_message(bmp_msg)
                parser.parse(tmp)
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
