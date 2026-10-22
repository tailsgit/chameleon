"""Exact seeded batch shares and padding that keeps unmatched groups as context."""
from __future__ import annotations
import numpy as np
import torch

def epoch_indices(data:dict,epoch:int,seed:int,batches:int=1250)->np.ndarray:
    rng=np.random.default_rng(seed+epoch)
    columns=[]
    for kind,count in enumerate((24,24,16,16)):
        pool=np.flatnonzero((data["split"]==0)&(data["source"]==kind))
        n=batches*count
        values=rng.choice(pool,n,replace=kind>=2)
        columns.append(values.reshape(batches,count))
    result=np.concatenate(columns,axis=1)
    for row in result:rng.shuffle(row)
    return result

def tensors(data:dict,indices:np.ndarray,device:str)->dict:
    n=int(data["valid"][indices].sum(1).max())
    result={}
    for key in ("cont","cat","valid","matched","target"):
        result[key]=torch.from_numpy(np.array(data[key][indices,:n],copy=True)).to(device)
    result["canvas"]=torch.from_numpy(np.array(data["canvas"][indices],copy=True)).to(device)
    source=np.minimum(np.array(data["source"][indices],copy=True),3)
    result["source"]=torch.from_numpy(source).to(device)
    return result

def finite_step(model:torch.nn.Module,optimizer:torch.optim.Optimizer,batch:dict[str,torch.Tensor],step:int,config:dict)->dict[str,float]:
    seed=config["seed"]
    epsilon=torch.randn(len(batch["cont"]),model.latent,generator=torch.Generator().manual_seed(seed+step)).to(batch["cont"].device)
    pred,mu,logvar=model.training_output(**batch,epsilon=epsilon)
    from generator.model import loss_terms
    l1,overlap,kl=loss_terms(pred,batch["target"],batch["matched"],batch["cat"],mu,logvar)
    beta=config["kl_weight"]*min(1.,step/config["kl_warmup_steps"])
    total=l1+config["overlap_weight"]*overlap+beta*kl
    if not torch.isfinite(torch.stack([total,l1,overlap,kl])).all():
        raise FloatingPointError(f"non-finite loss at step {step}: total={total.item()}, l1={l1.item()}, overlap={overlap.item()}, kl={kl.item()}")
    optimizer.zero_grad(set_to_none=True);total.backward()
    grads=[p.grad.reshape(-1) for p in model.parameters() if p.grad is not None]
    if not torch.isfinite(torch.cat(grads)).all():
        names=[name for name,p in model.named_parameters() if p.grad is not None and not torch.isfinite(p.grad).all()]
        raise FloatingPointError(f"non-finite gradient at step {step}: {names}")
    torch.nn.utils.clip_grad_norm_(model.parameters(),config["grad_clip"],error_if_nonfinite=True)
    optimizer.step()
    return {"loss":total.item(),"l1":l1.item(),"overlap":overlap.item(),"kl":kl.item(),"beta":beta}
