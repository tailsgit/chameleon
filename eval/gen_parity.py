"""Float32 training checkpoint versus engine ONNX on 200 held-out designs."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import torch
from engine.gen_candidates import features,runtime
from generator.model import Generator
from generator.pair_data import cached_rows
from eval.gen_integration import OUT,atomic


def run()->None:
    torch.set_num_threads(1);torch.manual_seed(2026);np.random.seed(2026)
    checkpoint=OUT.parent/'runs/cvae_full/best.pt'
    ck=torch.load(checkpoint,map_location='cpu',weights_only=False)
    model=Generator(**ck['config']['model']);model.load_state_dict(ck['model']);model.eval()
    chosen=[r for r in cached_rows() if r['split']=='val'][:200]
    maximum=0.
    with torch.no_grad():
        for i,row in enumerate(chosen):
            target={'width':1080,'height':1920} if i%2 else {'width':1920,'height':1080}
            x=features(row['groups'],dict(zip(['width','height'],row['canvas'])),target)
            n=len(row['groups'])
            expected=model(*(torch.from_numpy(x[k]) for k in ['cont','cat','valid','canvas','source'])).numpy()[:,:,:n]
            actual=runtime()[0].run(['boxes'],x)[0][:,:,:n]
            maximum=max(maximum,float(np.max(np.abs(expected-actual))))
    result=dict(designs=len(chosen),pytorch_float32_max_abs=maximum,phase4_tolerance=1e-6,passes=maximum<1e-6)
    atomic(OUT/'pytorch200.json',result);print(json.dumps(result),flush=True)
    assert len(chosen)==200 and result['passes'],result

if __name__=='__main__':run()
