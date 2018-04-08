#!/usr/bin/python3

#
# collector.py
# this is a generic TCP active sender
#
import os.path
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
                print("msg rcv: %s" % hex(msg))
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

def log(c):
    sys.stderr.write(c)
    sys.stderr.flush()

class Collector(threading.Thread):

    def __init__(self,name,host,port,passive=False):
        threading.Thread.__init__(self)
        self.name = name
        self.passive = passive
        self.daemon = False # keep main prog until collectors exit
        self.state = Initialising
        self.connections = 0
        self.event = threading.Event()
        self.address = (host,port)
        self.address_name = "%s:%d" % (host,port)
        self.log_err = lambda s : log("%s: %s\n" % (self.name,s))

    def run(self):
        while True:
            self.state = Connecting
            if self.passive:
                if self.connections == 0:
                    self.log_err("awaiting connection on %s\n" % self.address_name)
                else:
                    self.log_err("reawaiting connection on %s\n" % self.address_name)
            else:
                if self.connections == 0:
                    self.log_err("attempting connection to %s\n" % self.address_name)
                else:
                    self.log_err("reattempting connection to %s\n" % self.address_name)
            while self.state != Connected:
                if self.passive:
                    try:
                        listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        listen_socket.bind(self.address)
                        listen_socket.listen(1)
                        self.sock,self.address = listen_socket.accept()
                    except (socket.herror,socket.gaierror) as e:
                        self.log_err("unrecoverable error %s" % e + " connecting to %s\n" % self.address_name)
                        self.state = Error
                        sys.exit()
                    except (socket.error,socket.timeout) as e:
                        self.last_socket_error = e
                        self.state = Retrying
                        sleep(1)
                        continue
                    except Exception as e:
                        self.log_err("unknown error %s" % e + " connecting to %s\n" % self.address_name)
                        self.state = Error
                        sys.exit()
                    else:
                        self.state = Connected
                        self.connections += 1
                        self.log_err("connected to %s\n" % self.address_name)
                        self.event.clear()
                        self.event.wait()
                        self.event.clear()
                        session = Session()
                        session.run(self.send,self.recv)

                else:
                    try:
                        self.sock = socket.create_connection(self.address,1)
                    except (socket.herror,socket.gaierror) as e:
                        self.log_err("unrecoverable error %s" % e + " connecting to %s\n" % self.address_name)
                        self.state = Error
                        sys.exit()
                    except (socket.error,socket.timeout) as e:
                        self.last_socket_error = e
                        self.state = Retrying
                        sleep(1)
                        continue
                    except Exception as e:
                        self.log_err("unknown error %s" % e + " connecting to %s\n" % self.address_name)
                        self.state = Error
                        sys.exit()
                    else:
                        self.state = Connected
                        self.connections += 1
                        self.log_err("connected to %s\n" % self.address_name)
                        self.event.clear()
                        self.event.wait()
                        self.event.clear()
                        session = Session()
                        session.run(self.send,self.recv)


    def recv(self):
        if self.state != Connected:
            log('r')
            return None
        else:
            try:
                msg = self.sock.recv(BUFSIZ)
                fullmsg = msg
                while BUFSIZ == len(msg):
                    self.log_err("\nget more bytes on recv\n")
                    msg = self.sock.recv(BUFSIZ, socket.MSG_DONTWAIT)
                    fullmsg += msg
                return fullmsg

            except socket.error as errmsg:
                if self.is_alive():
                    self.state = Disconnected
                    log('!')
                    self.event.set()
                    return
                else:
                    self.log_err("socket manager has exited\n")
                    self.state = Error
                    sys.exit()
            except Exception as e:
                self.log_err("\nunknown error on recv %s\n" % e)
                self.state = Error
                return None

            log('+')

    def send(self,msg):
        if self.state != Connected:
            log('s')
        else:
            try:
                self.sock.sendall(msg)

            except socket.error as errmsg:
                if self.is_alive():
                    self.state = Disconnected
                    log('s')
                    self.event.set()
                    return
                else:
                    self.log_err("socket manager has exited\n")
                    self.state = Error
                    sys.exit()
            log('S')

def main(name,config):

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
            collectors.append(Collector(name,target['host'],target['port'],passive=False))

    if ('listener' in forward_cfg):
        cfg_listener = forward_cfg['listener']
        if '*' == cfg_listener['host']:
            cfg_listener['host'] = ''
        collectors.append(Collector(name,cfg_listener['host'],cfg_listener['port'],passive=True))

    for collector in collectors:
        collector.start()

if len(sys.argv) > 1:
    filenames = [sys.argv[1],'collector.yml']
else:
    filenames = ['collector.yml']
for filename in filenames:
    try:
        cfg = yaml.load(open(filename, 'r'))
    except Exception as e:
        print("couldn't open %s as YAML config" % filename,file=sys.stderr)
        print("exception %s" % e,file=sys.stderr)
    else:
        name = os.path.splitext(os.path.basename(filename))[0]
        main(name,cfg)
        exit()
