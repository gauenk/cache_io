"""
UUID Cache

Converts a collection of python dictionaries
with many keys into a uuid string
to be saved into a file.

UUID_DATABASE =

   key_1    |   key_1    | ... |    uuid
  v_{1,1}   |   v_{1,2}  | ... |   uuid_{1}
  v_{2,1}   |   v_{2,2}  | ... |   uuid_{2}
  ...
  v_{N,1}   |   v_{N,2}  | ... |   uuid_{N}


--- Functionality ---

- dictionary <-> uuid
  - write uuid specific filename
  - read u
- compare two dictionaries

root_directory/
    uuid_database_{version}.json
    uuid_str_1
    uuid_str_2
    ...
    uuid_str_N

uuid_database_{version}.json stores the UUID_DATABASE (pic above)

"""


import json,pprint
import uuid as uuid_gen
from easydict import EasyDict as edict

from ._write import *
from ._read import *
from ._utils import *
from ._convert import *
from ._append import *
from ._debug import *

class UUIDCache():

    def __init__(self,root,cache_name):
        self.root = root if isinstance(root,Path) else Path(root)
        self.cache_name = cache_name
        self.uuid_file_skel = "uuid_database_{:s}.json"
        # self.init_uuid_file()

    @property
    def uuid_file(self):
        return self.root / self.uuid_file_skel.format(self.cache_name)

    @property
    def data(self):
        """
        data (easydict)

        data.config (list of python dicts)
        data.uuid (list of uuids)

        data.config[i] is a list of (key,values) corresponding to data.uuid[i]
        """
        data = read_uuid_file(self.uuid_file)
        if data is None:
            self.init_uuid_file()
            data = read_uuid_file(self.uuid_file)
        return data

    def write_uuid_file(self,data):
        write_uuid_file(self.uuid_file,data)

    def remove_uuid(self,uuid):
        data = read_uuid_file(self.uuid_file)
        if not(uuid in data):
            print(f"[uuid_cache] No uuid found in cache [uuid = {str(uuid)}]")
            return
        del data[uuid]
        write_uuid_file(self.uuid_file,data)

    def get_uuid_from_config(self,exp_config,skips=None):
        if self.data is None:
            self.init_uuid_file()
            return -1
        else:
            return get_uuid_from_config(self.data,exp_config,skips=skips)

    def get_config_from_uuid(self,uuid):
        if self.data is None:
            self.init_uuid_file()
            return None
        else:
            return get_config_from_uuid(self.data,uuid)

    def get_config_from_uuid_list(self,uuids):
        configs = []
        for uuid in uuids:
            configs.append(self.get_config_from_uuid(uuid))
        return configs

    def init_uuid_file(self):
        if VERBOSE: print(f"Init [{self.uuid_file}]")
        if self.uuid_file.exists(): return None
        data = edict({'uuid':[],'config':[]})
        write_uuid_file(self.uuid_file,data)

    def add_uuid(self,uuid,config,overwrite=False,skips=None):
        self.add_uuid_config_pair(uuid,config,overwrite,skips=skips)

    def get_uuid(self,exp_config,uuid=None,skips=None):
        uuid_cfg = self.get_uuid_from_config(exp_config,skips=skips)
        if uuid_cfg == -1:
            if VERBOSE: print("Creating a new UUID and adding to cache file.")
            uuid = str(uuid_gen.uuid4()) if uuid is None else uuid
            self.add_uuid_config_pair(uuid,exp_config,skips=skips)
            # new_pair = edict({'uuid':uuid,'config':exp_config})
            # append_new_pair(self.data,self.uuid_file,new_pair)
            return uuid
        else:
            if VERBOSE: print(f"Exp Config has a UUID {uuid}")
            return uuid_cfg

    def add_uuid_config_pair(self,uuid,exp_config,overwrite=False,skips=None):
        if self.data is None:
            # print("\n"*10 + "init!" + "\n"*10)
            self.init_uuid_file()
        new_pair = edict({'uuid':uuid,'config':exp_config})
        append_new_pair(self.data,self.uuid_file,new_pair,overwrite,skips=skips)

    def append_new(self,new_field,new_data):
        print("WARNING: This feature needs updating.")
        exit(0)
        data = self.data
        cont = set_new_field_default(data,new_field,default)
        if cont == -1:
            print(f"Not appending new field [{new_field}]. Field already exists.")
            return None
        set_new_field_data(data,new_data,new_field)
        self.cache_name = self.cache_name + 1
        write_uuid_file(self.uuid_file,data)
        print(f"Upgraded UUID cache cache_name from v{self.cache_name-1} to v{self.cache_name}")

    def __str__(self):
        return f"UUIDCache cache_name [{self.cache_name}] with file at [{self.uuid_file}]"


