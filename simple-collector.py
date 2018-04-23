#!/usr/bin/env python

import sys
import yaml
from kafka import KafkaConsumer
from oBMPparse import oBMP_parse
import bmpparse
import bmpapp
from socket import AF_INET
from time import sleep

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

bmp_parser = bmpapp.BmpContext("simple")
peers = set()
consumer=KafkaConsumer( _topic, api_version_auto_timeout_ms = 1000, request_timeout_ms = 1000, bootstrap_servers=_bootstrap_servers, client_id=_client_id)
try:
    for message in consumer:
        raw_bmp_message = oBMP_parse(bytearray(message.value))
        raw_bmp_message, bmp_msg = bmpparse.BMP_message.get_next(raw_bmp_message)
        while bmp_msg:
            ( msg_type, peer, msg ) = bmp_parser.parse(bmpparse.BMP_message(bmp_msg))
            raw_bmp_message, bmp_msg = bmpparse.BMP_message.get_next(raw_bmp_message)
            if msg_type == bmpparse.BMP_Initiation_Message:
                print("BMP session start")
            elif msg_type == bmpparse.BMP_Termination_Message:
                print("BMP session end")
            else:
                if not peer['hash'] in peers:
                    peers.add(peer['hash'])
                    print("new peer connected AS%d:%s" % (peer['remote_AS'], peer['remote_IPv4_address']))
                if msg_type == bmpparse.BMP_Statistics_Report:
                    print("stats report for AS%d:%s" % (peer['remote_AS'], peer['remote_IPv4_address']))
                elif msg_type == bmpparse.BMP_Route_Monitoring:
                    pass
except KeyboardInterrupt:
    print("exit on keybaord interrupt")
consumer.close()



##from ipaddress import IPv4Address


##remote_peer_address = IPv4Address(config['remote peer address'])


