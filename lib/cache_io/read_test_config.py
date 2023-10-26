

import copy,tqdm
dcopy = copy.deepcopy
import pprint
pp = pprint.PrettyPrinter(depth=5,indent=8)
import yaml
import pandas as pd
from pathlib import Path
from easydict import EasyDict as edict
# from cache_io import mesh_pydicts
from cache_io.exps import load,load_edata
from cache_io.api import ExpCache
from cache_io import view
from cache_io import train_stages

def run(fn,cache_name=None,reset=False,skip_dne=False):

    # -- load cache --
    exp_cache = None
    if not(cache_name is None):
        exp_cache = ExpCache(cache_name)
        # exp_cache.clear()
        if reset:
            exp_cache.clear()
        exps = exp_cache.load_raw_fast(skip_results=True)[1]
        if len(exps) > 0:
            return exps
        exp_cache.clear()

    # -- read formatted config file --
    data = read(fn)
    exps = []

    # -- shared --
    chkpt_root = data['chkpt_root']
    te_cfgs = load_grid(data['test_grid0']) # multiple in future
    label_info = data['label_info']
    chkpt_root = Path(data.chkpt_root)

    # -- load grids --
    if "train_grid" in data:
        _tr_cfgs = load_train_grid(data['train_grid'],chkpt_root,learn=True)
        pp.pprint(_tr_cfgs[0])
        tr_uuids = get_uuids(_tr_cfgs,data['train_cache_name'])
        # w/out learn
        tr_cfgs = load_train_grid(data['train_grid'],chkpt_root,learn=False)
        pp.pprint(tr_cfgs[0])
        # te_cfgs = load_grid(data['test_grid0'],data['train_grid']) # multiple in future
        fill_train = data['test_grid0'].fill_train_cfg
        fill_train_overwrite = data['test_grid0'].fill_train_overwrite
        # fixed = data['test_grid0'].fixed
        fill_skips = data['test_grid0'].skips

        # -- view --
        # print(len(tr_cfgs))
        # diffs = view.get_diffs(tr_cfgs)
        # view.print_loop(tr_cfgs,tr_uuids,diffs)
        # diffs = view.get_diffs(tr_cfgs)
        # view.print_loop(te_cfgs,[None for _ in range(len(te_cfgs))],diffs)

        # -- combine train and test grid --
        # print("len(te_cfgs): ",len(te_cfgs))
        exps += trte_mesh(tr_cfgs,tr_uuids,te_cfgs,label_info,chkpt_root,
                          fill_train,fill_train_overwrite,fill_skips,skip_dne)

    # -- append fixed pretrained paths --
    if "fixed_paths" in data:
        exps += append_fixed_paths(data['fixed_paths'],\
                                   te_cfgs,\
                                   data['train_cache_name'])

    # print("b.")
    # df = pd.DataFrame(exps)
    # print(len(exps))
    # f = ['ws','wt','ntype','sigma','rate','nepochs','tr_uuid','vid_name']
    # print(df[f])
    # df = df[f]
    # print(len(df))
    # print(len(df.drop_duplicates()))
    # df =df.drop_duplicates()
    # print(df)
    # exit(0)

    # -- view --
    # diffs = view.get_diffs(exps)
    # uuids = [None for _ in exps]
    # view.print_loop(exps,uuids,diffs)

    # -- save exps --
    if not(exp_cache is None):
        uuids = [str(i) for i,_ in enumerate(exps)]
        res = [{"empty":"null"} for e in exps]
        exp_cache.save_raw_fast(uuids,exps,res)
    return exps

def trte_mesh(tr_cfgs,tr_uuids,te_cfgs,label_info,chkpt_root,
              fill_train,fill_train_overwrite,fill_skips,skip_dne):
    exps = []
    for tr_cfg,tr_uuid in zip(tr_cfgs,tr_uuids):
        for _te_cfg in te_cfgs:
            te_cfg = dcopy(_te_cfg)
            if fill_train:
                append_cfg0(te_cfg,tr_cfg,overwrite=fill_train_overwrite,
                            skips=fill_skips)
            te_cfg.pretrained_path = get_test_pretrained(chkpt_root,te_cfg,
                                                         tr_cfg,tr_uuid)
            te_cfg.label0 = get_label(tr_cfg,label_info)
            te_cfg.label1 = get_label(te_cfg,label_info)
            te_cfg.tr_uuid = tr_uuid

            # -- skip DNE --
            # print(te_cfg.pretrained_path)
            exists = check_path(chkpt_root,tr_uuid,te_cfg.pretrained_path)
            if not(exists):
                msg = "Pretrained path must exist [%s]" % te_cfg.pretrained_path
                if skip_dne: continue
                else: raise ValueError(msg)

            # -- update flow --
            # if te_cfg.flow and te_cfg.wt == 0:
            #     print("setting flow to false since no wt.")
            #     te_cfg.flow = False
            exps.append(te_cfg)
    return exps

