"""

Functons for API

"""

# -- printing --
import pprint
pp = pprint.PrettyPrinter(indent=4)

# -- cache api --
from .exps import read,load
from .misc import optional
from .exp_cache import ExpCache

# -- dispatch options --
from . import slurm 

# -- mangling --
from pathlib import Path
from easydict import EasyDict as edict


def run_exps(exp_file_or_list,exp_fxn,name=None,version=None,clear_fxn=None,
             records_fn=None,records_reload=True,skip_loop=False,verbose=True,
             einds=None,clear=False,enable_dispatch=None):

    # -- optionally restrict inds using an input parser --
    if not(enable_dispatch is None):
        assert (einds is None),"Indices are selected from dispatch"
        einds,clear = dispatch(enable_dispatch,einds,clear)

    # -- open cache --
    cache = open_cache(exp_file_or_list,name=name,version=version)
    if clear: cache.clear()

    # -- load list of exps --
    exps = get_exps(exp_file_or_list)
    if not(einds is None): exps = [exps[i] for i in einds]
    print(len(exps),type(exps[0]))

    # -- run exps --
    nexps = len(exps)
    for exp_num,exp in enumerate(exps):

        # -- optionally skip --
        if skip_loop: break

        # -- info --
        if verbose:
            print("-="*25+"-")
            print(f"Running experiment number {exp_num+1}/{nexps}")
            print("-="*25+"-")
            pp.pprint(exp)

        # -- logic --
        uuid = cache.get_uuid(exp) # assing ID to each Dict in Meshgrid

        # -- optionally clear --
        if not(clear_fxn is None) and clear_fxn(exp_num,exp):
            cache.clear_exp(uuid)

        # -- load result --
        results = cache.load_exp(exp) # possibly load result

        # -- run exp --
        if results is None: # check if no result
            exp.uuid = uuid
            results = exp_fxn(exp)
            cache.save_exp(uuid,exp,results) # save to cache

    # -- records --
    records = cache.to_records(exps,records_fn,records_reload)
    return records

def open_cache(exp_file,name=None,version=None):
    """

    Open ExpCache using the following inputs:
    (1) the kwarg (name,version)
    (2) the exp_file
    """
    if (name is None) or (version is None):
        edata = read(exp_file)
        name = edata['name']
        version = edata['version']
    cache = ExpCache(name,version)
    return cache

def get_exps(exp_file_or_list):
    islist = isinstance(exp_file_or_list,list)
    ispath = isinstance(exp_file_or_list,edict)
    if isinstance(exp_file_or_list,list):
        isdict = isinstance(exp_file_or_list[0],edict)
        isdict = isdict or isinstance(exp_file_or_list[0],dict)
        if isdict:
            exps = exp_file_or_list
        else: # list of config files
            exps = []
            for fn in exp_file_or_list:
                exps.extend(load(fn))
    else: # single list of config files
        exps = load(exp_file_or_list)
    return exps

def dispatch(enable_dispatch,*args):
    if enable_dispatch == "slurm":
        einds,clear = slurm.run_process(*args)
    elif enable_dispatch == "spli":
        einds,clear = split.run_process(*args)
    else:
        raise ValueError("Uknown dispatch type [%s]" % enable_dispatch)
    return einds,clear
