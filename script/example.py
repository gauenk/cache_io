

# -- import pacakge --
import cache_io

# -- example experiment script --
def exec_experiment(config):
    import numpy.random as npr
    acc =  npr.randint(config['noise_level'])
    prec =  npr.randint(config['noise_level'])
    return {"accuracy":[acc],"precision":[prec]}

#
# -- (1) Init Experiment Cache  --
#

verbose = False
cache_dir = ".cache_io"
cache_name = "example"
cache = cache_io.ExpCache(cache_dir,cache_name)
# cache.clear() # optionally reset values

#
# -- (2) Load An Meshgrid of Python Dicts: each describe an experiment --
#

exps = {"noise_level":[10.,25.,50.],
        "nn_arch":["unet","bert"],
        "dataset":["davis","kitti"]}
experiments = cache_io.mesh_pydicts(exps)

# -- (3) [Execute or Load] each Experiment --
nexps = len(experiments)
for exp_num,config in enumerate(experiments):

    # -- info --
    if verbose:
        print("-="*25+"-")
        print(f"Running exeriment number {exp_num+1}/{nexps}")
        print("-="*25+"-")
        print(config)


    # -- logic --
    results = cache.load_exp(config) # possibly load result
    uuid = cache.get_uuid(config) # assing ID to each Dict in Meshgrid
    if results is None: # check if no result
        results = exec_experiment(config) # [exec experiment]
        cache.save_exp(uuid,config,results) # save to cache

# -- 
records = cache.load_flat_records(experiments)
print(records.columns)
print(records[['accuracy','precision','dataset','nn_arch','noise_level']])





