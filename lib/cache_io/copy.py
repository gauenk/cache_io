"""

Copy one cache name to another.


    cache_dir,cache_name = "a","a"
    cache = cache_io.ExpCache(cache_dir,cache_name)
    cache_dir,cache_name = "b","b"
    cache1 = cache_io.ExpCache(cache_dir,cache_name)
    exps = get_list_of_experiments()
    cache_io.copy.exp_cache(cache1,cache,exps)
    # copy from "cache1" to "cache"


    OR


    exps = get_list_of_experiments()
    cache_io.copy.enames("a","a","b","b",exps)

"""

import tqdm
import os
import shutil
from .exp_cache import ExpCache
from .exps import get_exps

def enames(name0,version0,name1,version1,exps=None,
           overwrite=False,skip_empty=True):
    src = ExpCache(name0,version0)
    dest = ExpCache(name1,version1)
    exp_cache(src,dest,exps,overwrite,skip_empty)

def exp_cache_very_fast(src_list,dst,version,skip_results=False,
                        reset=False,links_only=False):
    """
    Copy all from src to dst without checks. 
    Much faster. More dangerous. #YOLO!
    """

    # -- reset --
    if reset:
        dst.uuid_cache.write_uuid_file({"config":[],"uuid":[]})

    # -- warning message --
    if len(dst.uuid_cache.data['config']) > 0:
        print("Warning: Destination should be an empty or the uuids should match.")

    # -- copy each source cache --
    uuids,cfgs = [],[]
    cnt = 0
    for src_name in tqdm.tqdm(src_list):
        src = ExpCache(src_name,version)
        src_data = src.uuid_cache.data
        src_uuids = src_data['uuid']
        src_cfgs = src_data['config']
        cnt_i,cfgs_i,uuids_i = copy_results(dst,src.root,src_uuids,src_cfgs,
                                            reset=reset,links_only=links_only)
        cnt += cnt_i
        cfgs.extend(cfgs_i)
        uuids.extend(uuids_i)
    print("Total Number of Exps Copied: %d" % cnt)

    # -- save pairs --
    dst.uuid_cache.write_uuid_file({"config":cfgs,"uuid":uuids})

def copy_results(dst,src_root,src_uuids,src_cfgs,reset=False,links_only=False):

    # -- include all (uuid,cfg) pairs --
    dst_cfgs = dst.uuid_cache.data['config']
    dst_uuids = dst.uuid_cache.data['uuid']
    if reset:  # no check if reset
        cfgs_i = src_cfgs
        uuids_i = src_uuids
    else:
        cfgs_i,uuids_i = [],[]
        for uuid,cfg in zip(src_uuids,src_cfgs):
            if uuid in dst_uuids: continue
            uuids_i.append(uuid)
            cfgs_i.append(cfg)

    # -- copy the uuid results --
    cnt = 0
    for uuid in src_uuids:#dst_uuids:
        src_path = src_root / uuid
        dst_path = dst.root / uuid
        if not(src_path.exists()):
            continue
        if dst_path.exists(): 
            # print("Destination [%s] exists. Skipping." % dst_path)
            continue
        cnt += 1
        if links_only:
            os.symlink(str(src_path.resolve()),str(dst_path.resolve()))
        else:
            shutil.copytree(src_path,dst_path)
    return cnt,cfgs_i,uuids_i

def exp_cache_fast(src,dest,skip_results=False):
    """
    Copy all from src to dest without checks. 
    Much faster. More dangerous. #YOLO!
    """
    uuids,cfgs,results = src.load_raw_fast(skip_results)
    dest.append_raw_fast(uuids,cfgs,results)

def exp_cache(src,dest,exps=None,overwrite=False,skip_empty=True):
    """
    src,dest: Two ExpCache files
    """
    if exps is None:
        uuids,exps,results = src.load_raw(skip_empty)
    else:
        if not(exps is None):
            exps = get_exps(exps)
        uuids,exps,results = src.load_raw_exps(exps,skip_empty)
    if len(exps) == 0: warn_message(src)
    # print([r is None for r in results])
    # print(uuids)
    # _dev_test(exps,results)
    dest.save_raw(uuids,exps,results,overwrite=overwrite)

def warn_message(src):
    msg = "No source data found.\n"
    msg += f"Check folders at [{src.root}]\n"
    msg += f"Example uuid: [{list(src.uuid_cache.data['uuid'])[0]}]\n"
    print(msg)

# FREELY DELETE ME
# def _dev_test(exps,res):
#     import pandas as pd
#     df = pd.DataFrame(exps)
#     print(df['wt'].unique())
#     print(len(df))
#     print(len(res))

