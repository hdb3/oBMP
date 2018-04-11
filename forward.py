#!/usr/bin/python3

#
# forwarder
# this is a Kafka consumer, speciallised to the role of fetching BMP data from an openBMP clooector cluster
# this instance can parse messages and forward them over a TCP connection
#

import yaml
import struct
import sys
import os
import socket
import threading
import time
import pprint

from oBMPparse import oBMP_parse
import bmpparse
import bmpapp
import topic

# kafka library and snappy installed via 'pip install kafka-python python-snappy'
# snappy also requires dev headers - apt install libsnappy-dev
# For mixed python2/python3 systems use pip3 not pip, from package python3-pip

from kafka import KafkaConsumer


Initialising = 1
Connecting = 2
Connected = 3
Error = 4
Retrying = 5
Connected = 6
Disconnected = 7

class Forwarder(threading.Thread):

    def __init__(self,host,port):
        threading.Thread.__init__(self)
        self.daemon = True
        self.state = Initialising
        self.connections = 0
        self.event = threading.Event()
        self.address = (host,port)

    def run(self):
        while True:
            self.state = Connecting
            if self.connections == 0:
                sys.stderr.write("attempting connection to %s:%d\n" % self.address)
            else:
                sys.stderr.write("reattempting connection to %s:%d\n" % self.address)
            while self.state != Connected:
                try:
                    self.sock = socket.create_connection(self.address,1)
                except (socket.herror,socket.gaierror) as e:
                    sys.stderr.write("unrecoverable error %s" % e + " connecting to %s:%d\n" % self.address)
                    self.state = Error
                    sys.exit()
                except (socket.error,socket.timeout) as e:
                    self.last_socket_error = e
                    self.state = Retrying
                    time.sleep(1)
                    continue
                except Exception as e:
                    sys.stderr.write("unknown error %s" % e + " connecting to %s:%d\n" % self.address)
                    self.state = Error
                    sys.exit()

                self.state = Connected
                self.connections += 1
                sys.stderr.write("connected to %s:%d\n" % self.address)
                self.event.clear()
                self.event.wait()
                self.event.clear()

    def send(self,msg):
        if self.state != Connected:
            sys.stderr.write('-')
            sys.stderr.flush()
        else:
            try:
                self.sock.sendall(msg)

            except socket.error as errmsg:
                if self.is_alive():
                    self.state = Disconnected
                    sys.stderr.write('!')
                    sys.stderr.flush()
                    self.event.set()
                    return
                else:
                    sys.stderr.write("socket manager has exited\n")
                    self.state = Error
                    sys.exit()
            sys.stderr.write('+')
            sys.stderr.flush()

max_ribsize = 0

msg_marker = struct.pack('!Q',0x9a9a9a9a9a9a9a9a)
def delimit(msg):
    assert isinstance(msg,bytearray)
    header = bytestring(marker + struct.pack('!I',len(msg)) + struct.pack('!I',zlib.crc32(msg)))
    return header.extend(msg) 

def forward(collector,target):
    forwarder = Forwarder(target['host'],target['port'])
    forwarder.start()

    consumer = KafkaConsumer(bootstrap_servers=collector['bootstrap_servers'],client_id=collector['client_id'],group_id=collector['group_id'])

    if 'pattern' in collector:
        if (collector['pattern'] in ('*','all')):
            pattern = '.*'
        else:
            pattern = collector['pattern']
        consumer.subscribe(pattern=pattern)
        sys.stderr.write("listening to %s for pattern %s\n" % (collector['bootstrap_servers'], pattern))
    elif 'topics' in collector:
        consumer.subscribe(topics=collector['topics'])
        topics = ','.join(collector['topics'])
        sys.stderr.write("listening to %s for topics %s\n" % (collector['bootstrap_servers'], topics))
    else:
        sys.stderr.write("error - neither topics nor pattern defined")

    messages_received = 0
    current_topics = {}

    for message in consumer:
        messages_received += 1
        #assert message.topic == collector['topic']
        if message.topic not in current_topics:
            current_topics[message.topic] = topic.Topic(message.topic)

        current_topics[message.topic].process(bytearray(message.value))
        #self.send(msg)

        sys.stderr.write("message rcvd %d\r" % messages_received)
        sys.stderr.flush()

    current_topics[message.topic].exit()

if len(sys.argv) > 1:
    config_file = sys.argv[1]
else:
    config_file = "forward.yml"

with open(config_file, 'r') as ymlfile:
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
