#!/usr/bin/python3

TC=10 # default seed count for testing
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
        #self.test_prefixes_removed=[]
        #self.test_prefixes_updated=[]
        self.test_paths=[]
        for i in range(path_count):
            self.test_paths.append(self.make_path())
        for i in range(pfx_count):
            self.test_prefixes[self.make_prefix()] = random.choice(self.test_paths)

    def make_path(self):
        path = Object()
        path.a = random.randint(0,0xffffffff)
        path.b = random.randint(0,0xffffffff)
        return path

    def make_prefix(self):
        return ( random.randint(0,0xffffffff), random.randint(0,32))

    # refresh the whole RIB with updates
    def refresh_test(self,rib):
        print("******refresh test")
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

    def test1(rq_size,count):
        print("*** Test 1 rq_size=%d count=%d")
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

    def test2():
        print("*** Test 2")
        print("testing the withdraw function")
        print(rib)

    def test3():
        print("*** Test 3")
        print("loop testing the refresh function")
        print(rib)

    def test4():
        print("*** Test 2")
        print("testing the reinsert function")
        print(rib)

    def testx():
        print("*** Test x")
        print(rib)

    start_time = time.perf_counter()
    test=Test(tc,min(10,int(tc/20)))
    print("BGPribdb Unit tests")
    rib = BGPribdb.BGPribdb()
    test1(int(tc/10),10)
    #test2()
    #test3()
    #test4()
    elapsed_time = time.perf_counter()-start_time
    print("End BGPribdb Unit tests")
    print("TC was %d, time was %f, time/TC=%fuS" % (tc,elapsed_time,elapsed_time/tc*1000000))

tc = TC
if len(sys.argv) > 1:
    try:
        tc = int(sys.argv[1])
    except:
        tc = TC
main(tc)
