
# BGPribdb.py
#
# a threadsafe BGP RIB for a router
#

class BGPribdb:
    def __init__(self):
        self.rib = {}
        self.path_attributes = {}
        self.path_update_requests = {}
        self.update_requests = {}
        self.update_requests[None] = []

        # refresh_update_requests is a list whilst refresh operation is in progress
        # when it is an empty list then it is time to send end-of-RIB, after which it is set None
        self.refresh_update_requests = None

    @staticmethod
    def path_attribute_hash(pa):
        return hash(pickle.dumps(simple, protocol=pickle.HIGHEST_PROTOCOL))

    def atomic_update(self,pfx,pa_hash):

        # ALWAYS update the main RIB
        # UNLESS the RIB is unchanged schedule update sending
        if self.rib[pfx] != pa_hash:
            self.rib[pfx] = pa_hash
            self.path_update_requests[pa_hash].append(pfx)

    def atomic_withdraw(self,k):
        atomic_update(self,pfx,None):

    def update(self,pa,pfx_list):
        self.lock()
        pa_hash = hash(pa)
        if pa_hash not in self.path_attributes:
            self.path_attributes[pa_hash] = pa
            self.refresh_update_requests[pa_hash] = []
        for pfx in pfx_list:
            self.atomic_update(pfx,pa_hash)
        self.unlock()

    def withdraw(self,k_list):
        self.lock()
        for pfx in pfx_list.keys():
            self.atomic_withdraw(pfx)
        self.unlock()

    def refresh(self):
        self.lock()
        self.path_update_requests = {}
        for (pfx,pa_hash) in self.rib.items()
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

    def get_update_request(self):
        if self.refresh_update_requests is None:
            if self.refresh_update_requests:
                return self.refresh_update_requests.pop(0)
            else:
                self.refresh_update_requests = None
                return((None,None))
        elif self.update_requests[None]:
            return (None,self.update_requests.pop(None))
        else:
            return self.update_requests.popitem()


