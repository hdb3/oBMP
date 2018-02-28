#!/usr/bin/python

import sys
import pprint
import struct
import string
from binascii import hexlify

from kafka import KafkaConsumer
# kafka library installed via 'pip install kafka-python'
# also requires snappy: 'pip install python-snappy'

#refer to ./docs/MESSAGE_BUS_API.md in branch 'caida' of https://github.com/CAIDA/openbmp.git

def parse(msg):
    print ("kafka header: %s:%d:%d: key=%s" % (msg.topic, msg.partition, msg.offset, msg.key))
    if (0x4F424D50 == struct.unpack_from('!I', msg.value, offset=0)[0]):
        # this is the obmp version 1.7+ binary format
        print ("obmp binary format message header | %s:%d:%d: key=%s value=%s" % (msg.topic, msg.partition, msg.offset, msg.key, msg.value))
        pass
    elif (0x563A == struct.unpack_from('!H', msg.value, offset=0)[0]):
        # this is a obmp legacy text header
        headerLength = string.find(msg.value,'\n\n')
        msgLength = len(msg.value)
        payloadLength = msgLength-headerLength-2
        header = msg.value[:headerLength]
        payload = msg.value[headerLength+2:]
        print ("obmp legacy text message header  | %s" % header)
        print ("obmp legacy text message payload | %d:%s" % (payloadLength,hexlify(payload)))
    elif (0x5645 == struct.unpack_from('!H', msg.value, offset=0)[0]):
        # this is a obmp (new format) text header
        print ("obmp (new format) text message header | %s" % msg.value)
    else:
        # unrecognised format!
        h = struct.unpack_from('!H', msg.value, offset=0)[0]
        # print(h, type(h))
        print ("unrecognised obmp message header | %s (%s)" % (hex(h), hexlify(msg.value)))

def listen(name,consumer,topics,verbose=False):
    if (topics[0] in ('*','all')):
        consumer.subscribe(pattern='.*')
    else:
        try:
            consumer.subscribe(topics=topics)
        except ValueError:
            consumer.subscribe(pattern=topics[0])
    print('listening to',name, 'for topics',topics)
    for message in consumer:
        ##print('type of message.value is',type(message.value))
        ##pprint.pprint(message)
        parse(message)
        exit()
        if verbose:
            try:
                print ("%s:%d:%d: key=%s value=%s" % (message.topic, message.partition, message.offset, message.key, message.value))
            except UnicodeDecodeError as e:
                print(e)
                try:
                    print ("%s:%d:%d: key=%s value=%s" % (message.topic, message.partition, message.offset, message.key, message.value.decode('utf-8')))
                except UnicodeDecodeError as e:
                    print(e)
                    print ("%s:%d:%d: key=%s value=%s" % (message.topic, message.partition, message.offset, message.key, hexlify(message.value)))
        else:
            print ("%s:%d:%d: key=%s length=%d" % (message.topic, message.partition, message.offset, message.key, len(message.value)))


collectors =  [
                ('caida openBMP',lambda: KafkaConsumer(bootstrap_servers=['bmp.bgpstream.caida.org:9092'],client_id='lancaster_university_UK',group_id='beta-bmp-stream')),
                 # refer to https://bgpstream.caida.org/v2-beta#bmp for the link and description of this service
                ('local openBMP',lambda: KafkaConsumer(bootstrap_servers=['r720:9092'])),
                ('caida openBMP plain',lambda: KafkaConsumer(bootstrap_servers=['bmp.bgpstream.caida.org:9092'],client_id='lancaster_university_UK')),
                ('bmp-dev.openbmp.org',lambda: KafkaConsumer(bootstrap_servers=['bmp-dev.openbmp.org:9092'],client_id='lancaster_university_UK',group_id='openbmp-file-consumer'))
              ]

def probe(name,consumer):
    print('probing',name, 'for topics')
    for topic in consumer.topics():
        print(topic)

argc = len(sys.argv)

if (1 == argc):
   n=1
   print('target collectors are:')
   for collector in collectors:
      print('%d : %s' % (n,collector[0]))
      n+=1
elif (1 < argc):
    n = int(sys.argv[1])-1
    collector = collectors[n]
    name     = collector[0]
    consumer = collector[1]()
    probe(name,consumer)

if (2 < argc):
    if (sys.argv[-1] in ['-v','-V']):
        topics = sys.argv[2:-1]
        listen(name,consumer,topics,verbose=True)
    else:
        topics = sys.argv[2:]
        listen(name,consumer,topics)
