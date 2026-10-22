"""Opset-17 CPU-only inference, all-val parity and two complete deterministic passes."""
from __future__ import annotations
import argparse
import hashlib
import json
import time
from pathlib import Path
import numpy as np
import onnx
import onnxruntime as ort
import torch
from generator.features import ROOT, load
from generator.make_data import atomic_json
from generator.model import Generator

def inputs(data:dict,idx:np.ndarray)->dict:
    return {"cont":np.array(data["cont"][idx]),"cat":np.array(data["cat"][idx]),"valid":np.array(data["valid"][idx]),
            "canvas":np.array(data["canvas"][idx]),"source":np.minimum(np.array(data["source"][idx]),3)}

@torch.no_grad()
def run(checkpoint:Path)->None:
    torch.set_num_threads(1);torch.manual_seed(2026);np.random.seed(2026)
    ck=torch.load(checkpoint,map_location="cpu",weights_only=False)
    model=Generator(**ck["config"]["model"]);model.load_state_dict(ck["model"]);model.eval()
    data=load();indices=np.flatnonzero(data["split"]==1);sample=inputs(data,indices[:2]);names=list(sample)
    args=tuple(torch.from_numpy(sample[k]) for k in names)
    out=checkpoint.parent/"generator.onnx"
    torch.onnx.export(model,args,str(out),input_names=names,output_names=["boxes"],opset_version=17,
        dynamic_axes={**{name:{0:"batch"} for name in names},"boxes":{0:"batch"}},do_constant_folding=True)
    graph=onnx.load(str(out));onnx.checker.check_model(graph)
    assert graph.opset_import[0].version==17
    assert not any(n.op_type.startswith("Random") for n in graph.graph.node)
    assert out.stat().st_size<10_000_000
    options=ort.SessionOptions();options.intra_op_num_threads=1;options.inter_op_num_threads=1
    options.execution_mode=ort.ExecutionMode.ORT_SEQUENTIAL
    sess=ort.InferenceSession(str(out),sess_options=options,providers=["CPUExecutionProvider"])
    first_hash=hashlib.sha256();second_hash=hashlib.sha256();maximum=0.
    for offset in range(0,len(indices),32):
        x=inputs(data,indices[offset:offset+32]);wanted=model(*(torch.from_numpy(x[k]) for k in names)).numpy()
        first=sess.run(["boxes"],x)[0];second=sess.run(["boxes"],x)[0]
        assert np.isfinite(first).all() and np.isfinite(wanted).all()
        assert np.array_equal(first,second),"ONNX output changed between repeated inference passes"
        maximum=max(maximum,float(np.abs(first-wanted).max()))
        first_hash.update(first.tobytes());second_hash.update(second.tobytes())
        if offset%1024==0:print(f"ONNX parity {offset}/{len(indices)}: max_abs={maximum:.3g}",flush=True)
    assert maximum<1e-5,f"ONNX max abs parity failed: {maximum}"
    assert first_hash.digest()==second_hash.digest()
    assert torch.equal(model(*args),model(*args)),"PyTorch CPU determinism failed"
    x=inputs(data,np.array([indices[np.flatnonzero(data['source'][indices]==3)[0]]]))
    for _ in range(20):sess.run(["boxes"],x)
    durations=[]
    for _ in range(100):
        start=time.perf_counter();sess.run(["boxes"],x);durations.append(time.perf_counter()-start)
    np.save(checkpoint.parent/"latents.npy",model.latents.numpy())
    atomic_json(checkpoint.parent/"export.json",{"opset":17,"bytes":out.stat().st_size,"max_abs_difference":maximum,
        "validation_pairs_checked":len(indices),"identical_two_passes":True,"output_sha256":first_hash.hexdigest(),
        "cpu_threads":1,"median_inference_ms_best16":float(np.median(durations)*1000),
        "p95_inference_ms_best16":float(np.quantile(durations,.95)*1000),"fixed_latents":16})
    print("PASS: ONNX export",(checkpoint.parent/"export.json").read_text(),flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--checkpoint",type=Path,required=True);a=p.parse_args();run(a.checkpoint)
