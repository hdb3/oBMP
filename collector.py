#!/usr/bin/python3

#
# collector.py
# this is a generic TCP active sender
#
import os.path
import errno
import yaml
import traceback
import sys
import socket
import threading
from time import sleep
import pprint
import bgpparse
import bmpparse
import BGPribdb
import bmpblkparse

def log(c):
    sys.stderr.write(c)
    sys.stderr.flush()

class Session():

    def __init__(self,name,send,recv):
        self.name = name
        self.recv = recv
        self.send = send
        if 'sink' in name.lower():
            self.sink()
        elif 'source' in name.lower():
            self.source()
        elif 'bmpd' in name.lower():
            self.bmpd()
        else:
            self.run()

    def bmpd(self):
        import bmpparse
        import bgpparse
        import BGPribdb
        import bmpapp
        log("Session.bmpd(%s) starting\n" % self.name)
        n=0
        r=1
        parser = bmpapp.BmpContext()
        buf = bytearray()
        while True:
            msg = self.recv()
            if msg is None:
                print("null message")
                break
            elif len(msg) == 0:
                print("empty message")
                break
            else:
                r += 1
                buf.extend(msg)
                #filebuffer,bmp_msg = bmpparse.BMP_message.get_next_parsed(filebuffer)
                buf,bmp_msg = bmpparse.BMP_message.get_next(buf)
                while bmp_msg:
                    ##print(len(buf),len(bmp_msg))
                    parser.parse(bmpparse.BMP_message(bmp_msg))
                    n += 1
                    buf,bmp_msg = bmpparse.BMP_message.get_next(buf)
        print("%d messages processed" % n)
        print("%d blocks read" % r)
        print(parser.rib)
        log("Session.bmpd(%s) exiting\n" % self.name)

    def sink(self):
        from time import time
        log("Session.sink(%s) starting\n" % self.name)

        try:
            os.mkdir("dump")
        except OSError as e:
            pass

        ts = str(time())
        fn = "dump/" + self.name + "-" + ts + ".bmp"
        f = open(fn,"wb")

        i = 0
        msg = self.recv()

        while msg:
            print("msg(%d) rcvd length %d" % (i,len(msg)))
            i += 1
            f.write(msg)
            msg = self.recv()

        f.close()
        log("Session.sink(%s) exiting\n" % self.name)

    def source(self):
        i = 0
        log("Session.source(%s) starting\n" % self.name)
        status = self.send( bytes("Hello caller from %s!" % self.name,"ascii"))

        while status:
            print("msg sent %d" % i)
            status = self.send( bytes("Hello again from %s! (%d)" % (self.name,i),"ascii"))
            i += 1
            sleep(5)

        log("Session.source(%s) exiting\n" % self.name)

    def run(self):
        i = 0
        log("Session.run(%s) starting\n" % self.name)
        self.send( bytes("Hello caller from %s!" % self.name,"ascii"))
        msg = self.recv()
        while msg:
            print("msg rcvd %s" % str(msg))
            if b'bye' not in msg.lower() and i < 10:
                self.send( bytes("Hello again from %s! (%d)" % (self.name,i),"ascii"))
                sleep(1)
                i += 1
            else:
                self.send( bytes("Goodbye from from %s!" % self.name,"ascii"))
                break
            msg = self.recv()
        log("Session.run(%s) exiting\n" % self.name)

Initialising = 1
Connecting = 2
Connected = 3
Error = 4
Retrying = 5
Connected = 6
Disconnected = 7
BUFSIZ=4096

