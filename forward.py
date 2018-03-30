#!/usr/bin/python3

import yaml
import sys
import pprint
import struct
import string
import ipaddress
from binascii import hexlify
import socket

from kafka import KafkaConsumer
# kafka library installed via 'pip install kafka-python'
# also requires snappy: 'pip install python-snappy'

#refer to ./docs/MESSAGE_BUS_API.md in branch 'caida' of https://github.com/CAIDA/openbmp.git

def parse(msg):
    payload = None
    # print ("kafka header: %s:%d:%d: key=%s" % (msg.topic, msg.partition, msg.offset, msg.key))
    if (0x4F424D50 == struct.unpack_from('!I', msg.value, offset=0)[0]):
        # this is the obmp version 1.7+ binary format
        ## print ("obmp binary format message header")
        majorVersion  = struct.unpack_from('!B', msg.value, offset=4)[0]
        assert(1 == majorVersion)
        minorVersion  = struct.unpack_from('!B', msg.value, offset=5)[0]
        assert(7 == minorVersion)
        headerLength  = struct.unpack_from('!H', msg.value, offset=6)[0]
        messageLength = struct.unpack_from('!I', msg.value, offset=8)[0]
        assert(len(msg.value) == headerLength + messageLength)
        flags         = struct.unpack_from('!B', msg.value, offset=12)[0]
        isIPv6 = bool(0x40 & flags)
        assert(not isIPv6)
        isRouter = bool(0x80 & flags)
        assert(isRouter)
        objectType    = struct.unpack_from('!B', msg.value, offset=13)[0]
        collectionTimestampSeconds = struct.unpack_from('!I', msg.value, offset=14)[0]
        collectionTimestampMicroSeconds = struct.unpack_from('!I', msg.value, offset=18)[0]
        collectionTimestamp= collectionTimestampSeconds + collectionTimestampMicroSeconds / 1000000.0
        collectorHash  = msg.value[22:37]
        collectorAdminIDLength  = struct.unpack_from('!H', msg.value, offset=38)[0]
        if (collectorAdminIDLength):
            collectorAdminID  = msg.value[40:40+collectorAdminIDLength]
        else:
            collectorAdminID = "<NULL>"
        routerHashOffset = 40+collectorAdminIDLength
        routerHash = msg.value[routerHashOffset:routerHashOffset+15]
        routerIPOffset = routerHashOffset+16
        routerIPv4num = struct.unpack_from('!I', msg.value, offset=routerIPOffset)[0]
        routerIPv4 = ipaddress.ip_address(routerIPv4num)
        routerGroupOffset = routerHashOffset+32
        routerGroupLength  = struct.unpack_from('!H', msg.value, offset=routerGroupOffset)[0]
        if (routerGroupLength):
            routerGroup  = msg.value[routerGroupOffset+2:routerGroupOffset+routerGroupLength+2]
        else:
            routerGroup = "<NULL>"
        rowCountOffset = routerGroupOffset+2+routerGroupLength
        rowCount = struct.unpack_from('!I', msg.value, offset=rowCountOffset)[0]
        assert(1==rowCount)
        assert(4 == headerLength-rowCountOffset)

        ## diagnostics prints only

        payload = msg.value[headerLength:]
        header = msg.value[:headerLength-1]
        ## print ("obmp binary header content | %d:%s" % (len(header),hexlify(header)))
        ## print ("obmp binary header values | majorVersion:%d minorVersion:%d headerLength:%d messageLength:%d flags:%x" % (majorVersion,minorVersion,headerLength,messageLength,flags))
        ## print ("obmp binary header values | objectType:%d collectionTimestampSeconds:%d collectionTimestampMicroSeconds:%d collectorHash:%s" % (objectType,collectionTimestampSeconds,collectionTimestampMicroSeconds,hexlify(collectorHash)))
        ## print ("obmp binary header values | collectorAdminID:%s routerHash:%s routerIPv4:%s routerGroup:%s" % (collectorAdminID,hexlify(routerHash),routerIPv4,routerGroup))
        ## print ("obmp binary header payload | %s" % hexlify(payload))

        ## print ("obmp header values | objectType:%d collectionTimestamp:%f collectorAdminID:%s routerIPv4:%s routerGroup:%s payload length:%d" % (objectType,collectionTimestampSeconds,collectorAdminID,routerIPv4,routerGroup,messageLength))

    elif (0x563A == struct.unpack_from('!H', msg.value, offset=0)[0]):
        # this is a obmp legacy text header
        headerLength = string.find(msg.value,'\n\n')
        msgLength = len(msg.value)
        payloadLength = msgLength-headerLength-2
        header = msg.value[:headerLength]
        payload = msg.value[headerLength+2:]
        ## print ("obmp legacy text message header  | %s" % header)
        ## print ("obmp legacy text message payload | %d:%s" % (payloadLength,hexlify(payload)))
        sys.stdout.write('-')
        sys.stdout.flush()
    elif (0x5645 == struct.unpack_from('!H', msg.value, offset=0)[0]):
        # this is a obmp (new format) text header
        ## print ("obmp (new format) text message header | %s" % msg.value)
        sys.stdout.write('+')
        sys.stdout.flush()
    else:
        # unrecognised format!
        h = struct.unpack_from('!H', msg.value, offset=0)[0]
        print ("unrecognised obmp message header | %s (%s)" % (hex(h), hexlify(msg.value)))

    return(payload)

def connect(host,port):

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host,port))
    except socket.error as msg:
        print("Failed to connect to remote target",host,port, msg)
        exit()
    return(sock)

def send(sock,msg):
    try:
        sock.sendall(msg)

    except socket.error as errmsg:
        print("Failed to send message to target", errmsg)
        exit()

def forward(collector,target):
    sock = connect(target['host'],target['port'])

    consumer = KafkaConsumer(bootstrap_servers=collector['bootstrap_servers'],client_id=collector['client_id'],group_id=collector['group_id'])
    consumer.subscribe(topics=collector['topic'])
    print('listening to',collector['bootstrap_servers'], 'for topics',collector['topic'])
    messages_received = 0
    for message in consumer:
        assert message.topic == collector['topic']
        if not messages_received:
            print("first message received")
        sys.stdout.write('.')
        sys.stdout.flush()
        messages_received += 1
        msg = parse(message)
        if (msg):
            send(sock,msg)

with open("config.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile)
    if ('forward' not in cfg):
        sys.exit("could not find section 'forward' in config file")
    else:
        forward_cfg=cfg['forward']
    if ('collector' not in forward_cfg):
        sys.exit("could not find sub-section 'collector' in config file")
    if ('target' not in forward_cfg):
        sys.exit("could not find sub-section 'target' in config file")

    forward(forward_cfg['collector'],forward_cfg['target'])
