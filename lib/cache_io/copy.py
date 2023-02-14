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

from .exp_cache import ExpCache
from .exps import get_exps

def enames(name0,version0,name1,version1,exps=None,
           overwrite=False,skip_empty=True):
    src = ExpCache(name0,version0)
    dest = ExpCache(name1,version1)
    exp_cache(src,dest,exps,overwrite,skip_empty)

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