def get_test_pretrained(chkpt_root,te_cfg,tr_cfg,tr_uuid):
    if isinstance(te_cfg.nepochs,int):
        pretrained_path = "%s-epoch=%02d.ckpt" % (tr_uuid,te_cfg.nepochs-1)
        check_path = chkpt_root / tr_uuid / pretrained_path
        if not(check_path.exists()):
            pretrained_path = "%s-save-epoch=%02d.ckpt" % (tr_uuid,te_cfg.nepochs-1)
            check_path = chkpt_root / tr_uuid / pretrained_path
        # print(chkpt_root,tr_uuid,te_cfg.nepochs)
        # assert check_path.exists()
    elif te_cfg.nepochs == "latest":
        base = "%s-epoch=%02d.ckpt"
        pretrained_path,epoch = get_pretrained_latest(chkpt_root,tr_cfg,tr_uuid,base)
        if epoch == -1:
            base = "%s-save-epoch=%02d.ckpt"
            pretrained_path,epoch = get_pretrained_latest(chkpt_root,tr_cfg,tr_uuid,base)
    elif te_cfg.nepochs == "best":
        # base = "%s-epoch=%02d-val_loss=%1.2e.ckpt"
        base = "%s-epoch=%02d-val_loss=%1.2e.ckpt"
        pretrained_path,epoch = get_pretrained_best(chkpt_root,tr_cfg,tr_uuid,base)
        assert epoch != -1, "[Error] Must pick at least some epoch."
    else:
        raise ValueError("Uknown value %s" % str(te_cfg.nepochs))
    check_path = chkpt_root / tr_uuid / pretrained_path
    # assert check_path.exists()
    return str(pretrained_path)

def check_path(chkpt_root,tr_uuid,pretrained_path):
    check_path = chkpt_root / tr_uuid / pretrained_path
    return check_path.exists()

def get_pretrained_best(chkpt_root,tr_cfg,tr_uuid,base):
    # -- get paths with validation --
    path_base = chkpt_root / tr_uuid
    epoch,val_loss = -1,1000000
    for fn in path_base.iterdir():
        name = fn.name
        if not("val_loss" in name): continue
        _epoch = int(name.split("epoch=")[-1].split("-")[0])
        _val_loss = name.split("val_loss=")[-1].split(".ckpt")[0]
        if "-v" in _val_loss: continue
        _val_loss = float(_val_loss)
        if _val_loss < val_loss:
            epoch = _epoch
            val_loss = _val_loss
    path = str(base) % (tr_uuid,epoch,val_loss)
    return path,epoch

def get_pretrained_latest(chkpt_root,tr_cfg,tr_uuid,base):
    pick_epoch = -1
    pretrained_path = base % (tr_uuid,-1)
    for epoch in range(tr_cfg.nepochs):
        path = chkpt_root / tr_uuid / (base % (tr_uuid,epoch))
        if path.exists():
            pretrained_path = path.name
            pick_epoch = epoch
    return pretrained_path,pick_epoch

def get_label(exp,label_info):
    args = []
    for key in label_info['keys']:
        if key in label_info:
            val = label_info[key][exp[key]]
        else:
            if key in exp:
                val = exp[key]
            else:
                val = "Missing"
        args.append(val)
    label = ""
    if len(label_info['fmt']) > 0:
        label = label_info['fmt'] % tuple(args)
    return label

# def get_checkpoint(checkpoint_dir,uuid,nepochs):
#     chkpt_fn = Path(checkpoint_dir) / ("%s-epoch=%02d.ckpt" % (uuid,nepochs))
#     return chkpt_fn

