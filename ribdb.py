
# ribdb.py
#
# a threadsafe RIB for a router
#

#
# an enhanced dictionary
# added items are marked as unread
# deleted items already marked as read are kept until the delete is also read
# deleting an unread item discrads it immediately
# reading added items marks them as read
# so that they will not be read again unless a refresh is requested
# reading deleted items causes them to be finally discarded
#
# implementation
#
# updates are initially stored in one dictionary, and moved to another when they have been read
# read requiests are only taken from the unread dict
# if a refresh is requested then the read and unread dicts are merged into a third dict
# which is emptied first to allow sending end-of-RIB
#
# when an update for an existing read item arrives then the read item is discarded immediately from the read dict
# when an update for an existing unread item arrives then the read item is discarded immediately from the unread dict (i.e. simple replacement)
# when an update for an existing deleted item arrives then the deleted item is discarded immediately from the deleted dict
# the net effect is that an item key may only exist in one queue/dict
# when an update arrives during a refresh then an existing item in refresh should be replaced (or deleted and the new item put in unread)
#
# deleted items
#
# deletes are applied directly/immeditately to the unread dict
# deletes on the read dict push items into a delete dict
# reads from the delete dict lead to discard
# on refresh the delete dict is dropped
#
# note - the above system does not maintain ordering between add and delete
# if this or ANY OTHER ordering is required then queues are needed
# 
# reading
#
# a read request can return either deletes or adds
# the question of whether to process deletes or adds first is for the application to decide
# deletes first could be better for service
# adds first might reduce overall processing
# note reading during refresh will only return adds as deletes are actioned immeditaley
#
#refresh
#
# refresh merges the read and unread dicts and discards the delete dict
# if a second refresh occurs before the first one completes then
# any new items will be in unread, and a further merge will be effective
# note any deletes will have been actioned already
#
# this implementation using multiple dictionaries is simple
# not preserving time order may be untypical
# it is probably as time and CPU efficient as matters given python
# an alternate would be a single dictionary, with an additional state value for each entry
# supplemented by a work queue
# the challenge with this would be handling multiple quedue actions for a single item
# i.e. a work item at the head of the queue might be superseeded by a later item
# it would need to use the item state value to resolve this
# it leaves the question whether the following action should be deferred or actioned
# if order preservation matters then deferral....
#

class RIBdb:
    def __init__(self):
        self.unsent_rib = {}
        self.sent_rib = {}
        self.withdraw_rib = {}
        self.refresh_rib = {}

    def atomic_update(self,k,v):

        # an update _always_ goes into the unread queue
        # if the same key is present in read,refresh or delete queues then it should be removed from them
        # the deletes can be cascaded in any order as the first success obviates the need for any others
        # when an update for an existing read item arrives then the read item is discarded immediately from the read dict

        self.unsent_rib[k] = v
        try:
            del self.sent_rib[k]
        except KeyError:
            # when an update for an existing deleted item arrives then the deleted item is discarded immediately from the deleted dict
            try:
                del self.withdraw_rib[k]
            except KeyError:
                try:
                    del self.refresh_rib[k]
                except KeyError:
                    pass

    def atomic_withdraw(self,k):
        # delete has effect on zero or one queue
        # all queues must be checked if an item is not present
        # once found, no other queues need be checked
        # a delete from the read queue removes an item from rib.read and adds the value to rib.deleted
        # delete from any other queue does not require further action
        try:
            del self.sent_rib[k]
        except KeyError:
            try:
                del self.unsent_rib[k]
            except KeyError:
                try:
                    del self.refresh_rib[k]
                except KeyError:
                    pass
        else:
            self.withdraw_rib[k] = None

    def update(self,k_v_list):
        self.lock()
        for (k,v) in k_v_list:
            self.atomic_update(k,v)
        self.unlock()

    def withdraw(self,k_list):
        self.lock()
        for k in k_list.keys():
            self.atomic_withdraw(k)
        self.unlock()

    def refresh(self):
        self.lock()
        item_count = len(self.sent_rib) + len(self.unsent_rib) + len(self.refresh_rib)
        self.withdraw_rib = {}
        tmp_read = self.sent_rib
        self.sent_rib = {}
        tmp_unread = self.unsent_rib
        self.unsent_rib = {}
        self.refresh_rib.update(tmp_read)
        self.refresh_rib.update(tmp_unread)
        assert len(self.refresh_rib) = item_count
        self.unlock()

    # consume API
    #
    # there are three sources - refresh, unsent and withdrawn
    # the consumer might have a preference a between unsent and withdrawn
    # and needs to distinguish refresh from unsent in order to implement end-of-RIB
    #
    # during refresh there can be no withdraws, and refresh takes precedence over unsent
    # so the only question is which policy to apply between unsent and withdrawn
    # By providing a separate method for withdraw and update (which is either unsent or refresh) the consumer may choose
    # a simple 'refresh active' flag allows the consumer to implement End-of-RIB
    # distinction between update and withdraw is simple too....
    # a null value is a withdraw
    #
    # so the API is a simple get
