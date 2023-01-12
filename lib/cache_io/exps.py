"""

Manage experiment files

"""

import yaml
from easydict import EasyDict as edict
from .mesh import mesh_groups,add_cfg

def load(fn): # read + unpack
    edata = read(fn)
    return unpack(edata)

def read(fn):
    with open(fn,"r") as stream:
        data = yaml.safe_load(stream)
    return data

def unpack(edata):
    cfg = edict(edata['cfg'])
    groups = [v for g,v in edata.items() if "group" in g]
    grids = [v for g,v in edata.items() if "global_grids" in g]
    if len(grids) == 0: grids = [{}]
    exps = []
    for grid in grids:
        exps += mesh_groups(grid,groups)
    if len(exps) == 0: exps = [cfg]
    else: add_cfg(exps,cfg)
    return exps

def get_exp_list(exp_file_or_list):
    return get_exps(exp_file_or_list)

def get_exps(exp_file_or_list):
    islist = isinstance(exp_file_or_list,list)
    ispath = isinstance(exp_file_or_list,edict)
    if islist:
        isdict = isinstance(exp_file_or_list[0],edict)
        isdict = isdict or isinstance(exp_file_or_list[0],dict)
        print(type(exp_file_or_list[0]))
        if isdict:
            exps = exp_file_or_list
        else: # list of config files
            exps = []
            for fn in exp_file_or_list:
                exps.extend(load(fn))
    else: # single list of config files
        exps = load(exp_file_or_list)
    return exps
