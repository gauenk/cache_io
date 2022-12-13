
import pprint
from pathlib import Path
from ._debug import VERBOSE

def compare_config(existing_config,proposed_config):
    if isinstance(existing_config,str): return False
    for key,value in existing_config.items():
        if not(key in proposed_config):
            # print("missing key: ",key)
            return False
        if proposed_config[key] != value:
            # print("neq key: ",key,proposed_config[key],value)
            return False
    return True

def print_config(config,indent=1):
    pp = pprint.PrettyPrinter(depth=5,indent=indent)
    pp.pprint(config)



