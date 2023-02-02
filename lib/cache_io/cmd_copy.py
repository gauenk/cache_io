"""

Commandline script to copy from one to another

"""

import sys,glob,os
from easydict import EasyDict as edict
from pathlib import Path
import argparse
import cache_io

def parser():
    # Example: cache_copy ./.cache_io_remote/my_exp v1 ./.cache_io/my_exp v1
    desc = "Allows copying from one cache to another."
    prog = "cache_cp"
    parser = argparse.ArgumentParser(
        prog = prog, description = desc, epilog = 'Happy Hacking')
    parser.add_argument("src_path")
    parser.add_argument("src_version")
    parser.add_argument("dest_path")
    parser.add_argument("dest_version")
    parser.add_argument('--exp_file',default=None,type=str,
                        help="choose exeriment file to copy")
    parser.add_argument('--overwrite',action="store_true",
                        help="overwrite dest if exists.")
    args = parser.parse_args()
    args = edict(vars(args))
    return args

def main():
    # -- parse --
    args = parser()
    cache_src = cache_io.ExpCache(args.src_path,args.src_version)
    cache_dest = cache_io.ExpCache(args.dest_path,args.dest_version)
    cache_io.copy.enames(args.src_path,args.src_version,
                         args.dest_path,args.dest_version,
                         exps=args.exp_file,overwrite=args.overwrite)
