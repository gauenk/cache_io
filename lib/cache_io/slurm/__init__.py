"""

Code to wrap launching a slurm process.

filename: scripts/my_script.py

    # -- imports etc --
    ...
    
    def main():
    
        # -- other code --
        ...
    
        # -- enable slurm dispatching --
        records = cache_io.run_exps(cfg_file,test_model.run,
                                    name=name,version=version,
                                    records_fn=records_fn,
                                    records_reload=records_reload,
                                    enable_dispatch="slurm")
    
        # -- finish script --
        ....
    
Slurm-enabled commandline launch:

```
sbatch_py ./scripts/my_script.py <num_of_experiments> <experiments_per_proc>

```

Standard commandline (without slurm) launch:


```
./scripts/my_script.py

```

A user does not need to change their code at all!

"""

from .api import run_launcher,dispatch_process
from .parsers import process_parser
