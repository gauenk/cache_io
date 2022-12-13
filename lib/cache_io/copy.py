"""

Copy one cache name to another.

"""



def exp_cache(src,dest,configs=None,overwrite=False,skip_empty=True):
    """
    src,dest: Two ExpCache files
    """
    if configs is None:
        uuids,configs,results = src.load_raw(skip_empty)
    else:
        uuids,configs,results = src.load_raw_configs(configs,skip_empty)
    dest.save_raw(uuids,configs,results,overwrite)

#         self.root = root if isinstance(root,Path) else Path(root)
#         self.tensor_cache = TensorCache(root)
#         self.uuid_cache = UUIDCache(root,version)

# ExpCache
#     pass

