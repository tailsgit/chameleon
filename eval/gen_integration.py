"""Focused, resumable Phase 4 checks; artifacts remain outside git."""
from __future__ import annotations
import argparse
import collections
import hashlib
import importlib.util
import json
import logging
import math
import os
from pathlib import Path
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor
import numpy as np

REPO=Path(__file__).resolve().parents[1]
MAIN=REPO.parent/'chameleon'
OUT=REPO.parent/'data/generator/integration'
BUCKETS=['<0.1','0.1-0.5','0.5-1','>1']


def atomic(path:Path,data:object)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix('.partial');tmp.write_text(json.dumps(data,indent=1));tmp.replace(path)


def canonical(out:dict)->str:
    return json.dumps(out,sort_keys=True,separators=(',',':'))


def setup()->None:
    os.environ['CHAMELEON_CPU_CLOCK']='1'
    os.environ['CHAMELEON_ASSETS']=str(REPO.parent/'data/crello_chameleon/assets')
    logging.disable(logging.WARNING)
    random.seed(2026);np.random.seed(2026)


def bucket(source:dict,target:dict)->str:
    a=source['canvas'];d=abs(math.log2((target['width']/target['height'])/(a['width']/a['height'])))
    return BUCKETS[next((i for i,e in enumerate([.1,.5,1]) if d<e),3)]


def cases(which:str)->list:
    from eval.bench import load_suite
    from eval.diagnose_pages import _source
    if which=='dev':return load_suite('crello-dev')[0]
    raw=json.loads((MAIN/'eval/results/crello-diagnose/recall2/cases.json').read_text())
    result=[]
    for r in raw:
        w,h=map(int,r['target'].split('×'))
        result.append((r['case'],r['sample'],'recall',{'width':w,'height':h},_source(r['sample'])))
    return result


