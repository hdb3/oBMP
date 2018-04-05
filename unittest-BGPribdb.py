#!/usr/bin/python3

TC=10
import random
import BGPribdb
import bgpparse

class Object():
    pass

class Test():
    def __init__(self):

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
        for i in range(TC):
            path = self.get_test_path()
            prefixes = []
            for j in range(random.randint(1,10)):
                prefixes.append(self.get_new_test_prefix())
            rib.update(path,prefixes)

    def update_test(self,rib):
        print("******updating test")
        for i in range(TC):
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
        while update:
            update=rib.get_update_request()
            if update:
                (path,pfxs)=update
                update_count += 1
                update_pfx_count += len(pfxs)

        print("update_count %d" % update_count)
        print("update_pfx_count %d" % update_pfx_count)


def main():
    test=Test()
    print("BGPribdb Unit tests")
    rib = BGPribdb.BGPribdb()
    test.insert_test(rib)
    print(rib)
    #test.update_test(rib)
    #test.withdraw_test(rib)
    test.request_test(rib)
    print("End BGPribdb Unit tests")

main()
