#!/usr/bin/python

import sys
from binascii import hexlify

from kafka import KafkaConsumer
# kafka library installed via 'pip install kafka-python'
# also requires snappy: 'pip install python-snappy'

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


collectors =  [ ('caida openBMP',lambda: KafkaConsumer(bootstrap_servers=['bmp.bgpstream.caida.org:9092'],client_id='lancaster_university_UK',group_id='beta-bmp-stream')),
                 # refer to https://bgpstream.caida.org/v2-beta#bmp for the link and description of this service
                ('local openBMP',lambda: KafkaConsumer(bootstrap_servers=['r720:9092']))
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
