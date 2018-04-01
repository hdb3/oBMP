#
# oBMP/parse.py
#
# this parser decapsulaes BMP messages from the openBMP/CAIDA/SNAS.IO formats used over Kafka
# it does not know anyhing about Kafka, nor does it know anything about BMP
# the metadata provided by this encapsulaion is fortunately light, so removing it has very little impact

import sys
import struct
import ipaddress
from binascii import hexlify
def eprint(s):
    sys.stderr.write(s+'\n')

#refer to ./docs/MESSAGE_BUS_API.md in branch 'caida' of https://github.com/CAIDA/openbmp.git

def oBMP_parse(msg):
    payload = None
    if (0x4F424D50 == struct.unpack_from('!I', msg, offset=0)[0]):
        # this is the obmp version 1.7+ binary format
        majorVersion  = struct.unpack_from('!B', msg, offset=4)[0]
        assert(1 == majorVersion)
        minorVersion  = struct.unpack_from('!B', msg, offset=5)[0]
        assert(7 == minorVersion)
        headerLength  = struct.unpack_from('!H', msg, offset=6)[0]
        messageLength = struct.unpack_from('!I', msg, offset=8)[0]
        assert(len(msg) == headerLength + messageLength)
        flags         = struct.unpack_from('!B', msg, offset=12)[0]
        isIPv6 = bool(0x40 & flags)
        assert(not isIPv6)
        isRouter = bool(0x80 & flags)
        assert(isRouter)
        objectType    = struct.unpack_from('!B', msg, offset=13)[0]
        collectionTimestampSeconds = struct.unpack_from('!I', msg, offset=14)[0]
        collectionTimestampMicroSeconds = struct.unpack_from('!I', msg, offset=18)[0]
        collectionTimestamp= collectionTimestampSeconds + collectionTimestampMicroSeconds / 1000000.0
        collectorHash  = msg[22:37]
        collectorAdminIDLength  = struct.unpack_from('!H', msg, offset=38)[0]
        if (collectorAdminIDLength):
            collectorAdminID  = msg[40:40+collectorAdminIDLength]
        else:
            collectorAdminID = "<NULL>"
        routerHashOffset = 40+collectorAdminIDLength
        routerHash = msg[routerHashOffset:routerHashOffset+15]
        routerIPOffset = routerHashOffset+16
        routerIPv4num = struct.unpack_from('!I', msg, offset=routerIPOffset)[0]
        routerIPv4 = ipaddress.ip_address(routerIPv4num)
        routerGroupOffset = routerHashOffset+32
        routerGroupLength  = struct.unpack_from('!H', msg, offset=routerGroupOffset)[0]
        if (routerGroupLength):
            routerGroup  = msg[routerGroupOffset+2:routerGroupOffset+routerGroupLength+2]
        else:
            routerGroup = "<NULL>"
        rowCountOffset = routerGroupOffset+2+routerGroupLength
        rowCount = struct.unpack_from('!I', msg, offset=rowCountOffset)[0]
        assert(1==rowCount)
        assert(4 == headerLength-rowCountOffset)

        ## diagnostics prints only

        payload = msg[headerLength:]
        header = msg[:headerLength-1]
        ## eprint ("obmp binary header content | %d:%s" % (len(header),hexlify(header)))
        ## eprint ("obmp binary header values | majorVersion:%d minorVersion:%d headerLength:%d messageLength:%d flags:%x" % (majorVersion,minorVersion,headerLength,messageLength,flags))
        ## eprint ("obmp binary header values | objectType:%d collectionTimestampSeconds:%d collectionTimestampMicroSeconds:%d collectorHash:%s" % (objectType,collectionTimestampSeconds,collectionTimestampMicroSeconds,hexlify(collectorHash)))
        ## eprint ("obmp binary header values | collectorAdminID:%s routerHash:%s routerIPv4:%s routerGroup:%s" % (collectorAdminID,hexlify(routerHash),routerIPv4,routerGroup))
        ## eprint ("obmp binary header payload | %s" % hexlify(payload))

        ## eprint ("obmp header values | objectType:%d collectionTimestamp:%f collectorAdminID:%s routerIPv4:%s routerGroup:%s payload length:%d" % (objectType,collectionTimestampSeconds,collectorAdminID,routerIPv4,routerGroup,messageLength))

    elif (0x563A == struct.unpack_from('!H', msg, offset=0)[0]):
        # this is a obmp legacy text header
        headerLength = string.find(msg,'\n\n')
        msgLength = len(msg)
        payloadLength = msgLength-headerLength-2
        header = msg[:headerLength]
        payload = msg[headerLength+2:]
        ## eprint ("obmp legacy text message header  | %s" % header)
        ## eprint ("obmp legacy text message payload | %d:%s" % (payloadLength,hexlify(payload)))
        sys.stdout.write('-')
        sys.stdout.flush()
    elif (0x5645 == struct.unpack_from('!H', msg, offset=0)[0]):
        # this is a obmp (new format) text header
        ## eprint ("obmp (new format) text message header | %s" % msg)
        sys.stdout.write('+')
        sys.stdout.flush()
    else:
        # unrecognised format!
        h = struct.unpack_from('!H', msg, offset=0)[0]
        eprint ("unrecognised obmp message header | %s (%s)" % (hex(h), hexlify(msg)))

    return(payload)
