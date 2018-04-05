#!/usr/bin/python3

import random
import BGPribdb
import bgpparse
import sys
import time

class Object():
    pass

class Test():
    def __init__(self,tc):

        self.tc = tc
        self.test_prefixes=[]
        self.test_paths=[]
        for i in range(100):
            path = Object()
            path.a = random.randint(0,0xffffffff)
            path.b = random.randint(0,0xffffffff)
            self.test_paths.append(path)

    def get_test_path(self):
        return random.choice(self.test_paths)


    def get_new_test_prefix(self):
        prefix = ( random.randint(0,0xffffffff), random.randint(0,32))
        self.test_prefixes.append(prefix)
        return prefix

    def get_old_test_prefix(self):
        return random.choice(self.test_prefixes)

    def rmv_old_test_prefix(self):
        if self.test_prefixes:
            item = random.choice(self.test_prefixes)
            self.test_prefixes.remove(item)
            return item
        else:
            print("rmv_old_test_prefix returns None")
            return None

    def insert_test(self,rib):
        print("******inserting test")
        for i in range(tc):
            path = self.get_test_path()
            prefixes = []
            for j in range(random.randint(1,10)):
                prefixes.append(self.get_new_test_prefix())
            rib.update(path,prefixes)

    def update_test(self,rib):
        print("******updating test")
        for i in range(tc):
            path = self.get_test_path()
            prefixes = []
            for j in range(random.randint(1,10)):
                prefixes.append(self.get_old_test_prefix())
            rib.update(path,prefixes)

    def withdraw_test(self,rib):
        print("******withdrawing test")
        while True:
            prefixes = []
            for j in range(random.randint(1,10)):
                pfx=self.rmv_old_test_prefix()
                if pfx:
                    prefixes.append(pfx)
                else:
                    break
            if prefixes:
                rib.withdraw(prefixes)
            else:
                break

    def request_test(self,rib):
        print("******request updates test")

        update=rib.get_update_request()
        update_count = 0
        update_pfx_count = 0
        withdraw_pfx_count = 0
        while update:
            update=rib.get_update_request()
            if update:
                (path,pfxs)=update
                update_count += 1
                if path:
                    update_pfx_count += len(pfxs)
                else:
                    withdraw_pfx_count += len(pfxs)

        print("update_count %d" % update_count)
        print("update_pfx_count %d" % update_pfx_count)
        print("withdraw_pfx_count_pfx_count %d" % withdraw_pfx_count)


def main(tc):
    start_time = time.perf_counter()
    test=Test(tc)
    print("BGPribdb Unit tests")
    rib = BGPribdb.BGPribdb()
    test.insert_test(rib)
    print(rib)
    test.update_test(rib)
    print(rib)
    test.withdraw_test(rib)
    print(rib)
    test.request_test(rib)
    test.insert_test(rib)
    test.update_test(rib)
    test.request_test(rib)
    print(rib)

    elapsed_time = time.perf_counter()-start_time
    print("End BGPribdb Unit tests")
    print("TC was %d, time was %f, time/TC=%fuS" % (tc,elapsed_time,elapsed_time/tc*1000000))

if len(sys.argv) > 1:
    try:
        tc = int(sys.argv[1])
    except:
        tc = 10
main(tc)
