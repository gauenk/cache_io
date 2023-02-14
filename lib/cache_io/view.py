"""

Print only diffs from all configs

"""

# -- unique --
import numpy as np

# -- uuids --
from .exp_cache import ExpCache

# -- printing --
import pprint
pp = pprint.PrettyPrinter(indent=4)

def run(cfgs,cache_name,cache_version="v1"):
    cache = ExpCache(cache_name,cache_version)
    uuids = get_uuids(cfgs,cache)
    diffs = get_diffs(cfgs)
    print_loop(cfgs,uuids,diffs)

def print_loop(cfgs,uuids,diffs):
    for i,cfg in enumerate(cfgs):
        fmt = "-="*8 + "-" + " [%d] %s " + "-="*8+"-"
        print(fmt % (i,uuids[i]))
        cfg_view = {}
        for d in diffs:
            if d in cfg:
                cfg_view[d] = cfg[d]
            else:
                cfg_view[d] = None
        pp.pprint(cfg_view)

def get_uuids(cfgs,cache):
    uuids = []
    for cfg in cfgs:
        uuid_i = cache.get_uuid(cfg)
        uuids.append(uuid_i)
    return uuids

def get_diffs(cfgs):
    diffs = []
    cfg_prev = None
    for i,cfg in enumerate(cfgs):

        # -- init --
        if i == 0: 
            cfg_prev = cfg
            continue

        # -- main --
        diffs_i = compare(cfg_prev,cfg)
        diffs_i += compare(cfg,cfg_prev)
        diffs.extend(np.unique(diffs_i))

    # -- unique --
    diffs = np.unique(diffs)
    print(diffs)
    return diffs

def compare(cfg0,cfg1):
    diffs = []
    for key in cfg0:
        if not(key in cfg1):
            diffs.append(key)
            continue
        if cfg0[key] != cfg1[key]:
            diffs.append(key)
    return diffs
