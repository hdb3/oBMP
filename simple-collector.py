#!/usr/bin/env python

import sys
import yaml
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
from oBMPparse import oBMP_parse

from bmpcontext import BMP_process

if len(sys.argv) > 1:
    config_file = sys.argv[1]
else:
    config_file = "vsimple.yml"

ymlfile = open(config_file, 'r')
config = yaml.load(ymlfile)
_bootstrap_servers = config['bootstrap_servers']
_client_id = config['client_id']
_group_id = config['group_id']
_topic = config['topic']
if 'name' in config:
    _name = config['name']
else:
    _name = _topic
while True:
    try:
        consumer=KafkaConsumer( _topic, api_version_auto_timeout_ms = 1000, request_timeout_ms = 1000, bootstrap_servers=_bootstrap_servers, client_id=_client_id)
        break
    except NoBrokersAvailable:
        print("retrying connection to Kafka broker")

bmp_process = BMP_process(_name)

try:
    for message in consumer:
        bmp_stream = oBMP_parse(bytearray(message.value))
        bmp_stream = bmp_process.get_next(bmp_stream)
        while bmp_stream:
            bmp_stream = bmp_process.get_next(bmp_stream)
except KeyboardInterrupt:
    print("exit on keybaord interrupt")
consumer.close()
