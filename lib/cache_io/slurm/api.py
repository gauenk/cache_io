
"""

The core logic of launching wrapped slurm processes

"""


from .parsers import launcher_parser,process_parser
from .helpers import create_paths
from .helpers import get_process_args,get_fixed_args
from .helpers import create_launch_files,run_launch_files
from .helpers import save_launch_info

def run_launcher(base):

    # -- create user args --
    args = launcher_parser()
    print("[Launcher] Running: ",args)

    # -- args --
    base /= args.job_name_base
    output_dir,launch_dir,info_dir = create_paths(base,args.reset)

    # -- create slurm launch files --
    proc_args = get_process_args(args)
    fixed_args = get_fixed_args(args)
    files,out_fns = create_launch_files(proc_args,fixed_args,launch_dir,output_dir)

    # -- launch files --
    slurm_ids = run_launch_files(files,out_fns)

    # -- save launch info --
    save_launch_info(info_dir,args.job_name_base,slurm_ids,out_fns)

def run_process(einds,clear):
    args = process_parser()
    print("[Process] Running: ",args)
    if args.launched_with_slurm is False:
        return einds,clear
    einds = [i for i in range(args.start,args.end)]
    clear = args.clear
    return einds,clear

