"""

Read and write experiments based on configs


"""

import shutil,os,json,tqdm,time
import pandas as pd
from pathlib import Path

# -- faster "to_records" --
from joblib import Parallel, delayed
from tqdm_joblib import tqdm_joblib # things are still slow

from tqdm import tqdm # things are slow.
from functools import partialmethod

import numpy as np
from einops import rearrange,repeat
from easydict import EasyDict as edict

from cache_io.uuid_cache import UUIDCache
from cache_io.tensor_cache import TensorCache

VERBOSE=False

def isfloat(num):
    try:
        float(num)
        return True
    except:
        return False

def isstr(num):
    try:
        num = str(num)
        return True
    except:
        return False


class FileCache():

    def __init__(self,root,version="v1"):
        self.root = root if isinstance(root,Path) else Path(root)
        self.tensor_cache = TensorCache(root)
        self.uuid_cache = UUIDCache(root,version)

    # -------------------------
    #     Primary API
    # -------------------------

    def read(self,config_or_uuid):
        # uuid = self.get_uuid_from_config(config)
        # if uuid == -1: return None
        uuid = self.ensure_uuid(config_or_uuid)
        if self.check_uuid_exists(uuid) is None:
            return None
        results = self.read_results(uuid)
        return results

    def write(self,uuid,results,overwrite=False):
        config = {"empty":"empty"}
        if uuid is None: uuid = self.get_uuid(config)
        exists = self.check_results_exists(uuid)
        if overwrite is True or exists is False:
            if (exists is True) and VERBOSE:
                print("Overwriting Old UUID.")
            if VERBOSE: print(f"UUID [{uuid}]")
            self.write_results(uuid,results)
        else:
            if VERBOSE:
                print(f"WARNING: Not writing. UUID [{uuid}] exists @ [{self.root}]")


    # -------------------------
    #     Clear Function
    # -------------------------

    def clear(self):
        print("Clearing Cache.")
        uuid_file = self.uuid_file
        if not uuid_file.exists(): return

        # -- remove all experiment results --
        data = self.uuid_cache.data
        for uuid in data.uuid:
            uuid_path = self.root / Path(uuid)
            if uuid_path.exists():
                shutil.rmtree(uuid_path)
                msg = f"exp cache [{uuid_path}] should be removed."
                assert not uuid_path.exists(),msg
            torch_path = self.pytorch_filepath(uuid)
            if torch_path.exists():
                shutil.rmtree(torch_path)
                msg = f"exp cache [{torch_path}] should be removed."
                assert not torch_path.exists(),msg

        # -- remove uuid cache --
        if uuid_file.exists(): os.remove(uuid_file)
        assert not uuid_file.exists(),f"uuid file [{uuid_file}] should be removed."
        # self.uuid_cache.init_uuid_file()

    def clear_exp(self,uuid):
        print(f"Clearing Experiment [uuid = {str(uuid)}]")

        # -- remove all experiment results --
        data = self.uuid_cache.data
        if not(uuid in data.uuid):
            print(f"[exp_cache] No experiment found with [uuid = {str(uuid)}]")
            return

        # -- remove exp data --
        uuid_path = self.root / Path(uuid)
        if uuid_path.exists():
            shutil.rmtree(uuid_path)
            msg = f"exp cache [{uuid_path}] should be removed."
            assert not uuid_path.exists(),msg
        torch_path = self.pytorch_filepath(uuid)
        if torch_path.exists():
            shutil.rmtree(torch_path)
            msg = f"exp cache [{torch_path}] should be removed."
            assert not torch_path.exists(),msg

        # -- remove uuid from uuid_cache --
        self.uuid_cache.remove_uuid(uuid)

    # -------------------------
    #     Tensor Management
    # -------------------------

    def convert_tensors_to_files(self,uuid,data):
        return self.tensor_cache.convert_tensors_to_files(uuid,data)

    def convert_files_to_tensors(self,uuid,data):
        return self.tensor_cache.convert_files_to_tensors(uuid,data)

    # -------------------------
    #     UUID Management
    # -------------------------

    def get_uuid(self,config,uuid=None,skips=None):
        return self.uuid_cache.get_uuid(config,uuid=uuid,skips=skips)

    def ensure_uuid(self,config_or_uuid):
        if isinstance(config_or_uuid,str):
            return config_or_uuid
        else:
            return self.get_uuid_from_config(config)

    def check_uuid_exists(self,uuid):
        path = self.root / Path(uuid) / "results.pkl"
        return path.exists()

    # -------------------------
    #   Read/Write Functions
    # -------------------------

    def get_uuid_from_config(self,config):
        return self.uuid_cache.get_uuid_from_config(config)

    def read_results(self,uuid):
        uuid_path = self.root / uuid
        if not uuid_path.exists(): return None
        results_path = uuid_path / "results.pkl"
        if not results_path.exists(): return None
        results = self.read_results_file(results_path,uuid)
        return results

    def results_exists(self,uuid):
        uuid_path = self.root / Path(uuid)
        results_path = uuid_path / "results.pkl"
        return results_path.exists()

    def write_results(self,uuid,results):
        uuid_path = self.root / Path(uuid)
        if not uuid_path.exists(): uuid_path.mkdir(parents=True)
        results_path = uuid_path / "results.pkl"
        self.write_results_file(results_path,uuid,results)

    def check_results_exists(self,uuid):
        path = self.root / Path(uuid) / "results.pkl"
        return path.exists()

    def write_results_file(self,path,uuid,data):
        if data is None:
            print("[exp_cache/__init__.py] Warning: data is None.")
            return
        data_files = self.convert_tensors_to_files(uuid,data)
        with open(path,'w') as f:
            json.dump(data_files,f)

    def read_results_file(self,path,uuid):
        with open(path,'r') as f:
            data = json.load(f)
        data_tensors = self.convert_files_to_tensors(uuid,data)
        return data_tensors

