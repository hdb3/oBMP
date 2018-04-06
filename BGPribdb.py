
# BGPribdb.py
#
# a threadsafe BGP RIB for a router
#

import threading
import pickle
import sys

class BGPribdb:
    def __init__(self):
        self.db_lock = threading.Lock()
        self.rib = {}
        self.path_attributes = {}
        self.update_requests = {}
        self.path_update_requests = {}
        self.path_update_requests[None] = []

        # the following are use counts over all received updates/withdraws
        # counting the size of the dictionary provides the unique count
        # summing each item give the total
        self.all_prefixes_rcvd={}
        self.all_prefixes_withdrawn={}

        # refresh_update_requests is a list whilst refresh operation is in progress
        # when it is an empty list then it is time to send end-of-RIB, after which it is set None
        self.refresh_update_requests = None

    def __str__(self):


        # calculate the global update state
        pa_hashes_in_update_dict = {}
        prefixes_in_update = 0
        prefixes_in_withdraw = 0
        pa_hashes = {}
        for (pfx,pa_hash) in self.update_requests:
            if pa_hash:
                prefixes_in_update += 1
                pa_hashes_in_update_dict[pa_hash]=None
            else:
                prefixes_in_withdraw += 1
            if not pa_hash in pa_hashes:
                pa_hashes[pa_hash] = 1
            else:
                pa_hashes[pa_hash] += 1
        pa_hashes_in_update = len(pa_hashes_in_update_dict)

        # calculate the per path update state
        # this includes obseleted updates/withdraws
        path_pa_hashes_in_update = 0
        path_prefixes_in_update = 0
        path_prefixes_in_withdraw = 0
        for (pa_hash,pfxlist) in self.path_update_requests.items():
            path_pa_hashes_in_update += 1
            if pa_hash:
                path_prefixes_in_update += len(pfxlist)
            else:
                path_prefixes_in_withdraw += len(pfxlist)

        # calculate the historic state
        cnt_all_unique_prefixes_rcvd = len(self.all_prefixes_rcvd)
        cnt_all_prefixes_rcvd = 0
        for pfx in self.all_prefixes_rcvd:
            cnt_all_prefixes_rcvd += self.all_prefixes_rcvd[pfx]

        cnt_all_unique_prefixes_withdrawn = len(self.all_prefixes_withdrawn)
        cnt_all_prefixes_withdrawn = 0
        for pfx in self.all_prefixes_withdrawn:
            cnt_all_prefixes_withdrawn += self.all_prefixes_withdrawn[pfx]


        return \
               "**BGPribdb state**\n" + \
               "  rib size %d    " % len(self.rib) + \
               "  paths in rib %d\n" % len(self.path_attributes) + \
               "  *historic view* prefixes rcvd / unique prefixes rcvd = %d/%d\n" % ( cnt_all_prefixes_rcvd,cnt_all_unique_prefixes_rcvd) + \
               "  *historic view* prefixes withd / unique prefixes withd = %d/%d\n" % ( cnt_all_prefixes_withdrawn,cnt_all_unique_prefixes_withdrawn) + \
               "  *global view* paths/prefixes/withdrawn in update %d/%d/%d\n" % (pa_hashes_in_update,prefixes_in_update,prefixes_in_withdraw) + \
               "  *path view* paths/prefixes/withdrawn in update %d/%d/%d\n" % (path_pa_hashes_in_update,path_prefixes_in_update,path_prefixes_in_withdraw)

    def lock(self):
        self.db_lock.acquire()

    def unlock(self):
        self.db_lock.release()


    @staticmethod
    def show_pfx(pfx):
        import ipaddress
        return str(ipaddress.ip_address(pfx[0]))+"/"+str(int(pfx[1]))

    @staticmethod
    def path_attribute_hash(pa):
        return hash(pickle.dumps(pa, protocol=pickle.HIGHEST_PROTOCOL))

    def atomic_update(self,pfx,pa_hash):

        # ALWAYS update the main RIB
        # UNLESS the RIB is unchanged schedule update sending
        if pa_hash not in self.rib or self.rib[pfx] != pa_hash:
            self.rib[pfx] = pa_hash
            self.path_update_requests[pa_hash].append(pfx)
            self.update_requests[pfx] = pa_hash
        else:
            # it's not expected that a duplicate insert occurs
            # but it's not a problem and it does not call for an UPDATE to be sent
            sys.stderr.write("\n*** Unexpected duplicate insert for %s/%s\n" % (self.show_pfx(pfx),pa_hash))
            # pass
        if pfx in self.all_prefixes_rcvd:
            self.all_prefixes_rcvd[pfx] += 1
        else:
            self.all_prefixes_rcvd[pfx] = 1

    def atomic_withdraw(self,pfx):
        self.atomic_update(pfx,None)
        if pfx in self.all_prefixes_withdrawn:
            self.all_prefixes_withdrawn[pfx] += 1
        else:
            self.all_prefixes_withdrawn[pfx] = 1

    def update(self,pa,pfx_list):
        self.lock()
        pa_hash = BGPribdb.path_attribute_hash(pa)
        ##pa_hash = hash(pa)
        if pa_hash not in self.path_attributes:
            self.path_attributes[pa_hash] = pa
        if pa_hash not in self.path_update_requests:
            self.path_update_requests[pa_hash] = []
        for pfx in pfx_list:
            self.atomic_update(pfx,pa_hash)
        self.unlock()

    def withdraw(self,pfx_list):
        self.lock()
        for pfx in pfx_list:
            self.atomic_withdraw(pfx)
        self.unlock()

    def refresh(self):
        self.lock()

        # zero out normal update actions queued
        self.path_update_requests = {}
        self.path_update_requests[None] = []
        self.update_requests = {}

        self.refresh_update_requests = {}
        for (pfx,pa_hash) in self.rib.items():
            # don't put withdraws into the refresh table
            if pa_hash:
                if pa_hash not in self.refresh_update_requests:
                    self.refresh_update_requests[pa_hash] = []
                self.refresh_update_requests[pa_hash].append(pfx)
                ## print("refresh - using update %s %0X" % (self.show_pfx(pfx),pa_hash))## debug code
        self.unlock()

    # consume API
    #
    # withdraw request objects and update request objects have the same structure, with the Path Attribute field None in the case of withdraw
    #
    # refresh request returns first items from the refresh list , then from the normal list, 
    # the last item from a refresh list is (None,None), which signals 'end-of-RIB'
    #
    # if there are no items in either list then the return value is simply 'None'

    def groom_updates(self,pa_hash,pfxlist):
        new_pfxlist=[]
        for pfx in pfxlist:
            if pfx in self.rib and self.rib[pfx] == pa_hash and pfx in self.update_requests and self.update_requests[pfx] == pa_hash:
                ## print("groom_updates - using update %s %0X/%0X" % (self.show_pfx(pfx),pa_hash,self.update_requests[pfx]))## debug code
                new_pfxlist.append(pfx)
                del self.update_requests[pfx]
            else:
                ## print("groom_updates - dropping update %s %d %0X/%0X" % (self.show_pfx(pfx),int(pfx in self.update_requests),pa_hash,self.update_requests[pfx]))## debug code
                pass
        return new_pfxlist

    def get_update_request(self):
        if self.refresh_update_requests is None:
            # return withdraws first....
            try:
                if None in self.path_update_requests:
                    pa_hash = None
                    pfxlist = self.path_update_requests.pop(None)
                else:
                    (pa_hash,pfxlist) = self.path_update_requests.popitem()
                return (self.path_attributes[pa_hash],self.groom_updates(pa_hash,pfxlist))
            except KeyError:
                return(None)
        else:
            if self.refresh_update_requests:
                return self.refresh_update_requests.popitem()
            else:
                self.refresh_update_requests = None
                return((None,None))

