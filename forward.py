#!/usr/bin/python3

#
# forwarder
# this is a Kafka consumer, speciallised to the role of fetching BMP data from an openBMP clooector cluster
# this instance can parse messages and forward them over a TCP connection
#

import yaml
import sys
import pprint
import struct
import string
import ipaddress
from binascii import hexlify
import socket

from oBMPparse import oBMP_parse

# kafka library and snappy installed via 'pip install kafka-python python-snappy'

from kafka import KafkaConsumer

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
        msg = oBMP_parse(message.value)
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
