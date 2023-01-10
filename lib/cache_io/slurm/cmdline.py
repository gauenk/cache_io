
"""

A commandline utility for launching slurm files

sbatch_py ./script/my_python_script <num_experiments> <experiments_per_process>

"""

import os
from pathlib import Path
from .api import run_launcher

def main():
    base = Path(os.getcwd()).resolve() / "dispatch"
    run_launcher(base)

if __name__ == "__main__":
    main()
