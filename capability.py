
import struct
from capabilitycodes import BGP_capability_codes
cc = BGP_capability_codes

class Capability:    
    # encode a capability value in wire format
    # this is also the way that the capability is currently stored internally, so this method is applicable for creating stored objects but not needed during dpearsing

    @staticmethod
    def cap(code,value=None):

        # assert code in valid_codes
        assert isinstance(code,BGP_capability_codes)
        v = bytearray()

        if code == cc.multiprotocol:
            assert isinstance(value,tuple) and 2 == len(value)
            assert isinstance(value[0],int)
            assert isinstance(value[1],int)
            v.extend( struct.pack('!H', value[1])) # AFI value
            v.extend( struct.pack('!B', 0 )) # reserved, == 0
            v.extend( struct.pack('!B', value[1])) # SAFI value

        # graceful restart is complex and in full implmentation requires AFI/SAFI fields
        # this implementation  is the simpler onw which indicates that end-of-RIB indicator is supported.
        # see RFC 4724

        elif code == cc.graceful_restart:
            assert isinstance(value,tuple) and 2 == len(value)
            assert isinstance(value[0],bool)
            assert isinstance(value[1],int)
            if value[0]:
                v.extend( struct.pack('!H', value[0])) # timer value
            else:
                v.extend( struct.pack('!H', 0x8000 | value[0])) # timer value with restart flag set

        elif code == cc.AS4:
            assert isinstance(value,int)
            v.extend( struct.pack('!I', value)) # 32 bit AS number

        else:
            assert value is None

        t = code.value
        l = len(v)
        r = bytearray()
        r.extend(struct.pack('!B', int(t)))
        r.extend(struct.pack('!B', l))
        r.extend(v)
        return r

    # produce storable format of a wire-encoded capability code
    @staticmethod
    def decode_cap(msg):

        t = struct.unpack_from('!B', msg, offset=0)[0]
        l = struct.unpack_from('!B', msg, offset=1)[0]
        assert t in valid_codes
        code = BGP_capability_codes(t)


        if code == cc.multiprotocol:
            assert l == 4
            assert 0 == struct.unpack_from('!B', msg, offset=4)[0] # reserved, == 0
            v = ( struct.unpack_from('!H', msg, offset=2)[0] # AFI value \
                , struct.unpack_from('!B', msg, offset=5)[0] ) # SAFI value

        elif code == cc.graceful_restart:
            assert l == 2
            restart_flag = bool(struct.unpack_from('!H', msg, offset=2)[0] & 0x8000)
            timer_value = struct.unpack_from('!H', msg, offset=2)[0] & 0x0fff
            v = ( restart_flag , timer_value )

        elif code == cc.AS4:
            assert l == 4
            v = struct.unpack_from('!I', msg, offset=2)[0]

        else:
            assert value is None
            v = None

        return (t,v)

    @staticmethod
    def display_cap(tpl):
        (c,v) = tpl
        assert t in valid_codes

        s = c.name()

        if code == cc.multiprotocol:
            s += " AFI:%d SAFI:%d" % (v[0],v[1])

        elif code == cc.graceful_restart:
            (restart_flag,timer_value) = v
            if restart_flag:
                fls = "True"
            else:
                fls = "False"

            s += " restart flag:%s timer:%d" % (fls,timer_value)

        elif code == cc.AS4:
            s += " AS4:%d" % value
        else:
            assert value is None

        return s
