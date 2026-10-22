"""Geometry-only copy and library retrieval, evaluated on matched groups only."""
from __future__ import annotations
import json
import math
from collections import Counter
from pathlib import Path
import numpy as np
from engine.retrieve import library, assign, FAMILY, ASPECT_TOL, LEFTOVER
from generator.download import digest
from generator.features import ROOT, load, SOURCES, ROLES, KINDS
from generator.make_data import atomic_json
from generator.partial_pairs import BUCKETS

def copy_boxes(boxes: np.ndarray, size: np.ndarray) -> np.ndarray:
    aw,ah,bw,bh = size; k=min(bw/aw,bh/ah)
    factor=np.array([aw*k/bw,ah*k/bh,aw*k/bw,ah*k/bh])
    offset=np.array([(bw-aw*k)/(2*bw),(bh-ah*k)/(2*bh),0,0])
    return boxes*factor+offset

def retrieval(boxes: np.ndarray, cat: np.ndarray, size: np.ndarray) -> tuple[np.ndarray,int]:
    aw,ah,bw,bh=map(float,size)
    fallback=copy_boxes(boxes,size)
    flow=[i for i,c in enumerate(cat) if KINDS[c[0]] not in {"background","panel"}]
    ours=Counter(ROLES[cat[i,1]] for i in flow)
    want=math.log(bw/bh)
    near=[d for d in library() if abs(math.log(d["aspect"])-want)<=ASPECT_TOL]
    near.sort(key=lambda d:(sum(abs(ours.get(r,0)-d["roles"].get(r,0)) for r in set(ours)|set(d["roles"])),abs(math.log(d["aspect"])-want)))
    outputs=[]
    for d in near[:16]:
        slots=d["units"]
        out=fallback.copy()
        if flow and slots:
            cost=np.empty((len(flow),len(slots)))
            for ii,i in enumerate(flow):
                role=ROLES[cat[i,1]]; kind="text" if KINDS[cat[i,0]]=="flow_text" else KINDS[cat[i,0]]
                for j,s in enumerate(slots):
                    x0,y0,x1,y1=s["box"]; w,h=max(x1-x0,1e-6),max(y1-y0,1e-6)
                    r=0 if role==s["role"] else .6 if FAMILY.get(role,role)==FAMILY.get(s["role"],s["role"]) else 1.5
                    c=0 if (kind=="text")== (s["kind"]=="text") else 1
                    area=.5*abs(math.log(max(boxes[i,2]*boxes[i,3],1e-6)/(w*h)))
                    shape=0 if kind=="text" else .5*abs(math.log(max(boxes[i,2]*aw,1e-6)/max(boxes[i,3]*ah,1e-6)/(w*bw)*h*bh))
                    cost[ii,j]=r+c+area+shape
            for ii,j in assign(np.hstack([cost,np.full((len(flow),len(flow)),LEFTOVER)])):
                if j<len(slots):
                    x0,y0,x1,y1=slots[j]["box"];out[flow[ii]]=[x0,y0,x1-x0,y1-y0]
        outputs.append(out)
    if not outputs: outputs=[fallback]
    actual=len(outputs)
    outputs += [outputs[-1].copy() for _ in range(16-len(outputs))]
    return np.stack(outputs),actual

def grouped(values: dict[str,np.ndarray], data: dict, indices: np.ndarray) -> list[dict]:
    result=[]
    for kind,k in enumerate(SOURCES):
        for b,label in [(-1,"all"),*enumerate(BUCKETS)]:
            take=(data["source"][indices]==kind)
            if b>=0:take&=data["bucket"][indices]==b
            if take.any(): result.append({"kind":k,"aspect_bucket":label,"pairs":int(take.sum()),
                                          **{name:float(np.mean(v[take])) for name,v in values.items()}})
    return result

def run() -> None:
    data=load();indices=np.flatnonzero(data["split"]==1)
    errors=[];copy=[];counts=[]
    candidates=np.lib.format.open_memmap(ROOT/"baseline_candidates.npy",mode="w+",dtype=np.float32,shape=(len(indices),16,40,4))
    for step,i in enumerate(indices):
        n=int(data["valid"][i].sum());boxes=data["cont"][i,:n,:4];mask=data["matched"][i,:n].astype(bool);target=data["target"][i,:n]
        prediction,count=retrieval(boxes,data["cat"][i,:n],data["size"][i])
        candidates[step,:,:n]=prediction
        errors.append(np.abs(prediction[:,mask]-target[mask]).mean(axis=(1,2)).min())
        copy.append(np.abs(copy_boxes(boxes,data["size"][i])[mask]-target[mask]).mean())
        counts.append(count)
        if step%1000==0:print(f"baselines {step}/{len(indices)}",flush=True)
    candidates.flush()
    np.savez(ROOT/"baselines.npz",indices=indices,copy=np.array(copy),retrieval_best16=np.array(errors),candidate_count=np.array(counts))
    result=grouped({"copy":np.array(copy),"retrieval_best16":np.array(errors)},data,indices)
    atomic_json(ROOT/"baselines.json",{"metrics":"mean per-pair masked box L1", "geometry_only":True,
        "library_sha256":digest(Path(__file__).resolve().parents[1]/"engine/data/layout_library.json"),
        "fewer_than_16_candidates":sum(c<16 for c in counts),"results":result})
    print("PASS: baselines",json.dumps(result),flush=True)

if __name__=="__main__":run()
