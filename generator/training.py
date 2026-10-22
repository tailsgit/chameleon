"""Finite-checked MPS training, resumable epoch sampler and validation selection."""
from __future__ import annotations
import argparse
import csv
import json
import os
import random
import time
from pathlib import Path
from typing import Any
import numpy as np
import torch
import yaml
from generator.batches import epoch_indices, tensors, finite_step
from generator.features import ROOT, RUNS, load
from generator.make_data import atomic_json
from generator.model import Generator, uniform_fit

def setup(seed:int)->None:
    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
    torch.set_num_threads(1);torch.use_deterministic_algorithms(True)
    assert torch.backends.mps.is_available(),"MPS unavailable; stop instead of silently changing device"

def cpu_tree(obj:Any)->Any:
    if isinstance(obj,torch.Tensor):return obj.detach().cpu()
    if isinstance(obj,dict):return {k:cpu_tree(v) for k,v in obj.items()}
    if isinstance(obj,list):return [cpu_tree(v) for v in obj]
    if isinstance(obj,tuple):return tuple(cpu_tree(v) for v in obj)
    return obj

def checkpoint(path:Path,model:Generator,optimizer:torch.optim.Optimizer,config:dict,state:dict)->None:
    temp=path.with_suffix(".partial")
    torch.save({"model":cpu_tree(model.state_dict()),"optimizer":cpu_tree(optimizer.state_dict()),"config":config,**state},temp)
    temp.replace(path)

@torch.no_grad()
def validate(model:Generator,data:dict,indices:np.ndarray,batch_size:int=64)->dict:
    model.eval();best=[];median=[];diversity=[]
    for start in range(0,len(indices),batch_size):
        b=tensors(data,indices[start:start+batch_size],"mps")
        out=model(b["cont"],b["cat"],b["valid"],b["canvas"],b["source"])
        error=(torch.abs(out-b["target"][:,None])*b["matched"][:,None,:,None]).sum((2,3))/(4*b["matched"].sum(1,keepdim=True))
        values=error.cpu().numpy()
        best.extend(values.min(1));median.extend(np.median(values,axis=1))
        pred=out.cpu().numpy();mask=b["matched"].cpu().numpy()
        # Mean over all 120 unordered latent pairs, not adjacent samples only.
        distance=np.abs(pred[:, :,None]-pred[:,None,:]).mean(-1)
        distance=(distance*mask[:,None,None,:]).sum(-1)/mask.sum(1)[:,None,None]
        ii,jj=np.triu_indices(16,1);diversity.extend(distance[:,ii,jj].mean(1))
    return {"best16":float(np.mean(best)),"median16":float(np.mean(median)),"pairwise_box_distance":float(np.mean(diversity))}

def overfit(config:dict,name:str)->None:
    setup(config["seed"]);data=load();root=RUNS/name;root.mkdir(parents=True,exist_ok=True)
    rng=np.random.default_rng(config["seed"])
    indices=np.concatenate([rng.choice(np.flatnonzero((data["split"]==0)&(data["source"]==k)),5,replace=False) for k in range(4)])
    b=tensors(data,indices,"mps");model=Generator(**config["model"]).to("mps")
    optimizer=torch.optim.AdamW(model.parameters(),lr=config["overfit_learning_rate"],weight_decay=config["weight_decay"])
    initial=float(((uniform_fit(b["cont"],b["canvas"])-b["target"]).abs()*b["matched"][...,None]).sum().item()/(4*b["matched"].sum().item()))
    values=[];begin=time.monotonic();passed=False
    with (root/"steps.csv").open("w",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=["step","loss","l1","overlap","kl","beta"]);writer.writeheader()
        for step in range(1,config["overfit_steps"]+1):
            model.train();v=finite_step(model,optimizer,b,step,config);values.append(v["l1"])
            writer.writerow({"step":step,**v})
            if step%50==0:
                model.eval()
                with torch.no_grad():
                    pred,_,_=model.training_output(**b,epsilon=torch.zeros(20,model.latent,device="mps"))
                    deterministic=float(((pred-b["target"]).abs()*b["matched"][...,None]).sum().item()/(4*b["matched"].sum().item()))
                stochastic=float(np.mean(values[-50:]))
                print(f"overfit step {step}: posterior L1={deterministic:.6f}; recent stochastic L1={stochastic:.6f}",flush=True)
                if deterministic<config["overfit_l1_threshold"] and stochastic<config["overfit_stochastic_threshold"]:
                    passed=True;break
    result={"pairs":20,"seed":config["seed"],"steps":step,"initial_copy_l1":initial,"posterior_l1":deterministic,
            "recent_stochastic_l1":stochastic,"seconds":time.monotonic()-begin,"passed":passed}
    atomic_json(root/"report.json",result)
    assert passed,f"overfit check failed: {result}"
    checkpoint(root/"last.pt",model,optimizer,config,{"step":step})
    print("PASS: overfit 20",json.dumps(result),flush=True)

