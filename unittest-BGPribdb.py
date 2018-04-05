#!/usr/bin/python3

TC=10
import random
import BGPribdb
import bgpparse

class Object():
    pass

class Test():
    __init(self)__:

        self.test_prefixes=[]
        self.test_paths=[]
        for i in range(100):
            path = Object()
            path.a = random.randint(0,0xffffffff)
            path.b = random.randint(0,0xffffffff)
            test_paths.append(path)

    def get_test_path():
        return random.choice(self.test_paths)


    def get_new_test_prefix():
        prefix = ( random.randint(0,0xffffffff), random.randint(0,32))
        self.test_prefixes.append(prefix)
        return prefix

    def get_old_test_prefix():
        return random.choice(self.test_prefixes)

    def rmv_old_test_prefix():
        if self.test_prefixes:
            item = random.choice(self.test_prefixes)
            self.test_prefixes.remove(item)
            return item
        else:
            print("rmv_old_test_prefix returns None")
            return None

    def insert_test(rib):
        print("******inserting test")
        for i in range(TC):
            path = self.get_test_path()
            prefixes = []
            for j in range(random.randint(1,10)):
                prefixes.append(self.get_new_test_prefix())
            rib.update(path,prefixes)

    def update_test(rib):
        print("******updating test")
        for i in range(TC):
            path = self.get_test_path()
            prefixes = []
            for j in range(random.randint(1,10)):
                prefixes.append(self.get_old_test_prefix())
            rib.update(path,prefixes)

    def withdraw_test(rib):
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

    def request_test(rib):
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
    insert_test(rib)
    #update_test(rib)
    #withdraw_test(rib)
    request_test(rib)
    print("End BGPribdb Unit tests")

main()