def get_uuids(exps,name,version="v1"):
    cache = ExpCache(name,version)
    uuids = []
    for exp in tqdm.tqdm(exps):
        uuid = cache.read_uuid(exp)
        if uuid == -1:
            print(uuid)
            pp.pprint(exp)
            print("Couldn't find experiment in the training set.")
            exit(0)
        uuids.append(uuid)
    return uuids

def load_train_grid(stages,chkpt_root,learn=True):
    exps,_ = train_stages.run_core(stages,chkpt_root,use_learn=learn)
    return exps

def load_grid(grid,learn=True):
    return load_mesh_grid(grid,learn=learn)
    # if grid.type == "self":
    #     return load_self_grid(grid,tr_grid)
    #     # raise NotImplementedError("Uknown test grid type.")
    # elif grid.type == "mesh":
    #     exps = load_mesh_grid(grid)
    # else:
    #     raise NotImplementedError("Uknown test grid type.")
    # return exps

def load_self_grid(te_grid,tr_grid):
    """
    Only test/training on the same grid of parameters
    example: train/test on g(30) and p(10,10), separately. no cross
    """
    print("WARNING: I am never called.")
    exit()
    tr_exps = load_mesh_grid(tr_grid,learn=False)
    te_exps = load_mesh_grid(te_grid)
    exps = mesh_pairs(tr_exps,te_exps)
    return exps

def load_mesh_grid(grid,learn=True):
    exps_var = load_edata(grid.mesh)
    exp_base = load(grid.base) # size is 1
    assert len(exp_base) == 1
    exp_base = exp_base[0]
    if "learning" in grid and learn:
        exp_learn = load(grid["learning"])
        assert len(exp_learn) == 1
        exp_learn = exp_learn[0]
        append_cfg0(exp_base,exp_learn)
    exps = mesh_base_var(exp_base,exps_var)
    return exps

def append_fixed_paths(fixed_paths,te_cfgs,cache_name):

    # -- pretrained opts --
    pretrained_opts = ["root","load","type"]
    L = len(fixed_paths['path'])

    # -- load other opts --
    misc_opts = list(fixed_paths.keys())
    print(misc_opts)
    if "path" in misc_opts:
        del misc_opts[misc_opts.index("path")]
    for opt in pretrained_opts:
        if opt in misc_opts:
            del misc_opts[misc_opts.index(opt)]

    exps = []
    for te_cfg in te_cfgs:
        for i in range(L):

            # -- fill --
            exp = dcopy(te_cfg)
            exp.pretrained_path = fixed_paths['path'][i]

            # -- fill pretrained optional --
            for opt in pretrained_opts:
                if opt in fixed_paths:
                    exp["pretrained_%s" % opt] = fixed_paths[opt][i]

            # -- fill from uuid --
            if 'tr_uuid' in fixed_paths:
                uuid = fixed_paths['tr_uuid'][i]
                cache = ExpCache(cache_name)
                config = cache.get_config_from_uuid(uuid)
                for key,val in config.items():
                    if not(key in exp):
                        exp[key] = val

            # -- fill misc [overwrite from uuid] --
            for opt in misc_opts:
                exp[opt] = fixed_paths[opt][i]

            # -- append --
            exps.append(exp)
    return exps

def append_cfg0(cfg0,cfg1,overwrite=False,skips=None):
    _skips = ["uuid"]
    if not(skips is None):
        _skips += skips
    for key in cfg1:
        if key in _skips: continue
        if not(key in cfg0) or overwrite:
            cfg0[key] = cfg1[key]

def mesh_base_var(exp_base,exps_var):
    exps = []
    for exp_v in exps_var:
        exp_b = dcopy(exp_base)
        for key in exp_v:
            exp_b[key] = exp_v[key]
        exps.append(exp_b)
    return exps

def mesh_pairs(exps0,exps1):
    print("WARNING: I am never called.")
    exit()
    exps = []
    for _exp0 in exps0:
        for _exp1 in exps1:
            exp0 = dcopy(_exp0)
            exp1 = dcopy(_exp1)
            append_cfg0(exp0,exp1)
            exps.append(exp0)
    return exps

def create_config(base,exp):
    cfg = dcopy(base)
    for key in exp:
        if key == "prev": continue
        cfg[key] = exp[key]
    return cfg

def read(fn):
    with open(fn,"r") as stream:
        data = yaml.safe_load(stream)
    return edict(data)

