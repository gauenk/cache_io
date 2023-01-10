
"""

The core logic of launching wrapped slurm processes

"""

import os,tqdm
from pathlib import Path
from ..exp_cache import ExpCache
from ..copy import exp_cache as exp_cache_copy

from .parsers import launcher_parser,process_parser
from .helpers import create_paths
from .helpers import get_process_args,get_fixed_args
from .helpers import create_launch_files,run_launch_files
from .helpers import save_launch_info

def run_launcher(base):
    """
    Parses arguments for the "sbatch_py" script when running it as a wrapper:

    ```
    sbatch_py <script_name.py> <num_of_experiments> <experiments_per_proc>
    ```    
    """

    # -- create user args --
    args = launcher_parser()
    print("[Launcher] Running: ",args)

    # -- args --
    base /= args.job_name_base
    output_dir,launch_dir,info_dir = create_paths(base,args.reset)

    # -- create slurm launch files --
    proc_args = get_process_args(args)
    fixed_args = get_fixed_args(args)
    files,out_fns,uuid_s = create_launch_files(proc_args,fixed_args,launch_dir,output_dir)

    # -- launch files --
    slurm_ids = run_launch_files(files,out_fns)

    # -- save launch info --
    save_launch_info(info_dir,uuid_s,args.job_name_base,slurm_ids,out_fns,proc_args)

def dispatch_process(merge_flag,einds,clear,name,version,exps):
    if merge_flag:
        merge(name,version,exps)
        return einds,clear,name
    else:
        return run_process(einds,clear,name,version,exps)

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
    if args.launched_with_slurm is False:
        return einds,clear,name
    einds = [i for i in range(args.start,args.end)]
    clear = args.clear
    if not(args.name is None):
        name = args.name
    return einds,clear,name

def merge(name,version,exps,overwrite=False,skip_empty=True):
    """
    Parses arguments for the "<script_name.py>" script, _always_.
    Should be used only for a single process and running the script directly.

    The "merge" parameter indicates if launched with dispatch or not.

    _without_ merge:
    ```
    sbatch_py <script_name.py> <num_of_experiments> <experiments_per_proc>
    ```    

    _with_ merge
    ```
    <script_name.py> <num_of_experiments> <experiments_per_proc>
    ```    

    -=-=-=-=-=-=- Standard Example -=-=-=-=-=-=-=-=-

    A. Run the script with unique names

    ```
    sbatch_py <script_name.py> <num_of_experiments> <experiments_per_proc> -UN
    ```    

    B. Merge the outputs to the original cache. Note, enable_dispatch must not change!

    (i) Edit the file so `merge_dispatch = True`

    (ii) Launch the script with `python` using the `sbatch_py` arguments
    ```
    python <script_name.py> <script_name.py> <num_of_experiments> <experiments_per_proc>
    ```

    (iii) Edit the file so `merge_dispatch = False`.


    C. Rerun as normal. Any `enable_dispatch` is allowed.

    ```
    python <script_name.py>
    ```

    """


    # -- get original names --
    print("Mering.")
    args = launcher_parser()
    base = Path(os.getcwd()).resolve() / "dispatch"
    print("[Merge] Running: ",args)

    # -- not split, so no merge --
    if not(args.unique_names):
        return None

    # -- get cache names --
    base /= args.job_name_base
    output_dir,launch_dir,info_dir = create_paths(base,False)
    proc_args = get_process_args(args)
    names = [p.name for p in proc_args]
    
    # -- copy each name --
    cache = ExpCache(name,version)
    print("Destination Cache: [%s]" % name)
    for name_p in tqdm.tqdm(names):
        print("Copying [%s]" % (name_p))
        cache_p = ExpCache(name_p,version)
        exp_cache_copy(cache_p,cache,exps,overwrite=overwrite,skip_empty=skip_empty)
    
