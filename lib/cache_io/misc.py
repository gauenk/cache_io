
from pathlib import Path


def exp_strings2bools(exp):
    for field in exp:
        if not isinstance(exp[field],str): continue
        if exp[field].lower() == "true":
            exp[field] = True
        elif exp[field].lower() == "false":
            exp[field] = False
        elif exp[field].lower() == "none":
            exp[field] = None

def strings2bools(exps):
    # convert "true" or "false" to True or False
    for exp in exps:
        exp_strings2bools(exps)

def optional(pydict,field,default):
    if pydict is None: return default
    if not(field in pydict): return default
    else: return pydict[field]
