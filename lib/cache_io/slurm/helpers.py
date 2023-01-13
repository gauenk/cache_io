
# -- sys --
import os,uuid,subprocess,time
from easydict import EasyDict as edict
import pandas as pd

# -- json --
import json

# -- io --
from pathlib import Path

def remove_files(path):
    for fn in path.iterdir():
        os.remove(str(fn))

def create_launch_files(proc_args,fixed_args,launch_dir,output_dir):
    # -- meshgrid --
    files,out_fns = [],[]
    uuid_s = str(uuid.uuid4())
    for pargs in proc_args:
        msg,out_fn = create_launch_msg(pargs,fixed_args,uuid_s,output_dir)
        fname = write_launch_file(pargs,uuid_s,launch_dir,msg)
        files.append(fname)
        out_fns.append(out_fn)
    return files,out_fns,uuid_s

def write_launch_file(pargs,uuid_s,launch_dir,msg):
    launch_fn =  str(launch_dir / ("%s_%d_%d.sh" % (uuid_s,pargs.start,pargs.end)))
    with open(launch_fn,'w') as f:
        f.write(msg)
    return launch_fn

def create_launch_msg(pargs,fixed_args,uuid_s,output_dir):
    msg = r"#!/bin/sh -l" + "\n"*2
    for sbatch_key,sbatch_val in fixed_args.items():
        msg += "#SBATCH %s %s\n" % (sbatch_key,sbatch_val)
    msg += "#SBATCH -C %s\n" % (pargs.machine)
    msg += "#SBATCH --job-name %s\n" % (pargs.job_name)
    output_fn =  str(output_dir / ("%s_%d_%d_log.txt" % (uuid_s,pargs.start,pargs.end)))
    msg += "#SBATCH --output %s\n" % (output_fn)
    msg += "\n\n/bin/hostname\n\n"
    msg += "echo \"Saving log at %s\"\n" % (output_fn)
    msg += "/home/gauenk/.pyenv/shims/python -u %s --start %d --end %d --launched_with_slurm" % (pargs.script,pargs.start,pargs.end)
    if pargs.clear is True:
        msg += " --clear"
    if not(pargs.name is None):
        msg += " --name %s" % (pargs.name)
    msg += "\n"
    return msg,output_fn

def get_process_args(args):

    # -- chunking exps --
    pargs = []
    for start in range(args.exp_start,args.total_exps,args.chunk_size):
        end = min(start+args.chunk_size,args.total_exps)
        pargs_i = edict()
        pargs_i.start = start
        pargs_i.end = end
        pargs_i.script = args.script
        pargs_i.clear = False
        pargs_i.name = None
        pargs_i.job_name = "%s_dispatch_%d" % (args.job_name_base,start)
        if start == 0 and args.clear_first is True:
            pargs_i.clear = True
        if args.unique_names is True:
            pargs_i.name =  "%s_dispatch_%d" % (args.job_name_base,start)
        pargs.append(pargs_i)

    # -- assigning machines --
    nprocs = len(pargs)
    nmachines = len(args.machines)
    div = (nprocs-1) / nmachines + 1
    m = 0
    for p in range(nprocs):
        pargs[p].machine = args.machines[m]
        m = (m+1) % nmachines

    return pargs

def get_fixed_args(args):
    fields = {"account":"-A","nodes":"--nodes",
              "gpus_per_node":"--gpus-per-node","time":"--time",
              "cpus_per_task":"--cpus-per-task"}
    slurm_args = edict()
    for args_key,sbatch_key in fields.items():
        slurm_args[sbatch_key] = args[args_key]
    return slurm_args

def run_launch_files(files,out_files):
    slurm_ids = []
    for fn,out_file in zip(files,out_files):
        args = ["sbatch",fn]
        proc = subprocess.run(args, capture_output=True, text=True)
        slurm_info = proc.stdout
        slurm_error = proc.stderr
        if slurm_error == "": slurm_id = slurm_info.split(" ")[-1].strip()
        else: 
            print(slurm_error)
            slurm_id = str(-1)
        print("Slurm ID: %s\nOutput: %s" % (slurm_id,out_file))
        slurm_ids.append(slurm_id)
        time.sleep(4) # don't overwrite the cache of the launched subprocess
    return slurm_ids

def save_launch_info(base,uuid_s,name,ids,files,pargs):
    names = [p.name for p in pargs]
    fn = base / ("%s_%s.txt" % (name,uuid_s))
    info = {"id":ids,"file":files,"name":names}
    df = pd.DataFrame(info)
    print("Info available at %s" % fn)
    df.to_csv(fn,index=False,sep=" ")

def create_paths(base,reset):
    output_dir = base / "output"
    launch_dir = base / "launching"
    info_dir = base / "info"
    if not(output_dir.exists()):
        output_dir.mkdir(parents=True)
    if not(launch_dir.exists()):
        launch_dir.mkdir(parents=True)
    if not(info_dir.exists()):
        info_dir.mkdir(parents=True)

    # -- reset dirs --
    if reset:
        remove_files(output_dir)
        remove_files(launch_dir)
        remove_files(info_dir)

    return output_dir,launch_dir,info_dir

def save_json(fn,pyobj):
    # Serializing json
    json_object = json.dumps(pyobj, indent=4)
    # Writing to sample.json
    with open(fn, "w") as outfile:
        outfile.write(json_object)

