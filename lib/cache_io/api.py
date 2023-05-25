"""

Functons for API

"""

# -- printing --
import os,tqdm
import copy
dcopy = copy.deepcopy
import pprint
pp = pprint.PrettyPrinter(indent=4)
import uuid as uuid_gen
from pathlib import Path

# -- wandb --
import copy
dcopy = copy.deepcopy
import numpy as np
import pandas as pd
try:
    import wandb
except:
    pass

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
             results_fxn=None,proj_name="match_me",use_wandb=True):

    # -- get cache info --
    name,version = cache_info(exp_file_or_list,name=name,version=version)

    # -- get exps --
    exps = get_exps(exp_file_or_list)

    # -- wandb defaults --
    if proj_name == "match_me":
        proj_name = "wandb_%s" % ("_".join(name.split("/")[1:]))

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

    # -- rank for logging --
    NODE_RANK = int(os.environ.get('NODE_RANK', 0))

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
            if use_wandb and NODE_RANK == 0:
                run = wandb.init(id=uuid,
                                 project=proj_name,
                                 config=wandb_format_exp(exp),
                                 resume="allow")
            results = exp_fxn(exp)
            if use_wandb:
                wandb.log(wandb_format(results))
                wandb.finish()
            cache.save_exp(uuid,exp,results) # save to cache

    # -- records --
    if to_records_fast:
        records = cache.to_records_fast(records_fn,records_reload,results_fxn=results_fxn)
    else:
        records = cache.to_records(exps,records_fn,records_reload,results_fxn=results_fxn)

    return records

def wandb_format_exp(exp):
    exp = dcopy(exp)
    # if "label0" in exp:
    #     exp.tr_epochs,exp.tr_sigma = exp["label0"].split(",")
    #     if "(" in exp.tr_epochs: exp.tr_epochs = int(exp.tr_epochs[1:])
    #     if ")" in exp.tr_sigma: exp.tr_sigma = int(exp.tr_sigma[:-1])
    for key,val in exp.items():
        if isinstance(val,Path):
            exp[key] = str(val)
    return exp

def wandb_format(results):
    fmt = {}
    def islist(value):
        return isinstance(value,list) or isinstance(value,np.ndarray)
    def isstr(value):
        return isinstance(value,str) or isinstance(value,np.str)
    def isfloat(value):
        return isinstance(value,float) or isinstance(value,np.float)
    def recurse_fmt(key,val):
        if not(islist(val)):
            fmt[key] = val
        elif len(val) == 0:
            fmt[key] = "None"
        elif not(islist(val[0])):
            if isstr(val[0]):
                fmt[key] = val
            elif isinstance(val[0],Path):
                fmt[key] = str(val[0])
            elif isfloat(val[0]):
                fmt[key] = np.mean(val)
            else:
                fmt[key] = val[0]
        else:
            recurse_fmt(key,val[0])
    for key,val in results.items():
        if key == "vid_name":
            fmt[key] = val[0][0]
        elif isinstance(val,Path):
            fmt[key] = str(val)
        else:
            recurse_fmt(key,val)
    # print(results)
    # print(fmt)
    return fmt

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

def get_uuids(exps,cache_or_name,version="v1",
              no_config_check=False,read=True,force_read=False,reset=False):

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
    if (len(exps) == len(cache.uuid_cache.data['config']) and read) or force_read:
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

