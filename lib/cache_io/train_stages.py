"""

Create a list of experiment configs from a filename with
parameters for training with stages


- The output from this list depends on the _checkpoint files_!!!
- We only load incomplete stages with complete previous stages!

Example:

  stage_0: [epochs 0-39]
  stage_1:
    - [epochs 40 - 49] using parameters 0
    - [epochs 40 - 49] using parameters 1
  stage_2:
    - [epochs 50 - 89] using parameters 2 from stage_1 parameters 0
  stage_3:
    - [epochs 90 - 99] using parameters 3 from stage_2 parameters 2
    - [epochs 90 - 99] using parameters 3 from stage_2 parameters 2

"""

import shutil
import copy
dcopy = copy.deepcopy
import pprint
pp = pprint.PrettyPrinter(depth=5,indent=8)
import yaml
from pathlib import Path
import uuid as uuid_gen
from easydict import EasyDict as edict
from .exp_cache import ExpCache
from .exps import get_exps
from .exps import load_edata

def run(fn,cache_name,cache_version="v1",
        load_complete=True,stage_select=0,
        reset=False,fast=True,update=False):

    # -- open files --
    stages = read(fn)
    chkpt_root = stages.chkpt_root
    cache = ExpCache(cache_name,cache_version)
    if reset: cache.clear()

    # -- todo: check length matches loaded exps; append new exps to cache. --
    if len(cache.uuid_cache.data['config']) > 0 and not(update):
        # print("Skip reloading exps since config is not empty.")
        uuids = cache.uuid_cache.data['uuid']
        cfgs = cache.uuid_cache.data['config']
        return cfgs,uuids

    # -- core run --
    exps,uuids = run_core(stages,chkpt_root,cache,fast,update,load_complete,stage_select)

    # -- save again ["get_uuid" doesn't write to cache.] --
    if fast:
        cache.uuid_cache.write_pair(uuids,exps)

    return exps,uuids

def run_core(stages,chkpt_root,cache=None,fast=True,
             update=False,load_complete=True,stage_select=-1,use_learn=True):

    # -- build bases --
    base = load_train_base(stages,use_learn=use_learn)
    bases = []
    for key in stages:
        if "mesh" in key:
            stages[key]['cfg'] = dcopy(base)
            bases += load_edata(stages[key])

    # -- run for each base config --
    nocheck = fast and not(update)
    exps,uuids = [],[]
    for base in bases:
        exps_b,uuids_b = run_base(base,stages,cache,chkpt_root,
                                  load_complete,stage_select,nocheck)
        exps += exps_b
        uuids += uuids_b

    return exps,uuids

def run_base(base,stages,cache,chkpt_root,
             load_complete=False,stage_select=-1,nocheck=True):

    # -- num stages --
    nstages = get_num(stages,"stage_%d")
    nstages = max(nstages,1)

    # -- accumulate experiments --
    train_exps = [] # exps
    train_uuids = [] # uuids
    for stage_i in range(nstages):

        # -- select only certain stages --
        if (stage_select >= 0) and not(stage_i == stage_select): continue

        # -- load stage --
        stage_k = "stage_%d" % stage_i
        stage = stages[stage_k] if stage_k in stages else {}
        if stage_i > 0:
            stage_prev = stages[stage.train_prev]

        # -- check each exp --
        nexps = get_num(stage,"exp_%d")
        nexps = max(nexps,1)
        for exp_i in range(nexps):
            # print(stage_i,exp_i)

            # -- get exp --
            exp_k = "exp_%d" % exp_i
            exp = stage[exp_k] if exp_k in stage else {}

            # -- create full config --
            cfg = create_config(base,exp)
            uuid = get_uuid(cfg,cache,nocheck=nocheck)

            # -- check if experiment stage complete [checkpoint dir] --
            complete = check_stage_complete(chkpt_root,uuid,cfg.nepochs)
            if not(load_complete) and complete: continue # only load incomplete stages

            # -- mange previous stage --
            if stage_i > 0:

                # -- load info --
                cfg_prev = get_previous_config(base,stage_prev,exp.prev)
                uuid_prev = get_uuid(cfg_prev,cache,nocheck=False)

                # -- [optional] check complete --
                # complete = check_stage_complete(chkpt_root,uuid_prev,cfg_prev.nepochs)
                # if not(complete): continue # don't add if incomplete previous stage

                # -- copy if previous is complete --
                rtn = copy_checkpoint(chkpt_root,uuid,uuid_prev,cfg_prev.nepochs)
                if rtn is False:
                    msg = "Warning: Failed to copy [stage,exp]: [%d,%d]"
                    print(msg % (stage_i,exp_i))

            # -- add exp to result --
            train_exps.append(cfg)
            train_uuids.append(uuid)

    # -- return values --
    return train_exps,train_uuids

