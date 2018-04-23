#!/usr/bin/env python

from kafka import KafkaConsumer
from oBMPparse import oBMP_parse
import bmpparse
import bmpapp

parser = bmpapp.BmpContext("simple")

topic = 'openbmp.router--route-views.routeviews.org.peer-as--7018.bmp_raw'
consumer=KafkaConsumer(topic, bootstrap_servers=['bmp.bgpstream.caida.org:9092'],client_id='lancaster_university_UK',group_id='beta-bmp-stream')
#consumer=KafkaConsumer(topic, bootstrap_servers=['bmp.bgpstream.caida.org:9092'],client_id='lancaster_university_UK',group_id='beta-bmp-stream')
for message in consumer:
    try:
        #print ("%s:%d:%d: key=%s length=%d" % (message.topic, message.partition, message.offset, message.key, len(message.value)))
        raw_bmp_message = oBMP_parse(bytearray(message.value))
        raw_bmp_message, bmp_msg = bmpparse.BMP_message.get_next(raw_bmp_message)
        while bmp_msg:
            parser.parse(bmpparse.BMP_message(bmp_msg))
            raw_bmp_message, bmp_msg = bmpparse.BMP_message.get_next(raw_bmp_message)
    except KeyboardInterrupt:
        break
consumer.close()



##from ipaddress import IPv4Address


##remote_peer_address = IPv4Address(config['remote peer address'])


