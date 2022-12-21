
import pprint
from pathlib import Path
from ._debug import VERBOSE

def compare_config(existing_config,proposed_config,verbose=False):
    if isinstance(existing_config,str): return False
    for key,value in existing_config.items():
        if not(key in proposed_config):
            if verbose: print("missing key: ",key)
            return False
        if t(proposed_config[key]) != t(value):
            if verbose:
                print("neq key: ",key,proposed_config[key],value)
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



