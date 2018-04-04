#!/usr/bin/python3

import random
import BGPribdb
import bgpparse

class Object():
    pass

def make_test_paths():
    global test_paths
    global test_prefixes
    test_prefixes=[]
    test_paths=[]
    for i in range(10):
        path = Object()
        path.a = random.randint(0,0xffffffff)
        path.b = random.randint(0,0xffffffff)
        test_paths.append(path)

def get_test_path():
    global test_paths
    return random.choice(test_paths)


def get_new_test_prefix():
    global test_prefixes
    prefix = ( random.randint(0,0xffffffff), random.randint(0,32))
    test_prefixes.append(prefix)
    return prefix

def get_old_test_prefix():
    global test_prefixes
    return random.choice(test_prefixes)


print("BGPribdb Unit tests")

make_test_paths()

rib = BGPribdb.BGPribdb()

print (rib)

for i in range(100):
    path = get_test_path()
    prefixes = []
    for j in range(random.randint(1,10)):
        prefixes.append(get_new_test_prefix())

    rib.update(path,prefixes)

print (rib)

update=rib.get_update_request()
while update:
    print(update)
    update=rib.get_update_request()

print (rib)


print("End BGPribdb Unit tests")
