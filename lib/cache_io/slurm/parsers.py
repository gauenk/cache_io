
"""

Considering two levels of parser... This would make merging cleaner.

"""

import argparse
from pathlib import Path
from easydict import EasyDict as edict

def process_parser():
    desc = 'This will equip the script to accept input args to launch slum programs',
    parser = argparse.ArgumentParser(
        prog = 'Parser which equips a script to be run by with the Python Slurm laucher',
        description = desc,
        epilog = 'Happy Hacking')
    parser.add_argument('--start',type=int,default=-1,
                        help="Starting Experiment Index")
    parser.add_argument('--end',type=int,default=-1,
                        help="Ending Experiment Index")
    parser.add_argument('--clear',action="store_true")
    parser.add_argument('--launched_with_slurm',action="store_true")
    parser.add_argument('--name',type=str,default=None)
    args = parser.parse_args()
    return edict(vars(args))

def launcher_parser():
    desc = "Launches python scripts equipped with 'slurm_parser' to accept arguments",
    parser = argparse.ArgumentParser(
        prog = 'Launching Dispatched Experiments with Slurm',
        description = desc,
        epilog = 'Happy Hacking')
    
    parser.add_argument('script',type=str,
                        help="The path of a Python script equipped with dispatch mode.")
    parser.add_argument('total_exps',type=int,
                        help="The total number of experiments")
    parser.add_argument('chunk_size',type=int,default=1,
                        help="Number of Experiments per Process")
    parser.add_argument('--exp_start',default=0,
                        help="Experiment Index to Start On.")
    parser.add_argument('-UN','--unique_names',action="store_true",
                        help="Each dispatched file is assigned a unique cache name. This removes the read/write race condition among the concurrent processes for a single cache, but requires merging caches after the experiments.")
    parser.add_argument('-J','--job_name_base',default=None)
    parser.add_argument('-c','--clear_first',action="store_true",
                        help="Clears the cache only for the first experiment.")
    parser.add_argument('-A','--account',default="standby")
    parser.add_argument('-M','--machines',nargs='+',
                        default=["b","d","e","f","g","i"])
    parser.add_argument('-n','--nodes',default=1)
    parser.add_argument('-t','--time',default="0-4:00:00")
    parser.add_argument('--gpus_per_node',default=1)
    parser.add_argument('--cpus_per_task',default=2)
    parser.add_argument('--reset',action="store_true",
                        help="Clear out the dispatch launch and output paths.")

    # -- merging --
    parser.add_argument('--merge_skip_empty',action="store_false",
                        help="Input when merging caches.")
    parser.add_argument('--merge_overwrite',action="store_true",
                        help="Input when merging caches.")

    # -- parse --
    args = parser.parse_args()

    # -- fill default job name --
    if args.job_name_base is None:
        args.job_name_base = Path(args.script).stem

    args = edict(vars(args))
    return args


