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
    # print("Very Fast.")
    # print("skip_results: ",skip_results)
    if len(dst.uuid_cache.data['config']) > 0:
        print("Warning: Destination should be an empty or the uuids should match.")

    # -- reset --
    if reset:
        dst.uuid_cache.write_uuid_file({"config":[],"uuid":[]})

    # -- copy each source cache --
    uuids,cfgs,results = [],[],[]
    cnt = 0
    for src_name in tqdm.tqdm(src_list):
        src = ExpCache(src_name,version)
        uuid_data = src.uuid_cache.data
        uuids = uuid_data['uuid']
        cfgs = uuid_data['config']
        cnt += copy_results(dst,src.root,uuids,cfgs,links_only=links_only)
    print("Total Number of Exps Copied: %d" % cnt)


def copy_results(dst,src_root,src_uuids,src_cfgs,links_only=False):

    # -- include all (uuid,cfg) pairs --
    dst_cfgs = dst.uuid_cache.data['config']
    dst_uuids = dst.uuid_cache.data['uuid']
    for uuid,cfg in zip(src_uuids,src_cfgs):
        if uuid in dst_uuids: continue
        dst_uuids.append(uuid)
        dst_cfgs.append(cfg)
    dst.uuid_cache.write_uuid_file({"config":dst_cfgs,"uuid":dst_uuids})

    # -- copy the uuid results --
    cnt = 0
    for uuid in dst_uuids:
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
    return cnt

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

