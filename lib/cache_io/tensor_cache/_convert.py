import numpy as np
from pathlib import Path

from ._read import *
from ._append import *
from ._utils import *

def convert_files_to_tensors(root,results):
    tensors = {}
    for field,field_data in results.items():
        path =  root / field
        names = get_tensor_cache_names(path,field_data)
        data = read_tensor_cache(path,names)
        tensors[field] = data
    return tensors

def convert_list_tensors_to_files(root,results):
    if isinstance(results,list):
        for i,result_i in enumerate(results):
            files = convert_tensors_to_files(root,result_i,overwrite=(i==0))
        # print(files)
    else:
        files = convert_tensors_to_files(root,results,overwrite=True)
    return files

def convert_tensors_to_files(root,results,overwrite=True):
    files = {}
    for field,field_data in results.items():
        path = root / field
        ll_append_tensor_cache(path,field_data,overwrite=overwrite)
        files[field] = str(path)
    return files
