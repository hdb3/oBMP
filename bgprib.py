
from bgpparse import *
import BGPribdb
##import ipaddress

analyse_withdraws = False
analyse_replacements = False

BGP_known_attributes = frozenset([
    BGP_TYPE_CODE_ORIGIN,
    BGP_TYPE_CODE_AS_PATH,
    BGP_TYPE_CODE_NEXT_HOP,
    BGP_TYPE_CODE_MULTI_EXIT_DISC,
    BGP_TYPE_CODE_LOCAL_PREF,
    BGP_TYPE_CODE_ATOMIC_AGGREGATE,
    BGP_TYPE_CODE_AGGREGATOR,
    BGP_TYPE_CODE_COMMUNITIES,
    BGP_TYPE_CODE_MP_REACH_NLRI,
    BGP_TYPE_CODE_MP_UNREACH_NLRI,
    BGP_TYPE_CODE_AS4_PATH,
    BGP_TYPE_CODE_AS4_AGGREGATOR,
    BGP_TYPE_CODE_LARGE_COMMUNITY])



class BGPrib:

    def __init__(self):
        self.RIB = {}
        ## self.last_update = None
        self.ribDB = BGPribdb()
        # a RIB entry contains a prefix and lots besides
        # to enforce this, use a method 'update', which adds entries and replaces
        # existing ones (with an action)
        # corresponding method 'withdraw' removes entries

    def get_rib(self):
        return self.RIB

    def get_rib_entry(self,prefix):
        self.validate_prefix(prefix)
        return self.RIB.key(prefix)

    def update(self,prefixes,attrs):
        if self.self.validate_attrs(attrs):
            ## self.RIB[prefix] = attrs
            self.ribDB.update(attrs,prefixes)

    def withdraw(self,prefixes):
        self.ribDB.withdraw(prefixes)

        ## try:
            ## del self.RIB[prefix]
        ## except  KeyError:
            ## pass

    def report(self,prefix,attrs,previous):
        global analyse_replacements
        if analyse_replacements and previous:
            eprint("updating RIB for %s/%d" % prefix)

    def reportw(self,prefix,previous):
        global analyse_withdraws
        if analyse_withdraws:
            eprint("withdrawing from RIB %s/%d" % prefix)



    def validate(self,prefix,attrs):
        # these conditions are mostly on code rather than external behaviour
        # the exception is the mandatroty attributes
        # there is no check on the types of attributes (yet)
        status = True
        try:
            self.validate_prefix(prefix)
            self.validate_attrs(attrs)
        except AssertionError as e:
            status = False
            eprint("Validation failure %s" % e)
        return status

    def validate_attrs(self,attrs):
        for k in attrs.keys():
            assert isinstance(k,int), "attribute code not int error"+str(type(k))
            assert k in BGP_known_attributes, "unknown attribute %d" % k
        assert BGP_TYPE_CODE_ORIGIN in attrs, "mandatory attribute BGP_TYPE_CODE_ORIGIN missing"
        assert BGP_TYPE_CODE_AS_PATH in attrs, "mandatory attribute BGP_TYPE_AS_PATH missing"
        assert BGP_TYPE_CODE_NEXT_HOP in attrs, "mandatory attribute BGP_TYPE_NEXT_HOP missing"

    def validate_prefix(self,prefix):
        (length,addr) = prefix
        assert isinstance(addr,int), "prefix not int error"+str(type(k))
        assert isinstance(length,int), "prefix  lengthnot int error"+str(type(k))
        assert length < 33, "prefix longer than 32 error"