def _name(address):
    assert isinstance(address,tuple)
    return "%s:%d" % address

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
        self.log_err = lambda s : log("%s: %s\n" % (self.name,s))

    def run(self):
        self.state = Connecting
        if self.passive:
            self.log_err("awaiting connection on %s\n" % _name(self.address))
            self.listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            for i in range(100):
                try:
                    self.state = Error
                    self.listen_sock.bind(self.address)
                    self.state = Connecting
                    if i > 0:
                        self.log_err("bind success!")
                    break
                except OSError as e:
                    if e.errno != errno.EADDRINUSE:
                        raise
                    else:
                        if i == 0:
                            self.log_err("bind - address in use - will wait and try again")
                        else:
                            log("~")
                        sleep(3)
                except (socket.herror,socket.gaierror) as e:
                    self.log_err("unrecoverable error %s" % e + " connecting to %s\n" % _name(self.address))
                    traceback.print_tb( sys.exc_info()[2],limit=9)
                    self.state = Error
                except Exception as e:
                    self.log_err(("unknown error %s" % e) + (" connecting to %s\n" % _name(self.address)))
                    traceback.print_tb( sys.exc_info()[2],limit=9)
                    self.state = Error

            if self.state == Error:
                self.log_err("bind - address in use - giving up")
                exit()

            self.listen_sock.listen(1)

            while self.state != Error:
                try:
                    self.sock,remote_address = self.listen_sock.accept()
                    self.sock.setblocking(True)
                    self.state = Connected
                    self.connections += 1
                    self.log_err("connected to %s\n" % _name(remote_address))
                    session = Session(self.name,self.send,self.recv)
                    try:
                        self.sock.shutdown(socket.SHUT_RDWR)
                        self.sock.close()
                    except Exception as e:
                        self.log_err("ignored exception closing listen socket: %s\n" % str(e))
                        traceback.print_tb( sys.exc_info()[2],limit=9)
                except (socket.herror,socket.gaierror) as e:
                    self.log_err("unrecoverable error %s" % e + " connecting to %s\n" % _name(self.address))
                    traceback.print_tb( sys.exc_info()[2],limit=9)
                    self.state = Error
                    break
                except Exception as e:
                    self.log_err(("unknown error %s" % e) + (" connecting to %s\n" % _name(self.address)))
                    traceback.print_tb( sys.exc_info()[2],limit=9)
                    self.state = Error
                    sleep(10)
                    self.log_err("reawaiting connection on %s\n" % _name(self.address))
                    continue

        else:
            while True:
                try:
                    if self.connections == 0:
                        self.log_err("attempting connection to %s\n" % _name(self.address))
                    else:
                        self.log_err("reattempting connection to %s\n" % _name(self.address))
                    self.sock = socket.create_connection(self.address,1)
                    self.sock.setblocking(True)
                    self.state = Connected
                    self.connections += 1
                    self.log_err("connected to %s\n" % _name(self.address))
                    session = Session(self.name,self.send,self.recv)
                    self.sock.close()
                    self.sock.shutdown(socket.SHUT_RDWR)
                except (socket.error,socket.timeout) as e:
                    self.last_socket_error = e
                    self.state = Retrying
                    sleep(1)
                    continue
                except (socket.herror,socket.gaierror) as e:
                    self.log_err("unrecoverable error %s" % e + " connecting to %s\n" % _name(self.address))
                    traceback.print_tb( sys.exc_info()[2],limit=9)
                    self.state = Error
                    break
                except Exception as e:
                    self.log_err("unknown error %s" % e + " connecting to %s\n" % _name(self.address))
                    traceback.print_tb( sys.exc_info()[2],limit=9)
                    self.state = Error
                    break


    def recv(self):
        if self.state != Connected:
            log('r')
            return None
        else:
            try:
                return self.sock.recv(BUFSIZ)

                ## below is pointless if the service can handle fractional messages
                ## which it must!!!
                ## however, writing into a local buffer might make sense.....

                ##msg = self.sock.recv(BUFSIZ)
                ##fullmsg = msg
                ##while BUFSIZ == len(msg):
                    ##self.log_err("\nget more bytes on recv\n")
                    ##msg = self.sock.recv(BUFSIZ, socket.MSG_DONTWAIT)
                    ##fullmsg += msg
                ##return fullmsg

            except socket.timeout:
                self.sock.close()
                self.sock.shutdown(socket.SHUT_RDWR)
                self.log_err("\nwaited too long on recv %s\n")
                self.state = Disconnected
                return
            except socket.error as errmsg:
                if self.is_alive():
                    self.state = Disconnected
                    log('!')
                    self.log_err("\nunexpected error on recv %s\n" % errmsg)
                    self.event.set()
                    return
                else:
                    self.log_err("socket manager has exited\n")
                    self.state = Error
                    sys.exit()
            except Exception as e:
                self.log_err("\nunknown error on recv %s\n" % e)
                traceback.print_tb( sys.exc_info()[2],limit=9)
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
            return True

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
