"""

Print only diffs from all configs

"""

# -- unique --
import numpy as np
from easydict import EasyDict as edict

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

def pair(cfgs,uuids):
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
    # print(diffs)
    return diffs

def find_dups(cfgs,uuids):

    # -- get diff fields --
    diffs = get_diffs(cfgs)

    # -- only diff fields
    dcfgs = [edict() for _ in cfgs]
    for i,cfg in enumerate(cfgs):
        for k in cfg:
            dcfgs[i][k] = cfg[k]

    # -- pairwise difference --
    L = len(cfgs)
    pairs = np.zeros((L,L),dtype=np.bool)
    for i,cfg_i in enumerate(dcfgs):
        for j,cfg_j in enumerate(dcfgs[:i]):
            if i != j:
                cmp_ij = match(cfg_i,cfg_j)
            else:
                cmp_ij = False
            pairs[i,j] = cmp_ij
            pairs[j,i] = pairs[i,j]

    # -- find duplicates (if any) --
    dups = {}
    for i,uuid in enumerate(uuids):
        inds_i = np.where(pairs[i] > 0)[0].tolist()
        # if i < 10:
        #     print(inds_i)
        #     print("i,inds_i.shape: ",i,inds_i.shape)
        dups[uuid] = []
        for ind in inds_i:
            if ind == i: continue
            dups[uuid].append(uuids[ind])

    # -- drop uuids if empty --
    pairs = [(uuid,u_dups) for uuid,u_dups in dups.items()]
    for (uuid,u_dups) in pairs:
        if len(u_dups) == 0:
            del dups[uuid]

    return dups

def match(cfg0,cfg1):
    diffs = compare(cfg0,cfg1)
    diffs += compare(cfg1,cfg0)
    return len(diffs) == 0

def compare(cfg0,cfg1):
    diffs = []
    for key in cfg0:
        if not(key in cfg1):
            diffs.append(key)
            continue
        if cfg0[key] != cfg1[key]:
            diffs.append(key)
    return diffs
