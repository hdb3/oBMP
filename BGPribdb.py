
# BGPribdb.py
#
# a threadsafe BGP RIB for a router
#

import threading

class BGPribdb:
    def __init__(self):
        self.db_lock = threading.Lock()
        self.rib = {}
        self.path_attributes = {}
        self.update_requests = {}
        self.path_update_requests = {}
        self.path_update_requests[None] = []

        # refresh_update_requests is a list whilst refresh operation is in progress
        # when it is an empty list then it is time to send end-of-RIB, after which it is set None
        self.refresh_update_requests = None

    def __str__(self):


        # calculate the global update state
        pa_hashes_in_update = 0
        prefixes_in_update = 0
        prefixes_in_withdraw = 0
        pa_hashes = {}
        for (pfx,pa_hash) in self.update_requests:
            if pa_hash:
                prefixes_in_update += 1
            else:
                prefixes_in_withdraw += 1
            if not pa_hash in pa_hashes:
                pa_hashes[pa_hash] = 1
            else:
                pa_hashes[pa_hash] += 1




        # calculate the per path update state
        path_pa_hashes_in_update = 0
        path_prefixes_in_update = 0
        path_prefixes_in_withdraw = 0
        for (pa_hash,pfxlist) in self.path_update_requests.items():
            path_pa_hashes_in_update += 1
            if pa_hash:
                path_prefixes_in_update += len(pfxlist)
            else:
                path_prefixes_in_withdraw += len(pfxlist)

        return "**BGPribdb state**" + \
\
               "\n  rib size =" + str(len(self.rib)) + \
               "\n  paths in rib =" + str(len(self.path_attributes)) + \
\
               "\n  *global view* paths in update =" + str(pa_hashes_in_update) + \
               "\n  *global view* prefixes in update =" + str(prefixes_in_update) + \
               "\n  *global view* prefixes in withdraw =" + str(prefixes_in_withdraw) + \
\
               "\n  *path view* paths in update =" + str(path_pa_hashes_in_update) + \
               "\n  *path view* prefixes in update =" + str(path_prefixes_in_update) + \
               "\n  *path view* prefixes in withdraw =" + str(path_prefixes_in_withdraw)

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
        return hash(pickle.dumps(simple, protocol=pickle.HIGHEST_PROTOCOL))

    def atomic_update(self,pfx,pa_hash):

        # ALWAYS update the main RIB
        # UNLESS the RIB is unchanged schedule update sending
        if pa_hash not in self.rib or self.rib[pfx] != pa_hash:
            self.rib[pfx] = pa_hash
            self.path_update_requests[pa_hash].append(pfx)
            self.update_requests[pfx] = pa_hash
        else:
            # it's not expected that a duplce insert occurs
            # it's not a problem and it does not call for an UPDATE to be sent
            sys.stder.write("\n*** Unexpected duplicate inset for %s/%s\n" % (self.show_pfx(pfx),pa_hash))
            # pass

    def atomic_withdraw(self,pfx):
        self.atomic_update(pfx,None)

    def update(self,pa,pfx_list):
        self.lock()
        pa_hash = hash(pa)
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
        self.path_update_requests = {}
        self.path_update_requests[None] = []
        for (pfx,pa_hash) in self.rib.items():
            # don't put withdraws into the refresh table
            if pa_hash:
                if pa_hash not in self.refresh_update_requests:
                    self.refresh_update_requests[pa_hash] = []
                self.refresh_update_requests = [pa_hash].append(pfx)
        self.unlock()

    # consume API
    #
    # withdraw request objects and update request objects have the same structure, with the Path Attribute field None in the case of withdraw
    #
    # refresh request returns first items from the refresh list , then from the normal list, 
    # the last item from a refresh list is (None,None), which signals 'end-of-RIB'
    #
    # if there are no items in either list then the return value is simply 'None'

    def old_groom_updates(self,pa_hash,pfxlist):
        new_pfxlist=[]
        for pfx in pfxlist:
            ## debug code
            if not pa_hash:## debug code
                pa_tmp1 = 0## debug code
            else:## debug code
                pa_tmp1 = pa_hash## debug code
            if not self.rib[pfx]:## debug code
                pa_tmp2 = 0## debug code
            else:## debug code
                pa_tmp2 = self.rib[pfx]  ## debug code
            ## end debug code
            if self.rib[pfx] == pa_hash:
                new_pfxlist.append(pfx)
                print("groom_updates - using update %s %0X/%0X" % (self.show_pfx(pfx),pa_tmp1,pa_tmp2))## debug code
            else:## debug code
                print("groom_updates - dropping update %s %0X/%0X" % (self.show_pfx(pfx),pa_tmp1,pa_tmp2))## debug code
        return new_pfxlist

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
                return (pa_hash,self.groom_updates(pa_hash,pfxlist))
            except KeyError:
                return(None)
        else:
            if self.refresh_update_requests:
                return self.refresh_update_requests.pop(0)
            else:
                self.refresh_update_requests = None
                return((None,None))