def check_stage_complete(root,uuid,nepochs):
    chkpt_fn = get_checkpoint(Path(root)/uuid,uuid,nepochs-1)
    return chkpt_fn.exists()

def get_uuid(cfg,cache,nocheck=True):
    if nocheck or (cache is None):
        uuid = str(uuid_gen.uuid4())
    else:
        uuid = cache.get_uuid(cfg)
    return uuid

def create_config(base,exp):
    cfg = dcopy(base)
    for key in exp:
        if key == "prev": continue
        cfg[key] = exp[key]
    return cfg

def copy_checkpoint(root,uuid,uuid_prev,nepochs_prev):

    # -- shared base --
    root = Path(root)
    # print(root,uuid,uuid_prev)

    # -- src --
    chkpt_dir_src = root / uuid_prev
    chkpt_src = get_checkpoint(chkpt_dir_src,uuid_prev,nepochs_prev-1)
    good_chkpt = chkpt_src.exists() and chkpt_src.is_file()
    if not(good_chkpt):
        return False

    # -- dest --
    chkpt_dir_dest = root / uuid
    dest_name = chkpt_src.name.replace(uuid_prev,uuid)
    chkpt_dest = chkpt_dir_dest / dest_name
    # print(chkpt_src,chkpt_dest)
    # exit(0)

    # -- copy --
    if not chkpt_dir_dest.exists():
        chkpt_dir_dest.mkdir(parents=True)
    shutil.copy(chkpt_src,chkpt_dest)
    return True

def get_previous_config(base,stage,pairs):
    nexps = get_num(stage,"exp_%d")
    for exp_i in range(nexps):
        # -- get exp --
        exp_k = "exp_%d" % exp_i
        exp = stage[exp_k]

        # -- get config --
        cfg = create_config(base,exp)

        # -- check --
        if check_keys(cfg,pairs):
            return cfg
    raise ValueError("Unable to convert exps from stages.")

def check_keys(exp,pairs):
    equal = True
    for key,val in pairs.items():
        equal = equal and (val == exp[key])
    return equal

def get_checkpoint(checkpoint_dir,uuid,nepochs):
    chkpt_fn = Path(checkpoint_dir) / ("%s-epoch=%02d.ckpt" % (uuid,nepochs))
    return chkpt_fn

def load_train_base(stages,use_learn=True):

    # -- load train/test base --
    base = get_exps(stages.base)
    assert len(base) == 1,"The base must be one experiment."
    base = base[0] # one elem

    # -- don't append learning --
    if use_learn is False: return base

    # -- load learning/training info --
    learning = get_exps(stages.learning)
    assert len(learning) == 1,"The learning must be one experiment."
    learning = learning[0] # one elem

    # -- append --
    for key in learning:
        base[key] = learning[key]
    
    return base

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
#
#              MISC
#
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

def get_num(cfg,fmt):
    num = -1
    exists = True
    while exists:
        num += 1
        stage_key = fmt % num
        exists = stage_key in cfg
    assert num >= 0
    return num

def read(fn):
    with open(fn,"r") as stream:
        data = yaml.safe_load(stream)
    return edict(data)


