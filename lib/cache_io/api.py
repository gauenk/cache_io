"""

Functons for API

"""

# -- printing --
import tqdm
import copy
dcopy = copy.deepcopy
import pprint
pp = pprint.PrettyPrinter(indent=4)
import uuid as uuid_gen

# -- cache api --
from .exps import read,get_exps
from .misc import optional
from .exp_cache import ExpCache

# -- dispatch options --
from . import slurm

def run_exps(exp_file_or_list,exp_fxn,name=None,version="v1",clear_fxn=None,
             records_fn=None,records_reload=True,skip_loop=False,verbose=True,
             einds=None,clear=False,uuids=None,preset_uuids=False,
             enable_dispatch=None,merge_dispatch=False,to_records_fast=False,
             results_fxn=None):

    # -- get cache info --
    name,version = cache_info(exp_file_or_list,name=name,version=version)

    # -- get exps --
    exps = get_exps(exp_file_or_list)

    # -- optionally restrict inds using an input parser --
    if not(enable_dispatch is None):
        assert (einds is None),"Indices are selected from dispatch"
        args = [merge_dispatch,einds,clear,name,version,skip_loop,exps]
        einds,clear,name,skip_loop = dispatch(enable_dispatch,*args)

    # -- open & clear cache --
    cache = ExpCache(name,version)
    if clear: cache.clear()

    # -- filter experiments --
    if not(einds is None):
        exps = [exps[i] for i in einds]
        if not(uuids is None):
            uuids = [uuids[i] for i in einds]

    # -- init uuids if needed --
    if uuids is None:
        uuids = [None for _ in exps]

    # -- preset uuids before running exp grid --
    if preset_uuids:
        for exp_num,exp in enumerate(exps):
            cache.get_uuid(exp,uuid=uuids[exp_num])

    # -- run exps --
    nexps = len(exps)
    for exp_num,exp in enumerate(exps):

        # -- optionally skip --
        if skip_loop: break

        # -- logic --
        uuid = cache.get_uuid(exp,uuid=uuids[exp_num]) # assing ID to each Dict in Meshgrid

        # -- info --
        if verbose:
            print("-="*25+"-")
            print(f"Running experiment number {exp_num+1}/{nexps}")
            print("-="*25+"-")
            print("UUID: ", uuid)
            pp.pprint(exp)

        # -- optionally clear --
        if not(clear_fxn is None) and clear_fxn(exp_num,exp):
            cache.clear_exp(uuid)

        # -- load result --
        results = cache.load_exp(exp) # possibly load result

        # -- run exp --
        if results is None: # check if no result
            exp.uuid = uuid
            results = exp_fxn(dcopy(exp))
            cache.save_exp(uuid,exp,results) # save to cache

    # -- records --
    if to_records_fast:
        records = cache.to_records_fast(records_fn,records_reload,results_fxn=results_fxn)
    else:
        records = cache.to_records(exps,records_fn,records_reload,results_fxn=results_fxn)

    return records

def load_results(exps,name,version,records_fn=None,records_reload=True):
    cache = ExpCache(name,version)
    records = cache.to_records(exps,records_fn,records_reload)
    return records

def cache_info(exp_file,name=None,version=None):
    """

    Open ExpCache using the following inputs:
    (1) the kwarg (name,version)
    (2) the exp_file
    """
    if (name is None) or (version is None):
        assert isinstance(exp_file,str),"Must pass the exp file, not exps, if no cache (name & version) pair is provided."
        edata = read(exp_file)
        name = edata['name']
        version = edata['version']
    return name,version#cache

def dispatch(enable_dispatch,*args):
    if enable_dispatch == "slurm":
        outs = slurm.dispatch_process(*args)
    elif enable_dispatch == "split":
        outs = split.dispatch_process(*args)
    else:
        raise ValueError("Uknown dispatch type [%s]" % enable_dispatch)
    return outs

def get_uuids(exps,cache_or_name,version="v1",no_config_check=False,read=True,reset=False):

    # -- open or assign cache --
    if isinstance(cache_or_name,ExpCache):
        cache = cache_or_name
    else:
        cache = ExpCache(cache_or_name,version)

    # -- rest --
    if reset: cache.clear()

    # -- return already assigned --
    nexps = len(exps)
    ncache = len(cache.uuid_cache.data['config'])
    if len(exps) == len(cache.uuid_cache.data['config']) and read:
        exps = cache.uuid_cache.data['config']
        uuids = cache.uuid_cache.data['uuid']
        return exps,uuids
    elif read and nexps > 0 and ncache == 0:
        print("# exps != # cache [%d != %d]. Read after loading once." % (nexps,ncache))
    elif read:
        print("# exps != # cache [%d != %d]. Think about this." % (nexps,ncache))
    if len(cache.uuid_cache.data['config']) > 0 and no_config_check:
        print("Warning: if no_config_check we want an empty uuid_cache.")

    # -- read uuids --
    uuids = []
    for exp in tqdm.tqdm(exps):
        if no_config_check:
            uuid = str(uuid_gen.uuid4())
        else:
            uuid = cache.get_uuid(exp)
        uuids.append(uuid)

    # -- assign uuids --
    if no_config_check:
        cache.uuid_cache.write_uuid_file({"config":exps,"uuid":uuids})
    print("[get_uuids] Completed Writing.")

    return exps,uuids

