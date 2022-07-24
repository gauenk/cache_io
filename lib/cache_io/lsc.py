"""
#!/usr/bin/python3.8
"""

import sys,glob,os
from pathlib import Path
# sys.path.append("/home/gauenk/Documents/experiments/cl_gen/lib/")
from .uuid_cache import UUIDCache,print_config

def create_uuid_list_from_glob(path_l,cache):

    # -- unpack a glob --
    uuid_l = []
    # glob_path_l = str(path_l) + "*"
    for filename in path_l:
        uuid_l.append(str(Path(filename).stem))

    # -- if empty; print all uuids --
    # if len(uuid_l) == 0:
    #     uuid_l = list(cache.data['uuid'])

    return uuid_l

def main():

    if len(sys.argv) < 3:
        print("lsc allows users to quickly read cache info.")
        print("Usage: lsc [cache_name] [path_to_json_dir] [optional:[glob of] uuids]")
        exit()

    try:
        name = float(sys.argv[1])
    except:
        name = sys.argv[1]
        # print("lsc recommends the second argument be a float.")
        # exit()

    # -- load cache --
    print(sys.argv)
    cache_name = sys.argv[1]
    root = Path(sys.argv[2])
    cache = UUIDCache(root,cache_name)

    # -- report DNE --
    if not cache.uuid_file.exists():
        print(f"lsc detects the UUID cache name [{name}] does not exist.")
        exit()

    # -- collect configs from paths --
    path_l = sys.argv[3:]
    uuid_l = create_uuid_list_from_glob(path_l,cache)
    config_l = cache.get_config_from_uuid_list(uuid_l)
    # if (len(config_l) == 1 and config_l[0] == -1) or (len(config_l) == 0):
    if len(config_l) == 0:
        print("No uuids selected so printing UUID Database")
        for index,uuid in enumerate(cache.data['uuid']):
            config = cache.data['config'][index]
            print("-="*35)
            print(f"[UUID]: {uuid}")
            print_config(config,indent=8)
    else:
        # -- print results --
        pidx = 0
        for uuid,config in zip(uuid_l,config_l):
            if config != -1:
                print("-="*35)
                if len(path_l) > pidx: print(f"Path: {path_l[pidx]}")
                print(f"[UUID]: {uuid}")
                print_config(config,indent=8)
