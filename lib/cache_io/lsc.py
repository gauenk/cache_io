"""
#!/usr/bin/python3.8
"""

import sys,glob,os
import argparse
from pathlib import Path
from easydict import EasyDict as edict
# sys.path.append("/home/gauenk/Documents/experiments/cl_gen/lib/")
from .uuid_cache import UUIDCache,print_config
from . import view

def parse():
    desc = 'List experiment configs',
    parser = argparse.ArgumentParser(
        prog = 'Commandline to inspect experiment configs',
        description = desc,
        epilog = 'Happy Hacking')
    parser.add_argument("cache_name",type=str,
                        help="The path to directory of the uuid file")
    parser.add_argument("--cache_version",type=str,default="v1",
                        help="The version of the uuid")
    parser.add_argument("--raw",action="store_true",
                        help="View raw cache output")
    parser.add_argument("--only_uuids",action="store_true",
                        help="View only uuids")
    parser.add_argument("--uuids",nargs="+",default=[])
    args = parser.parse_args()
    return edict(vars(args))

def get_uuids(uuids,cache):
    if len(uuids) == 0:
        return cache.data['uuid']
    else:
        return uuids

def view_only_uuids(uuid_l):
    for i,uuid in enumerate(uuid_l):
        print(i,uuid)

def main():

    # if len(sys.argv) < 3:
    #     print("lsc allows users to quickly read cache info.")
    #     print("Usage: lsc [path_to_json_dir] [optional:[glob of] uuids]")
    #     exit()

    # try:
    #     name = float(sys.argv[1])
    # except:
    #     name = sys.argv[1]
    #     # print("lsc recommends the second argument be a float.")
    #     # exit()
    # cache_name = args.cache_name
    # root = Path(sys.argv[2])

    # -- parse --
    args = parse()

    # -- load cache --
    cache = UUIDCache(args.cache_name,args.cache_version)

    # -- report DNE --
    if not cache.uuid_file.exists():
        print(f"lsc detects the UUID cache name [{args.cache_name}] does not exist.")
        exit()

    # -- collect configs from paths --
    uuids = args.uuids
    if args.only_uuids:
        view_only_uuids(uuids)
        return
    raw = args.raw or (len(cache.data['config']) == 1 ) or (len(uuids) <= 1)
    if len(uuids) == 0:
        print("No uuids selected so printing UUID Database")
        uuids = cache.data['uuid']

    # -- load configs --
    cfgs = cache.get_config_from_uuid_list(uuids)

    if raw:
        for uuid,cfg in zip(uuids,cfgs):
            print("-="*35)
            print(f"[UUID]: {uuid}")
            print_config(cfg,indent=8)
    else:
        # cfgs = cache.data['config']
        #cfgs = [cfg for cfg in cfgs if cfg.nepochs == 100]
        # uuids = view.get_uuids(cfgs,cache)
        # print(uuids)
        # print(uuids)
        # exit(0)
        # if use_sel_uuids:
        #     uuids = [u for u in uuids if u in uuids]
        diffs = view.get_diffs(cfgs)
        view.print_loop(cfgs,uuids,diffs)
        # view.run(cache.data['cfgs'],cache)
