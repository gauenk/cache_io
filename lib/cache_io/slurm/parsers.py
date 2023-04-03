
"""

Two levels of parsing for merging

"""

import argparse
from pathlib import Path
from easydict import EasyDict as edict

def process_parser():
    desc = 'This will equip the script to accept input args to launch slum programs'
    parser = argparse.ArgumentParser(
        prog = 'Parser which equips a script to be run by with the Python Slurm laucher',
        description = desc,
        epilog = 'Happy Hacking')
    parser.add_argument('--start',type=int,default=0,
                        help="Starting Experiment Index")
    parser.add_argument('--end',type=int,default=-1,
                        help="Ending Experiment Index (exclusive)")
    parser.add_argument('--clear',action="store_true")
    parser.add_argument('--name',type=str,default=None)
    args = parser.parse_known_args()[0]
    args = edict(vars(args))
    return args

def launcher_parser():
    desc = "Launches python scripts equipped with 'slurm_parser' to accept arguments"
    parser = argparse.ArgumentParser(
        prog = 'Launching Dispatched Experiments with Slurm',
        description = desc,
        epilog = 'Happy Hacking')
    parser.add_argument('script',type=str,
                        help="The path of a Python script equipped with dispatch mode.")
    parser.add_argument('total_exps',type=int,default=-1,nargs="?",
                        help="The total number of experiments")
    parser.add_argument('chunk_size',type=int,default=-1,nargs="?",
                        help="Number of Experiments per Process")
    parser.add_argument('--exp_start',default=0,type=int,
                        help="Experiment Index to Start On.")
    parser.add_argument('-U','--unique_names',action="store_true",
                        help="Each dispatched file is assigned a unique cache name. This removes the read/write race condition among the concurrent processes for a single cache, but requires merging caches after the experiments.")
    parser.add_argument('-J','--job_name_base',default=None)
    parser.add_argument('-C','--clear_first',action="store_true",
                        help="Clears the cache only for the first experiment.")
    parser.add_argument('-A','--account',default="standby")
    parser.add_argument('-M','--machines',nargs='+',
                        default=["e","f","b","g"]) # d, i
    parser.add_argument('-WM','--with_machines',action="store_true",
                        help="Run exp with specified machines.")
    parser.add_argument('-N','--nodes',default=1)
    parser.add_argument('-T','--time',default="0-4:00:00")
    # parser.add_argument('-E','--exclusive',action="store_true",
    #                     help="Run experiment with slurm exclusive flag.")
    parser.add_argument('--gpus_per_node',default=1)
    parser.add_argument('--cpus_per_task',default=4)
    parser.add_argument('--reset',action="store_true",
                        help="Clear out the dispatch launch and output paths.")

    # -- merging --
    parser.add_argument('--merge_skip_empty',action="store_false",
                        help="Input when merging caches.")
    parser.add_argument('--merge_overwrite',action="store_true",
                        help="Input when merging caches.")

    # -- parse --
    args = parser.parse_known_args()[0]

    # ---------------------------
    # --  commandline deaults  --
    # ---------------------------

    args = edict(vars(args))

    # -- fill default job name --
    if args.job_name_base is None:
        args.job_name_base = Path(args.script).stem

    # -- if chunks aren't specified, run all exps in one proces --
    print(args)
    args.exec_all = args.chunk_size == -1
    if args.total_exps == -1:
        args.total_exps = 1
        msg = "If total exps aren't specified, don't use chunk_size"
        assert args.chunk_size == -1,msg
    if args.exec_all:
        args.chunk_size = 1

    return args


def script_parser():

    # -- merging --
    desc = 'This parser _always_ runs when enable_dispatch="slum". '
    desc += 'Determines the scripts function: [mering, processing, or launching]'
    prog = 'Parser which equips a script to be run by with the Python Slurm laucher'
    parser = argparse.ArgumentParser(
        prog = prog,
        description = desc,
        epilog = 'Happy Hacking')

    # -- merging --
    parser.add_argument('--merge_cache',action="store_true",
                        help="Allowing merging of uniquely named cache_io Exp Caches.")
    parser.add_argument('--merge_skip_empty',action="store_false",
                        help="Input when merging caches.")
    parser.add_argument('--merge_skip_results',action="store_true",
                        help="Ignore results when merging cache [already copied].")
    parser.add_argument('--merge_overwrite',action="store_true",
                        help="Write over the uuid,results of the source cache")
    # parser.add_argument('--launched_with_slurm',action="store_true")
    parser.add_argument('--dispatch',action="store_true")
    parser.add_argument('--skip_loop',action="store_true")
    parser.add_argument('-J','--job_id',type=str,default=None)
    parser.add_argument('--nexps',type=int,default=None)
    parser.add_argument('--nexps_pp',type=int,default=None)
    parser.add_argument('--very_fast',action="store_true")
    parser.add_argument('--fast',action="store_true")
    parser.add_argument('--links_only',action="store_true")

    # -- parse --
    args = parser.parse_known_args()[0]
    args = edict(vars(args))
    return args

