"""All validation kinds/buckets, posterior-free fixed-latent inference only."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import torch
from generator.baselines import grouped
from generator.batches import tensors
from generator.features import ROOT, load
from generator.make_data import atomic_json
from generator.model import Generator

@torch.no_grad()
def run(checkpoint:Path)->dict:
    torch.set_num_threads(1);data=load();base=np.load(ROOT/"baselines.npz")
    indices=base["indices"];ck=torch.load(checkpoint,map_location="cpu",weights_only=False)
    model=Generator(**ck["config"]["model"]);model.load_state_dict(ck["model"]);model.eval().to("mps")
    best=[];median=[];diversity=[]
    for offset in range(0,len(indices),64):
        ii=indices[offset:offset+64];b=tensors(data,ii,"mps")
        prediction=model(b["cont"],b["cat"],b["valid"],b["canvas"],b["source"]).cpu().numpy()
        mask=b["matched"].cpu().numpy();target=b["target"].cpu().numpy()
        errors=(np.abs(prediction-target[:,None])*mask[:,None,:,None]).sum((2,3))/(4*mask.sum(1)[:,None])
        best.extend(errors.min(1));median.extend(np.median(errors,axis=1))
        distance=np.abs(prediction[:,:,None]-prediction[:,None,:]).mean(-1)
        distance=(distance*mask[:,None,None,:]).sum(-1)/mask.sum(1)[:,None,None]
        i,j=np.triu_indices(16,1);diversity.extend(distance[:,i,j].mean(1))
        if offset%1024==0:print(f"evaluation {offset}/{len(indices)}",flush=True)
    values={"model_best16":np.array(best),"model_median16":np.array(median),"copy":base["copy"],
            "retrieval_best16":base["retrieval_best16"],"mean_pairwise_distance":np.array(diversity)}
    rows=grouped(values,data,indices)
    real=next(r for r in rows if r["kind"]=="real" and r["aspect_bucket"]=="all")
    result={"checkpoint_step":ck["step"],"checkpoint_epoch":ck["epoch"],"results":rows,
            "collapse_threshold":ck["config"]["collapse_threshold"],
            "collapse_passed_real":real["mean_pairwise_distance"]>=ck["config"]["collapse_threshold"],
            "beats_both_real":real["model_best16"]<min(real["copy"],real["retrieval_best16"]),
            "improvement_over_copy_real":real["copy"]-real["model_best16"],
            "improvement_over_retrieval_real":real["retrieval_best16"]-real["model_best16"]}
    dest=checkpoint.parent;atomic_json(dest/"evaluation.json",result)
    np.savez(dest/"evaluation.npz",indices=indices,**values)
    lines=["Validation: matched groups only; mean per-pair normalized box L1. Lower is better.","",
           "| Kind | Aspect bucket | Pairs | Model best-16 | Model median-16 | Copy | Retrieval best-16 | Diversity |",
           "|---|---|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        lines.append(f"| {r['kind']} | {r['aspect_bucket']} | {r['pairs']} | {r['model_best16']:.5f} | {r['model_median16']:.5f} | {r['copy']:.5f} | {r['retrieval_best16']:.5f} | {r['mean_pairwise_distance']:.5f} |")
    (dest/"evaluation.md").write_text("\n".join(lines)+"\n")
    print("PASS: evaluation",json.dumps(result),flush=True)
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--checkpoint",type=Path,required=True);a=p.parse_args();run(a.checkpoint)
