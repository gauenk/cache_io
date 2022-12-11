
# -- python imports --
import json
import numpy as np
from pathlib import Path
from ._debug import VERBOSE

def write_uuid_file(uuid_file,data):
    if VERBOSE: print(f"Writing: [{cfg.uuid_file}]")
    if not uuid_file.parents[0].exists():
        uuid_file.parents[0].mkdir(parents=True)
    data_json = json.dumps(data)
    with open(uuid_file,'w') as f:
        f.write(data_json)

class CustomJSONizer(json.JSONEncoder):
    def default(self, obj):
        return super().encode(bool(obj)) \
            if isinstance(obj, np.bool_) \
            else super().default(obj)
