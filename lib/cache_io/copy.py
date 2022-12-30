"""

Copy one cache name to another.


    cache_dir,cache_name = "a","a"
    cache = cache_io.ExpCache(cache_dir,cache_name)
    cache_dir,cache_name = "b","b"
    cache1 = cache_io.ExpCache(cache_dir,cache_name)
    exps = get_list_of_experiments()
    cache_io.copy.exp_cache(cache1,cache,exps)
    # copy from "cache1" to "cache"

"""



def exp_cache(src,dest,configs=None,overwrite=False,skip_empty=True):
    """
    src,dest: Two ExpCache files
    """
    if configs is None:
        uuids,configs,results = src.load_raw(skip_empty)
    else:
        uuids,configs,results = src.load_raw_configs(configs,skip_empty)
    if len(configs) == 0: warn_message(src)
    dest.save_raw(uuids,configs,results,overwrite)

def warn_message(src):
    msg = "No source data found.\n"
    msg += f"Check folders at [{src.root}]\n"
    msg += f"Example uuid: [{list(src.uuid_cache.data['uuid'])[0]}]\n"
    print(msg)

#         self.root = root if isinstance(root,Path) else Path(root)
#         self.tensor_cache = TensorCache(root)
#         self.uuid_cache = UUIDCache(root,version)

# ExpCache
#     pass

