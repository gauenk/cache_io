"""

Commandline script to copy from one to another

"""

import sys,glob,os
from pathlib import Path
import argparse
import cache_io

def parser():
    desc = "Copy from cache_io results with commandline." + "\n"
    desc += "Usage: cache_copy <path_to_exps_cfg> <path_to_cache_src> <cache_version_src> <path_to_cache_dest> <cache_version_dest>" + "\n"
    desc += "Example: cache_copy ./.cache_io_remote/my_exp v1 ./.cache_io/my_exp v1"
    parser = argparse.ArgumentParser(
        prog = "Allows copying from one cache to another.",
        description = desc, epilog = 'Happy Hacking')
    parser.add_argument("src_path")
    parser.add_argument("src_version")
    parser.add_argument("dest_path")
    parser.add_argument("dest_version")
    parser.add_argument('--exp_file',default=None,
                        desc="choose exeriment file to copy")
    parser.add_argument('--overwrite',action="store_true",
                        desc="overwrite dest if exists.")
    args = parser.parse_args()
    args = edict(vars(args))
    return args

def main():
    # -- parse --
    args = parser()
    cache_src = cache_io.ExpCache(args.src_path,args.src_version)
    cache_dest = cache_io.ExpCache(args.dest_path,args.dest_version)
    cache_io.enames(args.src_path,args.src_version,
                    args.dest_path,args.dest_version,
                    exps=args.exp_file,overwrite=args.overwrite)
