#!/usr/bin/env python

# simple collector
# minimal colector of CAIDA openBMP service
#

import sys
from ipaddress import IPv4Address
import yaml

from oBMPparse import oBMP_parse
import bmpparse
import bmpapp

from kafka import KafkaConsumer

if len(sys.argv) > 1:
    config_file = sys.argv[1]
else:
    config_file = "simple.yml"

with open(config_file, 'r') as ymlfile:
    cfg = yaml.load(ymlfile)
    if 'collector' not in cfg:
        sys.exit("could not find section 'collector' in config file")
    else:
        config = cfg['collector']

remote_peer_address = IPv4Address(config['remote peer address'])

parser = bmpapp.BmpContext(remote_peer_address)

print('Kafka connection to %s)' % config['bootstrap_servers'])
consumer = KafkaConsumer(bootstrap_servers=config['bootstrap_servers'], client_id=config['client_id'], group_id=config['group_id'])
consumer.subscribe(topics=config['topic'])
print('Kafka subscription (3) to %s)' % subscription)
print('Kafka starting message loop)')
m = 0
n = 0
for message in consumer:
    print('Kafka in message loop)')
    raw_bmp_message = oBMP_parse(message)
    raw_bmp_message, bmp_msg = bmpparse.BMP_message.get_next(raw_bmp_message)
    while bmp_msg:
        parser.parse(bmpparse.BMP_message(bmp_msg))
        raw_bmp_message, bmp_msg = bmpparse.BMP_message.get_next(raw_bmp_message)
        n += 1
    assert 0 == len(raw_bmp_message)
    m += 1
    sys.stderr.write('\rmessage %d (%d)' % (m, n))
