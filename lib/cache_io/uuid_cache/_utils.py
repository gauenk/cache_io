
import pprint
from pathlib import Path
from ._debug import VERBOSE

def compare_config(existing_config,proposed_config,verbose=False):
    if isinstance(existing_config,str): return False
    dev_check = False
    if dev_check and _dev_cmp(existing_config):
        print("-"*10)
        print(proposed_config)
        print(existing_config)
        verbose = True
    left_cmp = compare_pair(existing_config,proposed_config,["uuid"],verbose)
    right_cmp = compare_pair(proposed_config,existing_config,["uuid"],verbose)
    pair_cmp = left_cmp and right_cmp
    if dev_check and _dev_cmp(existing_config):
        print(left_cmp,right_cmp,pair_cmp)
    return pair_cmp

# -> FREELY DELETE ME. <-
def _dev_cmp(cfg):
    match = True
    fields = {"arch_name":"n3net","vid_name":"sunflower","ws":15,"wt":0}
    for field in fields:
        if not(cfg[field] == fields[field]):
            match = False
            break
    return match

def compare_pair(cfg_a,cfg_b,skips,verbose=False):
    for key,value in cfg_a.items():
        if key in skips: continue
        if not(key in cfg_b):
            if verbose: print("missing key: ",key)
            return False
        if cfg_b[key] != value:
            if verbose: print("neq key: ",key,value,cfg_b[key])
            return False
    return True

def t(val):
    val = convert_bool_str(val)
    return val

def convert_bool_str(val):
    if val == "true":
        return True
    elif val == "false":
        return False
    else:
        return val

def print_config(config,indent=1):
    pp = pprint.PrettyPrinter(depth=5,indent=indent)
    pp.pprint(config)