def train(config:dict,name:str,seconds:float,resume:Path|None=None)->None:
    setup(config["seed"]);data=load();root=RUNS/name;root.mkdir(parents=True,exist_ok=True)
    model=Generator(**config["model"]).to("mps")
    assert 1_000_000<=sum(p.numel() for p in model.parameters())<=3_000_000
    optimizer=torch.optim.AdamW(model.parameters(),lr=config["learning_rate"],weight_decay=config["weight_decay"])
    state={"step":0,"epoch":0,"batch":0,"best":float("inf"),"bad_epochs":0,"elapsed_seconds":0.}
    if resume:
        ck=torch.load(resume,map_location="cpu",weights_only=False)
        assert ck["config"]==config,"resume config differs"
        model.load_state_dict(ck["model"]);optimizer.load_state_dict(ck["optimizer"])
        for opt_state in optimizer.state.values():
            for key,value in opt_state.items():
                if isinstance(value,torch.Tensor) and key!="step":opt_state[key]=value.to("mps")
        state.update({key:ck[key] for key in state})
    atomic_json(root/"config.json",config)
    val=np.flatnonzero((data["split"]==1)&(data["source"]==3))
    start=time.monotonic();last_ck=start;done=False;reason="max_epochs"
    fields=["step","epoch","batch","loss","l1","overlap","kl","beta"]
    csv_path=root/"steps.csv";exists=csv_path.exists()
    val_path=root/"validation.csv";val_exists=val_path.exists()
    with csv_path.open("a",newline="") as stream,val_path.open("a",newline="") as vs:
        writer=csv.DictWriter(stream,fieldnames=fields)
        vw=csv.DictWriter(vs,fieldnames=["epoch","step","train_l1","val_real_best16","val_real_median16","diversity","epoch_seconds"])
        if not exists:writer.writeheader()
        if not val_exists:vw.writeheader()
        for epoch in range(state["epoch"],config["max_epochs"]):
            schedule=epoch_indices(data,epoch,config["seed"],config["batches_per_epoch"])
            epoch_start=time.monotonic();l1_values=[]
            first=state["batch"] if epoch==state["epoch"] else 0
            for bi in range(first,len(schedule)):
                model.train();b=tensors(data,schedule[bi],"mps")
                v=finite_step(model,optimizer,b,state["step"]+1,config)
                state.update(step=state["step"]+1,epoch=epoch,batch=bi+1)
                l1_values.append(v["l1"])
                if state["step"]%10==0:writer.writerow({"step":state["step"],"epoch":epoch,"batch":bi+1,**v})
                now=time.monotonic()
                if state["step"]%100==0:
                    print(f"epoch {epoch} batch {bi+1}: step {state['step']} L1 {np.mean(l1_values[-100:]):.5f}; elapsed {now-start:.1f}s",flush=True);stream.flush()
                if now-last_ck>=config["checkpoint_seconds"]:
                    save=dict(state,elapsed_seconds=state["elapsed_seconds"]+now-start)
                    checkpoint(root/"last.pt",model,optimizer,config,save);last_ck=now
                if now-start+state["elapsed_seconds"]>=seconds:
                    done=True;reason="time_budget";break
            metrics=validate(model,data,val)
            row={"epoch":epoch,"step":state["step"],"train_l1":float(np.mean(l1_values)) if l1_values else 0.,
                "val_real_best16":metrics["best16"],"val_real_median16":metrics["median16"],"diversity":metrics["pairwise_box_distance"],
                "epoch_seconds":time.monotonic()-epoch_start}
            vw.writerow(row);vs.flush();stream.flush();print("validation",json.dumps(row),flush=True)
            improved=metrics["best16"]<state["best"]-config["min_delta"]
            if improved:state.update(best=metrics["best16"],bad_epochs=0)
            else:state["bad_epochs"]+=1
            if not done:state.update(epoch=epoch+1,batch=0)
            save=dict(state,elapsed_seconds=state["elapsed_seconds"]+time.monotonic()-start)
            checkpoint(root/"last.pt",model,optimizer,config,save);last_ck=time.monotonic()
            if improved:checkpoint(root/"best.pt",model,optimizer,config,save)
            if state["bad_epochs"]>=config["patience"]:reason="early_stop";done=True
            if done:break
    atomic_json(root/"report.json",{"reason":reason,"step":state["step"],"epoch":state["epoch"],"best_real_val_l1":state["best"],
        "wall_seconds":time.monotonic()-start,"model_params":sum(p.numel() for p in model.parameters()),"final_real_val":metrics})
    print("PASS: finite training completed",reason,flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--config",type=Path,default=Path(__file__).parent/"configs/cvae.yaml")
    p.add_argument("--name",required=True);p.add_argument("--mode",choices=["overfit","train"],default="train")
    p.add_argument("--seconds",type=float);p.add_argument("--resume",type=Path)
    a=p.parse_args();cfg=yaml.safe_load(a.config.read_text())
    if a.mode=="overfit":overfit(cfg,a.name)
    else:train(cfg,a.name,a.seconds or cfg["full_seconds"],a.resume)
