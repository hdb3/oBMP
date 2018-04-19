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

def log(c):
    sys.stderr.write(c)
    sys.stderr.flush()

class Session():

    def __init__(self,app,name,send,recv):
        self.name = name
        self.recv = recv
        self.send = send

        if app:
            if hasattr(self,app):
                getattr(self,app)()
            else:
                sys.exit("requested app '%s' not found" % app)
        elif hasattr(self,name):
            getattr(self,name)()
        else:
            self.run()
    
    def router(self):
        import bgppeel
        from bgpmsg import BGP_message,BGP_OPEN,BGP_KEEPALIVE,BGP_UPDATE,BGP_NOTIFICATION
        from bgpopen import BGP_OPEN_message
        from bgpupdate import BGP_UPDATE_message
        from ipaddress import IPv4Address
        from capabilitycodes import BGP_capability_codes,AFI_IPv4,SAFI_Unicast

        def make_open_msg():
            caps = [ (BGP_capability_codes.route_refresh, None), \
                     (BGP_capability_codes.multiprotocol,(AFI_IPv4,SAFI_Unicast)), \
                     (BGP_capability_codes.AS4,64505), \
                     (BGP_capability_codes.graceful_restart,(False,1000)) ]
            open_msg =  BGP_OPEN_message.new(64505,60,IPv4Address('10.30.65.209'), caps)
    
            return BGP_message.deparse(BGP_OPEN,open_msg.deparse())
    
    
        log("Session.router(%s) starting\n" % self.name)
        n=0
        r=1
        buf = bytearray()
        msg = self.recv()
        while msg:
            r += 1
            buf.extend(msg)
            msg_type,bgp_msg,buf = bgppeel.peel(buf)
            while bgp_msg:
                bgp_payload = bgp_msg[19:]
                if msg_type == BGP_KEEPALIVE:
                    print("BGP KEEPALIVE rcvd")
                    self.send(BGP_message.keepalive())
                elif msg_type == BGP_NOTIFICATION:
                    print("BGP NOTIFY rcvd")
                elif msg_type == BGP_UPDATE:
                    print("BGP UPDATE rcvd")
                    parsed_update_msg = BGP_UPDATE_message.parse(bgp_payload)
                elif msg_type == BGP_OPEN:
                    print("BGP OPEN rcvd")
                    parsed_open_msg = BGP_OPEN_message.parse(bgp_payload)
                    print(parsed_open_msg)
                    self.send(self.make_open_msg())
                    self.send(BGP_message.keepalive())
                else:
                    print("BGP msg type %d rcvd" % msg_type)
                n += 1
                msg_type,bgp_msg,buf = bgppeel.peel(buf)
            msg = self.recv()
        print("%d messages processed" % n)
        print("%d blocks read" % r)
        log("Session.router(%s) exiting\n" % self.name)
    
    def bmpd(self):
        import bmpparse
        import bmpapp
        log("Session.bmpd(%s) starting\n" % self.name)
        n=0
        r=1
        parser = bmpapp.BmpContext(self.name)
        buf = bytearray()
        msg = self.recv()
        while msg:
            r += 1
            buf.extend(msg)
            #filebuffer,bmp_msg = bmpparse.BMP_message.get_next_parsed(filebuffer)
            buf,bmp_msg = bmpparse.BMP_message.get_next(buf)
            while bmp_msg:
                parser.parse(bmpparse.BMP_message(bmp_msg))
                n += 1
                buf,bmp_msg = bmpparse.BMP_message.get_next(buf)
            msg = self.recv()
        print("%d messages processed" % n)
        print("%d blocks read" % r)
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

    def __init__(self,app,name,host,port):
        ## why not just use super????
        ## - -  well it doesn't work so don't....
        ##super().__init__(self,name=name,daemon=False)
        threading.Thread.__init__(self,name=name,daemon=False)
        self.state = Initialising
        self.app = app
        self.connections = 0
        self.event = threading.Event()
        self.address = (host,port)
        self.log_err = lambda s : log("%s: %s\n" % (self.name,s))


    def recv(self):
        if self.state != Connected:
            return None
        else:
            try:
                return self.sock.recv(BUFSIZ)

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

    def send(self,msg):
        if self.state != Connected:
            pass
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
            return True

class Listener(Collector):

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)

    def run(self):
        self.state = Connecting
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
                session = Session(self.app,self.name,self.send,self.recv)
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


class Talker(Collector):

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)

    def run(self):
        self.state = Connecting
        while True:
            try:
                if self.state == Connecting:
                    # only print out the message once per new connection attempt
                    # i.e. not every 1 second whilst retrying after timeout
                    if self.connections == 0:
                        self.log_err("attempting connection to %s\n" % _name(self.address))
                    else:
                        self.log_err("reattempting connection to %s\n" % _name(self.address))
                self.sock = socket.create_connection(self.address,1)
                self.sock.setblocking(True)
                self.state = Connected
                self.connections += 1
                self.log_err("connected to %s\n" % _name(self.address))
                self.connections += 1
                session = Session(self.app,self.name,self.send,self.recv)
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

def main(name,config):

    if ('collector' not in cfg):
        sys.exit("could not find section 'collector' in config file")
    else:
        collector_cfg=cfg['collector']

    if ('daemon' not in collector_cfg):
        sys.exit("could not find sub-section 'daemon' in config file")

    if ('listener' not in collector_cfg and 'targets' not in collector_cfg):
        sys.exit("could not find sub-section 'targets' or 'listener' in config file")

    collectors = []
    if ('targets' in collector_cfg):
        cfg_targets = collector_cfg['targets']
        for cfg_target in cfg_targets:
            assert 'host' in cfg_target
            assert 'port' in cfg_target
            collectors.append(Talker(collector_cfg['daemon'],name,cfg_target['host'],cfg_target['port']))

    if ('listener' in collector_cfg):
        cfg_listener = collector_cfg['listener']
        ## TODO move this functionality into the listener code
        if '*' == cfg_listener['host']:
            cfg_listener['host'] = ''
        collectors.append(Listener(collector_cfg['daemon'],name,cfg_listener['host'],cfg_listener['port']))

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
