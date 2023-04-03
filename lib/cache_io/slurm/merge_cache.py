"""

Merging for cache_io via commandline

this is possibly the wrong package for this function

"""


import os
from pathlib import Path

# -- api --
from . import api

# -- parsing --
import argparse
from easydict import EasyDict as edict

def parser():
    
    # -- merging --
    desc = 'This parser _always_ runs when enable_dispatch="slum". '
    desc += 'Determines the scripts function: [mering, processing, or launching]'
    prog = 'Parser which equips a script to be run by with the Python Slurm laucher'
    parser = argparse.ArgumentParser(
        prog = prog,
        description = desc,
        epilog = 'Happy Hacking')

    # -- required inputs --
    parser.add_argument('cache_name',type=str,default=None,
                        help="Directory of cache for merging.")
    parser.add_argument('nexps',type=int,default=-1,nargs="?",
                        help="The total number of experiments")
    parser.add_argument('nexps_pp',type=int,default=-1,nargs="?",
                        help="Number of Experiments per Process")
    parser.add_argument('job_id',type=str,default=None)

    # -- merging options --
    parser.add_argument('--merge_cache',action="store_true",
                        help="Allowing merging of uniquely named cache_io Exp Caches.")
    parser.add_argument('--merge_skip_empty',action="store_false",
                        help="Input when merging caches.")
    parser.add_argument('--merge_skip_results',action="store_true",
                        help="Ignore results when merging cache [already copied].")
    parser.add_argument('--merge_overwrite',action="store_true",
                        help="Write over the uuid,results of the source cache")
    parser.add_argument('--cache_version',type=str,default="v1",
                        help="Version of cache for merging.")

    # -- merging speed --
    parser.add_argument('--very_fast',action="store_true")
    parser.add_argument('--links_only',action="store_true")

    # -- parse --
    args = parser.parse_known_args()[0]
    args = edict(vars(args))
    return args

def main():

    # -- parse --
    args = parser()
    cache_name = args.cache_name
    cache_version = args.cache_version
    args.fast = True # must be to skip "exps"
    api.merge(args,cache_name,cache_version,None)

if __name__ == "__main__":
    main()
