
"""

The core logic of launching wrapped slurm processes

"""

import os,tqdm
from pathlib import Path
from ..exp_cache import ExpCache
from ..copy import exp_cache as exp_cache_copy
from ..copy import exp_cache_fast as exp_cache_copy_fast
from ..copy import exp_cache_very_fast as exp_cache_copy_very_fast

from .parsers import launcher_parser,process_parser,script_parser
from .helpers import create_paths
from .helpers import get_process_args,get_fixed_args
from .helpers import create_launch_files,run_launch_files
from .helpers import save_launch_info,save_json
from .helpers import get_job_names


def dispatch_process(merge_flag,einds,clear,name,version,skip_loop,exps):
    # if we merge, we don't run the process
    script_args = script_parser()
    skip_loop = script_args.skip_loop or skip_loop

    if merge_flag or script_args.merge_cache:
        merge(script_args,name,version,exps)
    elif script_args.dispatch is True:
        einds,clear,name = run_process(einds,clear,name,version,exps)
    return einds,clear,name,skip_loop

def run_launcher(base):
    """
    Parses arguments for the "sbatch_py" script when running it as a wrapper:

    ```
    sbatch_py <script_name.py> <num_of_experiments> <experiments_per_proc>
    ```

    This function is called by the "sbatch_py" script [aka cmdline.py].

    Functionally, it creates a list of shell files formatted per the parse arguemnts.
    Then it executes each of them with the sbatch create.

    """

    # -- command user args --
    args = launcher_parser()
    print("[Launcher] Running: ",args)

    # -- args --
    base /= args.job_name_base
    output_dir,launch_dir,info_dir = create_paths(base,args.reset)

    # -- create slurm launch files --
    unique = args.unique_names
    proc_args = get_process_args(args)
    fixed_args = get_fixed_args(args)
    files,out_fns,uuid_s = create_launch_files(proc_args,fixed_args,
                                               launch_dir,output_dir)
    print("UUID: ",uuid_s)

    # -- launch files --
    slurm_ids = run_launch_files(files,out_fns,unique)

    # -- save launch info --
    save_launch_info(info_dir,uuid_s,args.job_name_base,slurm_ids,out_fns,proc_args)
    save_json(info_dir/("%s_args.json"%uuid_s),args)

    # -- [recommended named launch command] --
    print("Recommended command.")
    jname = args.job_name_base
    args = (jname,uuid_s,args.total_exps,args.chunk_size,jname)
    fmt = "nohup named_launch %s %s %d %d username > named_launch_%s.txt &"
    print(fmt % args)

def run_process(einds,clear,name,version,exps):
    """
    Parses arguments for the "<script_name.py>" script, _always_:

    The "launch_with_slurm" parameter indicates if launched with dispatch or not.
    This is set in the bash scripts used to run the python file above.

    with dispatch:
    ```
    sbatch_py <script_name.py> <num_of_experiments> <experiments_per_proc>
    ```

    without dispatch:
    ```
    <script_name.py> <num_of_experiments> <experiments_per_proc>
    ```
    """
    args = process_parser()
    print("[Process] Running: ",args)
    end = len(exps) if args.end == -1 else args.end
    einds = [i for i in range(args.start,end)]
    clear = args.clear
    if not(args.name is None):
        name = ".cache_io/%s" % (args.name)
    return einds,clear,name

def merge(args,name,version,exps):
    """

    Merges the ExpCaches created when dispatches the launched parameters.

    -=-=-=-=-=-=- Standard Example -=-=-=-=-=-=-=-=-

    A. Run the script with unique names

    ```
    sbatch_py <script_name.py> <num_of_experiments> <experiments_per_proc> -U
    ```

    B. Merge the outputs to the original cache.

    Launch the script with `python` using the `sbatch_py` arguments

    ```
    python <script_name.py> --job_id <job_id> --nexps <num_of_experiments> \
           --nexps_pp <experiments_per_proc> --merge_cache --skip_loop
    ```

    C. Rerun as normal. Any `enable_dispatch` is allowed.

    ```
    python <script_name.py>
    ```

    """

    # -- unpack merge args --
    print("Merging.")
    overwrite = args.merge_overwrite
    skip_empty = args.merge_skip_empty
    base = Path(os.getcwd()).resolve() / "dispatch"

    # -- get cache names --
    base /= args.job_id
    output_dir,launch_dir,info_dir = create_paths(base,False)
    job_names = get_job_names(args)
    cache_names = [".cache_io/%s" % name for name in job_names]

    # -- copy each name --
    cache = ExpCache(name,version)
    print("Destination Cache: [%s]" % name)

    # -- copy all at once --
    if args.very_fast:
        exp_cache_copy_very_fast(cache_names,cache,version,
                                 args.merge_skip_results,
                                 reset=args.reset,links_only=args.links_only)
        return

    # -- copy in a loop --
    for cache_name_p in tqdm.tqdm(cache_names):
        print("Copying [%s]" % (cache_name_p))
        cache_p = ExpCache(cache_name_p,version)
        if args.fast:
            exp_cache_copy_fast(cache_p,cache,args.merge_skip_results)
        else:
            exp_cache_copy(cache_p,cache,exps,overwrite=overwrite,skip_empty=skip_empty)
