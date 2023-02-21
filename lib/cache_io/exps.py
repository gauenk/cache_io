"""

Manage experiment files

"""

import copy
dcopy = copy.deepcopy
import yaml
from easydict import EasyDict as edict
from .mesh import mesh_groups,add_cfg
from .mesh import read_rm_picked,append_picked

def load(fn):
    edata = read(fn)
    return load_edata(edata)

def load_edata(edata):
    picks = read_rm_picked(edata)
    exps = unpack(edata)
    if len(picks) > 0:
        if len(picks) > 1:
            print("Warning. Not able to properly handle more than one pick list.")
        exps = append_picked(exps,picks)
    return exps

# def load(fn): # read + unpack
#     edata = read(fn)
#     return unpack(edata)

def read(fn):
    with open(fn,"r") as stream:
        data = yaml.safe_load(stream)
    return data

def unpack(edata):

    cfg = edict(edata['cfg']) if 'cfg' in edata else edict()
    mutexs = [v for g,v in edata.items() if "mutex" in g]
    groups = [v for g,v in edata.items() if "group" in g]
    listed = [v for g,v in edata.items() if "listed" in g]
    grids = [v for g,v in edata.items() if "global" in g]
    if len(grids) == 0: grids = [{}]

    # -- mesh groups for each grid --
    exps = []
    for grid in grids:
        exps += mesh_groups(grid,groups)

    # -- add set of listed configs --
    exps = append_listed(exps,listed)


    # -- mutex == non-meshed (or mutually-exclusive) groups --
    exps = append_mutex(exps,mutexs)


    # -- use cfg to overwrite each exp from accumulation --
    if len(exps) == 0: exps = [cfg]
    else: add_cfg(exps,cfg)
    return exps

def append_listed(exps,listed):
    if len(listed) == 0: return exps
    exps_base = dcopy(exps)
    exps = []
    for list_i in listed:
        L = len(list_i[list(list_i.keys())[0]])
        for l in range(L):
            dict_i = edict({k:v[l] for k,v in list_i.items()})
            exps_li = dcopy(exps_base)
            add_cfg(exps_li,dict_i)
            exps += exps_li
    return exps


def append_mutex(exps,mutexs):
    if len(mutexs) == 0: return exps
    exps_base = dcopy(exps)
    exps = []
    for mut in mutexs:
        mut_m = mesh_groups({},[mut])
        for mut_m_i in mut_m:
            exps_m = dcopy(exps_base)
            add_cfg(exps_m,mut_m_i)
            exps += exps_m
    return exps

def get_exp_list(exp_file_or_list):
    return get_exps(exp_file_or_list)

def get_exps(exp_file_or_list):
    islist = isinstance(exp_file_or_list,list)
    ispath = isinstance(exp_file_or_list,edict)
    if islist:
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
