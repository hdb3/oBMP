#!/usr/bin/env python

import sys
import yaml
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
from oBMPparse import oBMP_parse

import bmpapp
from bmpparse import BMP_message, BMP_Initiation_Message, BMP_Termination_Message, BMP_Route_Monitoring, BMP_Statistics_Report
class BMP_process:
    
    def __init__(self):
        self.parser = bmpapp.BmpContext("simple")
        self.peers = set()

    def process_message(self,bmp_msg):
        ( msg_type, peer, msg ) = self.parser.parse(BMP_message(bmp_msg))
        if msg_type == BMP_Initiation_Message:
            print("BMP session start")
        elif msg_type == BMP_Termination_Message:
            print("BMP session end")
        else:
            if not peer['hash'] in self.peers:
                self.peers.add(peer['hash'])
                print("new peer connected AS%d:%s" % (peer['remote_AS'], peer['remote_IPv4_address']))
            if msg_type == BMP_Statistics_Report:
                print("stats report for AS%d:%s" % (peer['remote_AS'], peer['remote_IPv4_address']))
            elif msg_type == BMP_Route_Monitoring:
                pass


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
while True:
    try:
        consumer=KafkaConsumer( _topic, api_version_auto_timeout_ms = 1000, request_timeout_ms = 1000, bootstrap_servers=_bootstrap_servers, client_id=_client_id)
        break
    except NoBrokersAvailable:
        print("retrying connection to Kafka broker")

bmp_process = BMP_process()

try:
    for message in consumer:
        bmp_stream = oBMP_parse(bytearray(message.value))
        bmp_stream, bmp_msg = BMP_message.get_next(bmp_stream)
        while bmp_msg:
            bmp_process.process_message(bmp_msg)
            bmp_stream, bmp_msg = BMP_message.get_next(bmp_stream)
except KeyboardInterrupt:
    print("exit on keybaord interrupt")
consumer.close()



##from ipaddress import IPv4Address


##remote_peer_address = IPv4Address(config['remote peer address'])


