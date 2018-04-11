import struct
import sys
import os
import time
import zlib

from oBMPparse import oBMP_parse
import bmpparse
import bmpapp


_msg_marker = struct.pack('!Q',0x9a9a9a9a9a9a9a9a)

class Topic:

    def __init__(self,topic,parse_enabled=False,bmp_file_enabled=True,obmp_file_enabled=True):

        self.bmp_file_enabled = bmp_file_enabled
        self.obmp_file_enabled = obmp_file_enabled
        self.parse_enabled = parse_enabled
        self.topic = topic

        try:
            os.mkdir("dump")
        except OSError as e:
            pass

        ts = str(time.time())

        self.messages_received = 0
        if self.bmp_file_enabled:
            self.bmp_file = open("dump/" + self.topic + "-" + ts + ".bmp","wb")
        if self.obmp_file_enabled:
            self.obmp_file = open("dump/" + self.topic + "-" + ts + ".obmp","wb")
        if parse_enabled:
            self.parser = bmpapp.BmpContext(topic)

        sys.stderr.write("topic %s is active\n" % self.topic)

    def exit(self):
        self.bmp_file.close()
        self.obmp_file.close()

    @staticmethod
    def delimit(msg):
        assert isinstance(msg,bytearray)
        delimited_message = bytearray(_msg_marker + struct.pack('!I',len(msg)) + struct.pack('!I',zlib.crc32(msg)))
        delimited_message.extend(msg) 
        return delimited_message

    def process(self,obmp_message):
        assert isinstance(obmp_message,bytearray)
    
        self.messages_received += 1

        if self.obmp_file_enabled:
            self.obmp_file.write(self.delimit(obmp_message))

        raw_bmp_message = oBMP_parse(obmp_message)
        if self.bmp_file_enabled:
            self.bmp_file.write(raw_bmp_message)

        if self.parse_enabled:
            raw_bmp_message,bmp_msg = bmpparse.BMP_message.get_next(raw_bmp_message)
            while bmp_msg:
                self.parser.parse(bmpparse.BMP_message(bmp_msg))
                raw_bmp_message,bmp_msg = bmpparse.BMP_message.get_next(raw_bmp_message)

            assert 0 == len(raw_bmp_message)
