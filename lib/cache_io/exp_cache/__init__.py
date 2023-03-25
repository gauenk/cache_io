"""

Read and write experiments based on configs


"""

import shutil,os,json,tqdm
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


class ExpCache():

    def __init__(self,root,version):
        self.root = root if isinstance(root,Path) else Path(root)
        self.tensor_cache = TensorCache(root)
        self.uuid_cache = UUIDCache(root,version)

    @property
    def version(self):
        return self.uuid_cache.version

    @property
    def uuid_file(self):
        return self.uuid_cache.uuid_file

    def get_uuid_from_config(self,config):
        return self.uuid_cache.get_uuid_from_config(config)

    def get_config_from_uuid(self,uuid):
        return self.uuid_cache.get_config_from_uuid(uuid)

    def convert_tensors_to_files(self,uuid,data):
        return self.tensor_cache.convert_tensors_to_files(uuid,data)

    def convert_files_to_tensors(self,uuid,data):
        return self.tensor_cache.convert_files_to_tensors(uuid,data)

    # ---------------------
    #   Primary Functions
    # ---------------------

    def load_exp(self,config):
        uuid = self.get_uuid_from_config(config)
        if uuid == -1: return None
        results = self.read_results(uuid)
        return results

    def load_exps(self,configs=None,skip_empty=False):
        if configs is None:
            return self.load_raw()
        else:
            return self.load_raw_exps(configs,skip_empty=skip_empty)

    # def load_exp(self,config):
    #     uuid = self.get_uuid_from_config(config)
    #     print(uuid)
    #     if uuid == -1: return None
    #     results = self.read_results(uuid)
    #     return results

    def save_exp(self,uuid,config,results,overwrite=False):
        # check_uuid = self.get_uuid_from_config(config)
        # 12/21/21 -- the assert statement is logical error
        # we want to be able to set the uuid before we save the experiment.
        # assert check_uuid == -1,"The \"config\" must not exist in the uuid cache."
        # assert uuid == check_uuid, "Only one uuid per config."
        exists = self.check_results_exists(uuid)
        if overwrite is True or exists is False:
            if (exists is True) and VERBOSE:
                print("Overwriting Old UUID.")
            if VERBOSE: print(f"UUID [{uuid}]")
            self.write_results(uuid,results)
        else:
            if VERBOSE:
                print(f"WARNING: Not writing. UUID [{uuid}] exists @ [{self.root}]")

    def read_uuid(self,config):
        return self.uuid_cache.read_uuid(config)

    # def get_uuids(self,configs,uuids=None,skips=None):
    #     out_uuids = []
    #     for i,config in enumerate(configs):
    #         uuid = None if uuids is None else uuids[i]
    #         uuid = self.get_uuid(config,uuid=uuid,skips=skips)
    #         out_uuids.append(uuid)
    #     return uuid

    def get_uuid(self,config,uuid=None,skips=None):
        return self.uuid_cache.get_uuid(config,uuid=uuid,skips=skips)

    def add_uuid_config_pair(self,uuid,config):
        self.uuid_cache.add_uuid_config_pair(uuid,config)

    def load_records(self,exps,save_agg=None,clear=False):
        return self.load_flat_records(exps,save_agg,clear)
        # records = []
        # for config in tqdm.tqdm(exps):
        #     results = self.load_exp(config)
        #     uuid = self.get_uuid(config)
        #     if results is None: continue
        #     self.append_to_record(records,uuid,config,results)
        # records = pd.DataFrame(records)
        # return records

    def append_to_record(self,records,uuid,config,results):
        record = {'uuid':uuid}
        for key,value in config.items():
            record[key] = value
        for result_id,result in results.items():
            record[result_id] = result
        records.append(record)

    def save_raw(self,uuids,configs,results,overwrite=False,use_tqdm=False):
        N  = len(uuids)
        zipped = zip(uuids,configs,results)
        tqdm.__init__ = partialmethod(tqdm.__init__, disable=not(use_tqdm))
        for uuid,config,result in tqdm(zipped,total=N):
            # print(uuid)
            self.uuid_cache.add_uuid(uuid,config,overwrite)
            config.uuid = uuid
            # print(uuid,result is None,overwrite)
            self.save_exp(uuid,config,result,overwrite)
        # print(self.uuid_cache.data.uuid)

    def save_raw_fast(self,uuids,configs,results):
        """

        runs save_raw but does not check uniqueness and overwrites all values

        """
        uuid_data = edict({'uuid':uuids,'config':configs})
        self.uuid_cache.write_uuid_file(uuid_data)
        for uuid,res in zip(uuids,results):
            if res is None: continue
            self.write_results(uuid,res)

    def append_raw_fast(self,uuids,configs,results):
        """

        runs append_raw but only checks uuid uniqueness and overwrites all values

        """

        # -- (1) Filter by existing uuid --
        data = self.uuid_cache.data
        # print(data['uuid'])
        uuids_f,configs_f,results_f = [],[],[]
        for (uuid,cfg,res) in zip(uuids,configs,results):
            if uuid in data['uuid']: continue
            # if not(self.results_exists(uuid)): continue
            uuids_f.append(uuid)
            configs_f.append(cfg)
            results_f.append(res)

        # -- (2) append new (uuids,cfgs) --
        # print(len(uuids_f))
        uuids = data['uuid'] + uuids_f
        configs = data['config'] + configs_f
        uuid_data = edict({'uuid':uuids,'config':configs})
        self.uuid_cache.write_uuid_file(uuid_data)

        # -- (3) write new results --
        for uuid,res in zip(uuids_f,results_f):
            if res is None: continue
            self.write_results(uuid,res)


    def load_raw(self,skip_empty=True):
        uuids = []
        configs = []
        results = []
        data = self.uuid_cache.data
        if data is None: return [],[],[]
        for uuid in data.uuid:
            config = self.get_config_from_uuid(uuid)
            result = self.load_exp(config)
            if (result is None) and skip_empty: continue
            uuids.append(uuid)
            configs.append(config)
            results.append(result)
        return uuids,configs,results

    def load_raw_fast(self,skip_results=False):
        uuid_data = self.uuid_cache.data
        if uuid_data is None:
            uuids = []
            cfgs = []
        else:
            uuids = uuid_data['uuid']
            cfgs = uuid_data['config']
        if skip_results or (uuid_data is None):
            results = [None for _ in range(len(cfgs))]
        else:
            uuids_l,cfgs_l = uuids,cfgs
            uuids,cfgs = [],[]
            results = []
            for uuid,cfg in zip(uuids_l,cfgs_l):
                if not(self.check_results_exists(uuid)): continue
                result = self.load_exp(cfg)
                if result is None: continue
                uuids.append(uuid)
                cfgs.append(cfg)
                results.append(result)
        return uuids,cfgs,results

    def load_raw_configs(self,in_configs,skip_empty=True):
        return self.load_raw_exps(in_configs,skip_empty)

    def load_raw_exps(self,in_configs,skip_empty=True):
        uuids = []
        results = []
        configs = []
        for config in in_configs:
            uuid = self.get_uuid(config)
            result = self.load_exp(config)
            if (result is None) and skip_empty: continue
            uuids.append(uuid)
            configs.append(config)
            results.append(result)
        return uuids,configs,results

    def load_all_records(self):
        records = []
        data = self.uuid_cache.data
        for uuid in data.uuid:
            config = self.get_config_from_uuid(uuid)
            results = self.load_exp(config)
            if results is None: continue
            self.append_to_flat_record(records,uuid,config,results)
        records = pd.concat(records)
        return records

    def _load_agg_records(self,save_agg,clear=False):
        # -- check if saved --
        records = None
        if not(save_agg is None):
            save_agg = Path(save_agg)
            pdir = save_agg.parents[0]
            if not(pdir.exists()):
                print("Creating Aggregation Cache Path: %s" % str(pdir))
                pdir.mkdir()
            if save_agg.exists() and clear is False:
                records = pd.read_pickle(str(save_agg))
            elif save_agg.exists() and clear is True:
                save_agg.unlink() # delete file.
            return records
        else:
            return None

    def _save_agg_records(self,records,save_agg):
        # -- check if saved --
        if not(save_agg is None):
            save_agg = Path(save_agg)
            records.to_pickle(save_agg)

    def load_flat_records(self,exps,save_agg=None,clear=False):
        return self.to_records(exps,save_agg,clear)

    def to_records_fast(self,save_agg=None,clear=False,results_fxn=None):
        """

        Load records quickly without checking caches each time.

        """
        # -- [optional] check & rtn if saved --
        records = self._load_agg_records(save_agg,clear)
        if not(records is None):
            return records

        # -- [optional] post-process records --
        if results_fxn is None:
            results_fxn = lambda x: x

        # -- gather uuids,exps --
        uuids = self.uuid_cache.data['uuid']
        exps = self.uuid_cache.data['config']

        # -- def parallel fxn --
        def append(cfg,uuid):
            record = []
            # uuid = self.uuid_cache.read_uuid(cfg) # not allowed to optionally write.
            assert uuid != -1,"All uuids must exist for fast read to work."
            # results = self.load_exp(cfg)
            results = self.read_results(uuid)
            if results is None:
                print("Missing results for uuid [%d]" % str(uuid),flush=True)
                return []
            results = results_fxn(results)
            self.append_record(record,uuid,cfg,results)
            return record[0]

        # -- launch parallel --
        # uuids = self.uuid_cache.data['uuid']
        # cfgs = self.uuid_cache.data['config']
        E = len(exps)
        append_d = delayed(append)
        with tqdm_joblib(desc="Loading Experiment Results", total=E) as progress_bar:
            records = Parallel(n_jobs=16)(append_d(exp,uuid) for exp,uuid in zip(exps,uuids))
        records = pd.concat(records)
        records.reset_index(inplace=True,drop=True)

        # -- [optional] save agg records --
        self._save_agg_records(records,save_agg)

        return records

    def to_records(self,exps,save_agg=None,clear=False,results_fxn=None):
        """
        Load records but flatten exp configs against
        experiments. Requires "results" to be have
        equal number of rows.
        """

        # -- [optional] check & rtn if saved --
        records = self._load_agg_records(save_agg,clear)
        if not(records is None):
            return records

        # -- [optional] post-process records --
        if results_fxn is None:
            results_fxn = lambda x: x

        # -- load each record --
        records = []
        for config in tqdm(exps):
            results = self.load_exp(config)
            uuid = self.get_uuid(config)
            if results is None: continue
            results = results_fxn(results)
            self.append_to_flat_record(records,uuid,config,results)
        records = pd.concat(records)
        records.reset_index(inplace=True,drop=True)

        # -- [optional] save agg records --
        self._save_agg_records(records,save_agg)

        return records

    def append_to_flat_record(self,records,uuid,config,results):
        return self.append_record(records,uuid,config,results)

    def append_record(self,records,uuid,config,results):

        # -- init --
        record = {}

        # -- append results --
        rlen = -1
        for result_id,result in results.items():
            if isstr(result): result = [result]
            if isfloat(result): result = np.array([result])
            if len(result) == 0: continue
            rlen = len(result) if rlen == -1 else rlen
            record[result_id] = list(result)
            if len(result) < rlen:
                assert len(result) == 1,"if neq must be 1."
                val = np.array([result[0]])
                record[result_id] = list(repeat(val,'1 -> r',r=rlen))
            elif len(result) > rlen and rlen > 1:
                raise ValueError("We can't have multiple results lengths.")

        # -- repeat uuid --
        uuid_np = repeat(np.array([str(uuid)]),'1 -> r',r=rlen)
        record['uuid'] = list(uuid_np)

        # -- standard append for config; each is a single value --
        for key,value in config.items():
            if hasattr(value,"__getitem__"): # iterables become strings.
                value = str(value)
            record[key] = list(repeat(np.array([value]),'1 -> r',r=rlen))

        # -- create id along axis --
        pdid = np.arange(rlen)
        record['pdid'] = np.arange(rlen)

        # -- repeat config info along result axis --
        all_equal,msg = self.check_equal_field_len(record)
        if not(all_equal): record = self.try_to_expand_record(record)
        all_equal,msg = self.check_equal_field_len(record)
        assert all_equal,f"All record shapes must be equal.\n\n{msg}"
        pdid = record['pdid']

        # -- squeeze to 0-dim if possible --
        self.squeeze_0dims(record,rlen)

        # -- append --
        record = pd.DataFrame(record,index=pdid)
        records.append(record)

    def squeeze_0dims(self,record,rlen):
        if rlen == 1:
            for key,val in record.items():
                # print(key)
                # print(key,type(val),type(val[0]),len(val),val[0].ndim)
                # if len(val) == 1:
                #     record[key] = val[0]
                if val[0] is None:
                    record[key] = val
                elif val[0].ndim == 0:
                    record[key] = val[0]

    def check_equal_field_len(self,record):
        all_equal,msg,vlen = True,"",-1
        for key,val in record.items():
            if vlen == -1: vlen = len(val)
            elif vlen != len(val): all_equal = False
            msg += "%s, %d\n" %( key, len(val) )
        return all_equal,msg

    def try_to_expand_record(self,record):
        max_len,num_ones,nmax = 0,0,0
        for key,val in record.items():
            if len(val) == 1: num_ones += 1
            if len(val) > max_len:
                max_len = len(val)
                nmax = 0
            if len(val) == max_len: nmax += 1
        if (num_ones + nmax) != len(record):
            return record
        # print("Trying to expand single record match values.")
        for key,val in record.items():
            vlen = len(val)
            if vlen == 1:
                if isinstance(val,list):
                    record[key] = np.array(record[key]*max_len)
                elif isinstance(val,np.ndarray):
                    record[key] = record[key][None,:].repeat(max_len,0)
            if isinstance(val,list):
                record[key] = np.array(record[key]).squeeze()
        record['pdid'] = np.arange(max_len) # replace "pandas ID"

        return record

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

    # -- allow for model checkpoints to be removed with cache --
    def pytorch_filepath(self,uuid):
        pytorch_models = self.root/"pytorch_models"/uuid
        return pytorch_models

    # -------------------------
    #   Read/Write Functions
    # -------------------------

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
