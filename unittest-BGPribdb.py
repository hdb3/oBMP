#!/usr/bin/python3

RS=1000 # default RIB size for testing
import random
import BGPribdb
import bgpparse
import sys
import time

class Object():
    pass

class Test():
    def __init__(self,pfx_count,path_count):

        self.test_prefixes={}
        self.test_paths=[]
        for i in range(path_count):
            self.test_paths.append(self.make_path())
        for i in range(pfx_count):
            prefix = self.make_prefix()

            # for large numbers random somtimes means duplicate!
            # so check and discard....
            while prefix in self.test_prefixes:
                prefix = self.make_prefix()
            self.test_prefixes[prefix] = random.choice(self.test_paths)

    def make_path(self):
        path = Object()
        path.a = random.randint(0xffff,0xffffffff)
        path.b = random.randint(0xffff,0xffffffff)
        path.h = hex(hash(path.a ^ path.b))
        return path

    def make_prefix(self):
        return ( random.randint(0,0xffffffff), random.randint(8,32))

    # refresh the whole RIB with updates
    def populate_rib(self,rib):
        print("******populate RIB with initial content")
        paths={}
        for prefix in self.test_prefixes.keys():
           path = self.test_prefixes[prefix] 
           if path not in paths:
               paths[path]=[prefix]
           else:
               paths[path].append(prefix)
        for path in paths.keys():
            rib.update(path,paths[path])

    def update_test(self,rib,count,withdraw=False):
        if withdraw:
            print("******withdraw test")
            path = None
        else:
            print("******update test")
            path = random.choice(self.test_paths)
        prefixes = []
        assert count < len(self.test_prefixes)
        for prefix in random.sample(list(self.test_prefixes),count):
            self.test_prefixes[prefix] = path
            prefixes.append(prefix)
        if withdraw:
            rib.withdraw(prefixes)
        else:
            rib.update(path,prefixes)

    def withdraw_test(self,rib,count):
        self.update_test(rib,count,withdraw=True)

    def refresh_request(self,rib):
        print("******request full refresh")
        rib.refresh()

    def update_request(self,rib):
        print("******request updates test")
        update=rib.get_update_request()
        update_count = 0
        update_pfx_count = 0
        withdraw_pfx_count = 0
        end_of_RIB = False
        while update:
            if update:
                (path,pfxs)=update
                update_count += 1
                if path:
                    update_pfx_count += len(pfxs)
                elif pfxs:
                    withdraw_pfx_count += len(pfxs)
                else:
                    end_of_RIB = True
            update=rib.get_update_request()

        print("update_count %d" % update_count)
        print("update_pfx_count %d" % update_pfx_count)
        print("withdraw_pfx_count_pfx_count %d" % withdraw_pfx_count)
        print("end_of_RIB %s" % end_of_RIB)


def main(test_no,rs,rq_size):

    def test0():
        print("*** Test 0")
        print("simplest test of all - create the RIB, inspect it")
        test.populate_rib(rib)
        print(rib)

    def test1():
        print("*** Test 1")
        print("refresh request test - create the RIB, make a request with no updates, signal refresh, repaet the request")
        test.populate_rib(rib)
        print(rib)
        test.update_request(rib)
        print(rib)
        test.refresh_request(rib)
        print(rib)
        test.update_request(rib)
        print(rib)

    def test2(rq_size,count):
        print("*** Test 2 rq_size=%d count=%d" % (rq_size,count))
        test.populate_rib(rib)
        print(rib)
        for c in range(count):
            test.update_test(rib,rq_size)
            test.withdraw_test(rib,rq_size)

        print(rib)
        test.update_request(rib)
        print(rib)
        test.refresh_request(rib)
        print(rib)
        test.update_request(rib)
        print(rib)

    def test3(rq_size):
        print("*** Test 2 %d" % rq_size)
        print("testing the withdraw function")
        test.populate_rib(rib)
        print(rib)
        test.withdraw_test(rib,rq_size)
        print(rib)
        test.update_request(rib)
        print(rib)

    start_time = time.perf_counter()
    test=Test(rs,max(10,int(rs/20)))
    print("BGPribdb Unit tests")
    rib = BGPribdb.BGPribdb()
    if test_no == 0:
        test0()
    elif test_no == 1:
        test1()
    elif test_no == 2:
        test2(rq_size,10)
    elif test_no == 3:
        test3(rq_size)
    else:
        sys.stderr.write("oops there is something wrong withthe test no requested")

    #test0()
    #test1()
    #test2(rq_size,10)
    #test3(rq_size)
    #test3()
    elapsed_time = time.perf_counter()-start_time
    print("End BGPribdb Unit tests")
    print("RS was %d, time was %f, time/RS=%fuS" % (rs,elapsed_time,elapsed_time/rs*1000000))

if len(sys.argv) > 1:
    try:
        test_no = int(sys.argv[1])
    except:
        test_no = 0
else:
    test_no = 0

if len(sys.argv) > 2:
    try:
        rs = int(sys.argv[2])
    except:
        rs = RS
else:
    rs = RS

if len(sys.argv) > 3:
    try:
        rq_size = int(sys.argv[3])
    except:
        rq_size = min(10,int(rs/10))
else:
        rq_size = min(10,int(rs/10))

main(test_no,rs,rq_size)
