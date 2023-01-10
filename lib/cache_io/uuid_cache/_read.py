
import json
from pathlib import Path
from easydict import EasyDict as edict

from ._debug import VERBOSE

def read_uuid_file(uuid_file):
    if VERBOSE: print(f"Reading: [{uuid_file}]")
    if not uuid_file.exists(): return None
    try:
        with open(uuid_file.resolve(),'r') as f:
            data_json = f.read()
        data = edict(json.loads(data_json))
    except Exception as e:
        raise ValueError(f"Can't open uuid_file [{str(uuid_file)}]")
    return data


class CustomJSONizer(json.JSONDecoder):
    def default(self, obj):
        return super().encode(bool(obj)) \
            if obj=="true"\
            else super().default(obj)

            # if isinstance(obj, np.bool_) \
            # else super().default(obj)


