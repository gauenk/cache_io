
import pprint
from pathlib import Path
from ._debug import VERBOSE

def compare_config(existing_config,proposed_config):
    if isinstance(existing_config,str): return False
    left_cmp = compare_pair(existing_config,proposed_config,["uuid"])
    right_cmp = compare_pair(proposed_config,existing_config,["uuid"])
    pair_cmp = left_cmp and right_cmp
    return pair_cmp

def compare_pair(cfg_a,cfg_b,skips):
    for key,value in cfg_a.items():
        if key in skips: continue
        if not(key in cfg_b):
            # print("missing key: ",key)
            return False
        if cfg_b[key] != value:
            # print("neq key: ",key,proposed_config[key],value)
            return False
    return True

def print_config(config,indent=1):
    pp = pprint.PrettyPrinter(depth=5,indent=indent)
    pp.pprint(config)



