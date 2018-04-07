#!/usr/bin/python3

#
# forwarder.py
# this is a generic TCP active sender
#

import yaml
import sys
import socket
import threading
from time import sleep
import pprint

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

def main():

    with open("forwarder.yml", 'r') as ymlfile:
        cfg = yaml.load(ymlfile)
        if ('forwarder' not in cfg):
            sys.exit("could not find section 'forwarder' in config file")
        else:
            forward_cfg=cfg['forwarder']
        if ('target' not in forward_cfg):
            sys.exit("could not find sub-section 'target' in config file")

    target = (forward_cfg['target'])
    forwarder = Forwarder(target['host'],target['port'])
    forwarder.start()
    i = 0
    while True:
        test_msg = bytes("Hello world %d" % i,"ascii")
        forwarder.send(test_msg)
        sleep(5)
        i += 1

main()
