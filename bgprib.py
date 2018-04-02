
from bgpparse import *
import ipaddress

BGP_known_attributes = frozenset([
    BGP_TYPE_CODE_ORIGIN,
    BGP_TYPE_CODE_AS_PATH,
    BGP_TYPE_CODE_NEXT_HOP,
    BGP_TYPE_CODE_MULTI_EXIT_DISC,
    BGP_TYPE_CODE_LOCAL_PREF,
    BGP_TYPE_CODE_ATOMIC_AGGREGATE,
    BGP_TYPE_CODE_AGGREGATOR,
    BGP_TYPE_CODE_COMMUNITIES,
    BGP_TYPE_CODE_AS4_PATH ])


class BGPrib:

    def __init__(self):
        self.RIB = {}
        # a RIB entry contains a prefix and lots besides
        # to enforce this, use a method 'update', which adds entries and replaces
        # existing ones (with an action)
        # corresponding method 'withdraw' removes entries

    def get_rib(self):
        return self.RIB

    def get_rib_entry(self,prefix):
        self.validate_prefix(prefix)
        return self.RIB.key(prefix)

    def update(self,prefix,attrs):
        if self.validate(prefix,attrs):
            previous = self.RIB.get(prefix)
            if previous:
                self.report(prefix,attrs,previous)
        self.RIB[prefix] = attrs

    def withdraw(self,prefix):
        self.validate_prefix(prefix)
        analyse_withdraws = True
        if not analyse_withdraws:
            try:
                del self.RIB[prefix]
            except  KeyError:
                pass
        else:
        ## if you want to analyse withdraws, the follwoing code will do it
            previous = self.RIB.get(prefix)
            if previous:
                self.reportw(prefix,previous)
                del self.RIB[prefix]

    def report(self,prefix,attrs,previous):
        if previous:
            eprint("updating RIB for %s/%d" % prefix)

    def reportw(self,prefix,previous):
        eprint("withdrawing from RIB %s/%d" % prefix)



    def validate(self,prefix,attrs):
        # these conditions are mostly on code rather than external behaviour
        # the exception is the mandatroty attributes
        # there is no check on the types of attributes (yet)
        self.validate_prefix(prefix)
        self.validate_attrs(attrs)

    def validate_attrs(self,attrs):
        keys = ""
        for k in attrs.keys():
            assert isinstance(k,int)
            assert k in BGP_known_attributes
            keys += " " + str(k)
        ##eprint("!!validate_attrs - keys %s" % keys)
        assert BGP_TYPE_CODE_ORIGIN in attrs
        assert BGP_TYPE_CODE_AS_PATH in attrs
        assert BGP_TYPE_CODE_NEXT_HOP in attrs

    def validate_prefix(self,prefix):
        (length,addr) = prefix
        ##assert isinstance(addr,ipaddress.IPv4Address)
        assert isinstance(addr,int)
        assert isinstance(length,int)
        assert length < 33
