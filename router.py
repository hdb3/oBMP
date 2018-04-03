#!/usr/bin/python3

#
# router
#

import yaml
import sys
import socket
import threading
from time import sleep
import pprint

from oBMPparse import oBMP_parse
from bgpparse import *
from bgprib import *
from bmpparse import *

Initialising = 1
Connecting = 2
Connected = 3
Error = 4
Retrying = 5
Connected = 6
Disconnected = 7

class RouterPeer(threading.Thread):

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
                    sleep(1)
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

def local_BGP_processor(rib,bgpmsg):
    global max_ribsize, parsed_bgp_message
    parsed_bgp_message = BGP_message(bgpmsg)
    for withdrawn_prefix in parsed_bgp_message.withdrawn_prefixes:
        rib.withdraw(withdrawn_prefix)
    ##eprint("parsed_bgp_message %s\n" % parsed_bgp_message)
    ##eprint("parsed_bgp_message.attribute %s\n" % pprint.pformat(parsed_bgp_message.attribute))
    for updated_prefixes in parsed_bgp_message.prefixes:
        rib.update(updated_prefixes,parsed_bgp_message.attribute)
    ribsize = len(rib.get_rib())
    if ribsize > max_ribsize:
        max_ribsize = ribsize
        ## sys.stderr.write("RIB size %d\n" % max_ribsize)
        ## sys.stderr.flush()
    return parsed_bgp_message.except_flag

def status_report():
    global rib
    ribsize = len(rib.get_rib())
    sys.stderr.write("RIB size/max size %d/%d\n" % (ribsize,max_ribsize))
    sys.stderr.flush()
    print("###########################################################")
    print("Status report")
    print("RIB size/max size %d/%d\n" % (ribsize,max_ribsize))
    print("**********************")
    print("random RIB entry")
    print("**********************")
    print(str(rib.last_update))
    print("**********************")
    print("last UPDATE")
    print("**********************")
    global parsed_bgp_message
    print(str(parsed_bgp_message))
    print("###########################################################")

def forward(collector,target):
    forwarder = Forwarder(target['host'],target['port'])
    forwarder.start()
    global rib
    rib = BGPrib()

    consumer = KafkaConsumer(bootstrap_servers=collector['bootstrap_servers'],client_id=collector['client_id'],group_id=collector['group_id'])
    consumer.subscribe(topics=collector['topic'])
    sys.stderr.write("listening to %s for topics %s\n" % (collector['bootstrap_servers'], collector['topic']))
    messages_received = 0
    for message in consumer:
        assert message.topic == collector['topic']
        if not messages_received:
            sys.stderr.write("first message received\n")
        messages_received += 1
        raw_msg = oBMP_parse(message.value)

        bmpmsgs = get_BMP_messages(raw_msg)
        for bmpmsg in bmpmsgs:
            if bmpmsg.msg_type == BMP_Statistics_Report:
                eprint("-- BMP stats report rcvd, length %d" % bmpmsg.length)
                status_report()
            elif bmpmsg.msg_type == BMP_Route_Monitoring:
                bgpmsg = bmpmsg.bmp_RM_bgp_message
                if (local_BGP_processor(rib,bgpmsg)):
                    forwarder.send(bgpmsg)
            else:
                sys.stderr.write("-- BMP non RM rcvd, BmP msg type was %d, length %d\n" % (bmpmsg.msg_type,bmpmsg.length))

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