def legacy():
    spec=importlib.util.spec_from_file_location('_reference_rules_resize',MAIN/'engine/resize.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod.resize


def diagnostics(source:dict,target:dict)->dict:
    """All 16, including prefiltered samples; not included in case timing."""
    from engine.analyze import analyze
    from engine.gen_candidates import predict,project,fit_sample
    from eval.check import check
    a=analyze(source);g,raw=predict(a,target)
    failed=collections.Counter();passed=0
    for i,b in enumerate(raw):
        p=project(g,b,target['width'],target['height'])
        out=fit_sample(a,target,g,p,i)
        errors=check(source,target,out)
        passed+=not errors
        failed.update(set(e['rule'] for e in errors))
    return dict(samples=16,passing=passed,failed_sample_rules=dict(failed))


class Capture(logging.Handler):
    def __init__(self):super().__init__();self.messages=[]
    def emit(self,record):self.messages.append(record.getMessage())


def one(job:tuple)->dict:
    setup()
    mode,index,case,k=job
    name,sample,fmt,target,source=case
    os.environ["CHAMELEON_ASSETS"]=str(REPO.parent/"data/crello_chameleon/assets" if sample.startswith("crello_") else REPO/"brand_kit/assets")
    path=OUT/mode/f'{index:04d}.json'
    if path.exists():return json.loads(path.read_text())
    from engine.resize import resize
    from engine import gen_candidates as gen
    from eval.score import score
    from eval.check import check
    if mode=='off':
        os.environ['GEN_OFF']='1'
        left=legacy()(source,target);right=resize(source,target)
        result=dict(case=name,identical=canonical(left)==canonical(right),
                    reference_sha=hashlib.sha256(canonical(left).encode()).hexdigest(),
                    off_sha=hashlib.sha256(canonical(right).encode()).hexdigest())
    else:
        os.environ.pop('GEN_OFF',None);os.environ['GEN_K']=str(k)
        t=time.process_time();w=time.perf_counter()
        output=resize(source,target)
        cpu=time.process_time()-t;wall=time.perf_counter()-w
        stats={key:val for key,val in gen.LAST.items() if key!='outputs'}
        generated=gen.LAST.get('outputs',[])
        result=dict(case=name,sample=sample,bucket=bucket(source,target),k=k,cpu_s=cpu,wall_s=wall,
                    sha=hashlib.sha256(canonical(output).encode()).hexdigest(),
                    passed=not check(source,target,output),score=score(source,target,output)['total'],
                    generator=stats,gen_won=bool(stats.get('won_selection',False)))
        if mode.startswith('eval_'):
            # Run legacy only after recording enabled timing; keep labels untouched.
            t=time.process_time();old=legacy()(source,target)
            result['rules_cpu_s']=time.process_time()-t
            result['rules_score']=score(source,target,old)['total']
            result['delta']=result['score']-result['rules_score']
            result['all16']=diagnostics(source,target)
    atomic(path,result)
    return result


def run_cases(mode:str,which:str,n:int,jobs:int,k:int)->None:
    setup();OUT.mkdir(parents=True,exist_ok=True)
    chosen=cases(which)[:n or None]
    todo=[(mode,i,c,k) for i,c in enumerate(chosen)]
    start=time.monotonic();rows=[]
    with ProcessPoolExecutor(jobs) as pool:
        for row in pool.map(one,todo,chunksize=1):
            rows.append(row)
            print(f'{mode} {len(rows)}/{len(todo)} {row["case"]} cpu={row.get("cpu_s",0):.3f}',flush=True)
    summary=dict(cases=len(rows),elapsed_s=time.monotonic()-start)
    if mode=='off':summary['mismatches']=[r for r in rows if not r['identical']]
    else:
        summary.update(cpu_median=float(np.median([r['cpu_s'] for r in rows])),cpu_max=max(r['cpu_s'] for r in rows),
                       wall_median=float(np.median([r['wall_s'] for r in rows])),wall_max=max(r['wall_s'] for r in rows))
    atomic(OUT/(mode+'.json'),dict(summary=summary,rows=rows))
    print(json.dumps(summary),flush=True)
    if mode=='off':assert not summary['mismatches'],summary['mismatches']


def parity()->None:
    setup()
    import onnxruntime as ort
    from generator.pair_data import cached_rows,raw_rows
    from generator.extract import memory_assets
    from generator.features import continuous,canvases,KINDS,ROLES
    from eval.crello_convert import convert
    from engine.analyze import analyze
    from engine.gen_candidates import features,predict,runtime
    picked=[r for r in cached_rows() if r['split']=='val'][:200]
    by_shard=collections.defaultdict(dict)
    for r in picked:by_shard[r['raw_shard']][r['raw_row']]=r
    other=ort.SessionOptions();other.intra_op_num_threads=other.inter_op_num_threads=1
    other.execution_mode=ort.ExecutionMode.ORT_SEQUENTIAL
    reference=ort.InferenceSession(str(REPO/'engine/data/generator.onnx'),other,providers=['CPUExecutionProvider'])
    done=0;maximum=0.
    for shard,wanted in sorted(by_shard.items()):
        for index,row,fonts,formats in raw_rows(shard):
            if index not in wanted:
                if index>max(wanted):break
                continue
            cached=wanted[index];source,_,images=convert(row,fonts,formats)
            try:
                target={'width':1080,'height':1920} if done%2 else {'width':1920,'height':1080}
                with memory_assets(images):
                    a=analyze(source)
                    groups,engine_out=predict(a,target)
                    assert groups==cached['groups'],f'group extraction differs at {shard}:{index}'
                    actual=features(groups,source['canvas'],target)
                    g=len(groups)
                    expected={key:np.zeros_like(v) for key,v in actual.items()}
                    expected['cont'][0,:g]=[continuous(v) for v in cached['groups']]
                    expected['cat'][0,:g]=[[KINDS.index(v['kind']),ROLES.index(v['role'])] for v in cached['groups']]
                    expected['valid'][0,:g]=1;expected['source'][:]=3
                    expected['canvas'][0]=canvases({'canvas_a':cached['canvas'],'canvas_b':[target['width'],target['height']]})
                    for key in actual:np.testing.assert_array_equal(actual[key],expected[key])
                    wanted_out=reference.run(['boxes'],expected)[0][0,:,:g]
                    maximum=max(maximum,float(np.max(np.abs(wanted_out-engine_out))))
                    assert maximum<=1e-6,maximum
                    np.testing.assert_array_equal(engine_out,runtime()[0].run(['boxes'],actual)[0][0,:,:g])
                done+=1
                if done%10==0:print(f'parity {done}/200 max_abs={maximum}',flush=True)
            finally:
                for im in images.values():im.close()
    assert done==200,done
    atomic(OUT/'parity.json',dict(designs=done,feature_exact=True,output_max_abs=maximum,repeated_identical=True))
    print('PASS parity',done,maximum,flush=True)


def main()->None:
    p=argparse.ArgumentParser();p.add_argument('mode');p.add_argument('--suite',default='recall',choices=['recall','dev'])
    p.add_argument('--n',type=int,default=0);p.add_argument('--jobs',type=int,default=4);p.add_argument('--k',type=int,default=6)
    a=p.parse_args()
    if a.mode=='parity':parity()
    else:run_cases(a.mode,a.suite,a.n,a.jobs,a.k)

if __name__=='__main__':main()
