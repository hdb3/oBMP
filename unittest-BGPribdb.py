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
        self.test_prefixes_removed=[]
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

    def get_rmvd_test_prefix(self):
        return random.choice(self.test_prefixes_removed)

    def rmv_old_test_prefix(self):
        if self.test_prefixes:
            item = random.choice(self.test_prefixes)
            self.test_prefixes.remove(item)
            self.test_prefixes_removed.append(item)
            return item
        else:
            print("rmv_old_test_prefix returns None")
            return None

    def reinsert_test(self,rib):
        print("******reinserting test")
        for i in range(tc):
            path = self.get_test_path()
            prefixes = []
            for j in range(random.randint(1,10)):
                prefixes.append(self.get_rmvd_test_prefix())
            rib.update(path,prefixes)

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
                try:
                    prefixes.append(self.get_old_test_prefix())
                except IndexError:
                    break
            rib.update(path,prefixes)

    def withdraw_test(self,rib):
        print("******withdrawing test")
        for i in range(tc):
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

    def withdraw_all_test(self,rib):
        print("******withdrawing all test")
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

    def refresh_test(self,rib):
        print("******refresh test")
        rib.refresh()


    def request_test(self,rib):
        print("******request updates test")

        update=rib.get_update_request()
        update_count = 0
        update_pfx_count = 0
        withdraw_pfx_count = 0
        end_of_RIB = False
        while update:
            update=rib.get_update_request()
            if update:
                (path,pfxs)=update
                update_count += 1
                if path:
                    update_pfx_count += len(pfxs)
                elif pfxs:
                    withdraw_pfx_count += len(pfxs)
                else:
                    end_of_RIB = True

        print("update_count %d" % update_count)
        print("update_pfx_count %d" % update_pfx_count)
        print("withdraw_pfx_count_pfx_count %d" % withdraw_pfx_count)
        print("end_of_RIB %s" % end_of_RIB)


def main(tc):

    def test1():
        print("*** Test 1")
        print("testing the refresh function")
        test.insert_test(rib)
        test.request_test(rib)
        test.request_test(rib)
        test.refresh_test(rib)
        print(rib)
        test.request_test(rib)
        test.request_test(rib)

    def test2():
        print("*** Test 2")
        print("testing the withdraw function")
        test.insert_test(rib)
        test.withdraw_test(rib)
        test.insert_test(rib)
        test.withdraw_test(rib)
        test.reinsert_test(rib)
        test.withdraw_test(rib)
        test.insert_test(rib)
        test.update_test(rib)
        test.withdraw_test(rib)
        test.reinsert_test(rib)
        test.update_test(rib)
        print(rib)
        test.withdraw_all_test(rib)
        print(rib)

    def test3():
        print("*** Test 3")
        print("loop testing the refresh function")
        for i in range(10):
            test.insert_test(rib)
            test.request_test(rib)
            test.refresh_test(rib)
            test.insert_test(rib)
            test.request_test(rib)
            test.insert_test(rib)
            test.refresh_test(rib)
            test.request_test(rib)
        print(rib)

    def test4():
        print("*** Test 2")
        print("testing the reinsert function")
        test.insert_test(rib)
        test.withdraw_test(rib)
        print(rib)
        test.reinsert_test(rib)
        #test.update_test(rib)
        #test.withdraw_test(rib)
        #test.reinsert_test(rib)
        print(rib)

    def testx():
        print("*** Test x")
        #test.insert_test(rib)
        #print(rib)
        #test.update_test(rib)
        #print(rib)
        #test.withdraw_test(rib)
        #print(rib)
        #test.request_test(rib)
        test.insert_test(rib)
        test.request_test(rib)
        test.insert_test(rib)
        test.request_test(rib)
        test.refresh_test(rib)
        test.request_test(rib)
        print(rib)

    start_time = time.perf_counter()
    test=Test(tc)
    print("BGPribdb Unit tests")
    rib = BGPribdb.BGPribdb()
    #test1()
    #test2()
    #test3()
    test4()
    elapsed_time = time.perf_counter()-start_time
    print("End BGPribdb Unit tests")
    print("TC was %d, time was %f, time/TC=%fuS" % (tc,elapsed_time,elapsed_time/tc*1000000))

if len(sys.argv) > 1:
    try:
        tc = int(sys.argv[1])
    except:
        tc = 10
main(tc)
