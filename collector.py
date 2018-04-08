#!/usr/bin/python3

#
# collector.py
# this is a generic TCP active sender
#

import yaml
import sys
import socket
import threading
from time import sleep
import pprint

class Session(threading.Thread):

    def __init__(send,recv):
        self.recv = recv
        self.send = send
        self.run()

    def run(self):
        i = 0
        while True:
            self.send( bytes("Hello caller! (%d)" % i,"ascii"))
            msg = self.recv()
            if msg:
                print("msg rcv: %s" % hex(msg)
            else:
                test_msg = bytes("Hello world (%d)" % i,"ascii")
            self.send( bytes("Hello world! (%d)" % i,"ascii"))
            sleep(5)
            i += 1

Initialising = 1
Connecting = 2
Connected = 3
Error = 4
Retrying = 5
Connected = 6
Disconnected = 7

class Collector(threading.Thread):

    def __init__(self,host,port,passive=False):
        threading.Thread.__init__(self)
        self.daemon = False # keep main prog until collectors exit
        self.state = Initialising
        self.connections = 0
        self.event = threading.Event()
        self.address = (host,port)

    def run(self):
        while True:
            self.state = Connecting
            if self.passive:
                if self.connections == 0:
                    sys.stderr.write("awaiting connection to %s:%d\n" % self.address)
                else:
                    sys.stderr.write("reawaiting connection to %s:%d\n" % self.address)
            else:
                if self.connections == 0:
                    sys.stderr.write("attempting connection to %s:%d\n" % self.address)
                else:
                    sys.stderr.write("reattempting connection to %s:%d\n" % self.address)
            while self.state != Connected:
                if self.passive:
                    try:
                        socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.bind(self.address)
                        s.listen(1)
                        self.sock,self.address = s.accept()
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
                    else:
                        self.state = Connected
                        self.connections += 1
                        sys.stderr.write("connected to %s:%d\n" % self.address)
                        self.event.clear()
                        self.event.wait()
                        self.event.clear()
                        session = Session()
                        session.run(self.send,self.recv)

                else:
                    if self.connections == 0:
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
                    else:
                        self.state = Connected
                        self.connections += 1
                        sys.stderr.write("connected to %s:%d\n" % self.address)
                        self.event.clear()
                        self.event.wait()
                        self.event.clear()
                        session = Session()
                        session.run(self.send,self.recv)


    def recv(self):
        if self.state != Connected:
            sys.stderr.write('r')
            sys.stderr.flush()
            return None
        else:
            try:
                msg = self.sock.recv(BUFSIZ)
                fullmsg = msg
                while BUFSIZ == len(msg):
                    sys.stderr.write("\nget more bytes on recv\n")
                    msg = self.sock.recv(BUFSIZ, socket.MSG_DONTWAIT)
                    fullmsg += msg
                return fullmsg

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
            except Exception as e:
                sys.stderr.write("\nunknown error on recv %s\n" % e)
                self.state = Error
                return None

            sys.stderr.write('+')
            sys.stderr.flush()

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

    with open("collector.yml", 'r') as ymlfile:
        cfg = yaml.load(ymlfile)
        if ('collector' not in cfg):
            sys.exit("could not find section 'collector' in config file")
        else:
            forward_cfg=cfg['collector']

        if ('listener' not in forward_cfg and 'targets' not in forward_cfg):
            sys.exit("could not find sub-section 'targets' or 'listener' in config file")

        collectors = []
        if ('targets' in forward_cfg):
            cfg_targets = forward_cfg['targets']
            for target in cfg_targets:
                assert 'host' in target
                assert 'port' in target
            collectors.append() = Collector(target['host'],target['port'],passive=False)

        if ('listener' in forward_cfg):
            cfg_listener = forward_cfg['listener']
            for target in cfg_targets:
                assert 'host' in cfg_listener
                assert 'port' in cfg_listener
            collectors.append() = Collector(cfg_listener['host'],cfg_listener['port'],passive=True)

    for collector in collectors:
        collector.start()

main()
