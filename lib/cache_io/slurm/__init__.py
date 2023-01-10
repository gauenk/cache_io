"""

Code to wrap launching a slurm process.


def slurm_main():
    records = cache_io.run_exps(cfg_file,train_model.run,
                                einds=einds,clear=args.clear)

"""

from .api import run_launcher,run_process
from .parser import process_parser
