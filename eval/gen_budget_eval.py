"""Count-budget calibration, historical clock replay and deterministic evaluation."""
from __future__ import annotations
import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from contextlib import ExitStack,contextmanager
import hashlib
import csv
import io
from functools import lru_cache
import importlib
import json
import logging
import math
import os
from pathlib import Path
import subprocess
import sys
import time
from unittest.mock import patch
import numpy as np
from eval.gen_integration import OUT,REPO,MAIN,atomic,canonical,setup,cases,bucket,diagnostics,legacy


@contextmanager
def operations():
    import engine.recipes as recipes
    import engine.resize as R
    import engine.gen_candidates as gen
    values={}
    def wrap(key,fn):
        def timed(*args,**kwargs):
            t=time.process_time()
            try:return fn(*args,**kwargs)
            finally:values.setdefault(key,[]).append(time.process_time()-t)
        return timed
    specs=[(R,'analyze','analyze'),(R,'generate','generate'),(R,'realize','realize'),
           (R,'select','select'),(R,'variants','finish'),(R,'better_variant','finish_select'),
           (recipes,'stack','recipe.stack'),(recipes,'split','recipe.split'),
           (recipes,'strip','recipe.strip'),(recipes,'anchor','recipe.anchor'),
           (recipes,'preserve_plans','preserve_four'),(recipes,'retrieved','retrieval_batch'),
           (gen,'predict','generator_infer'),(gen,'fit_sample','generator_fit'),(gen,'candidates','generator_total')]
    with ExitStack() as stack:
        for obj,name,key in specs:stack.enter_context(patch.object(obj,name,wrap(key,getattr(obj,name))))
        yield values


def snapshot()->str:
    names=['engine/resize.py','engine/recipes.py','engine/retrieve.py','engine/gen_candidates.py','engine/search.py','engine/select.py']
    h=hashlib.sha256()
    for name in names:h.update(name.encode());h.update((REPO/name).read_bytes())
    return h.hexdigest()


def historical_clock(source:dict,target:dict)->dict:
    """Compare original flag-off adapter at 713838d before the deliberate cap change."""
    code=subprocess.check_output(['git','show','713838d:engine/resize.py'],cwd=REPO,text=True)
    namespace={'__name__':'_historical_flag_off'};exec(compile(code,'historical-flag-off','exec'),namespace)
    reference=legacy();modules=[importlib.import_module(n) for n in ['engine.recipes','engine.select','engine.retrieve','engine.preserve','engine.search']]
    ticks=[]
    def record():
        t=time.process_time();ticks.append(t);return t
    os.environ['GEN_OFF']='1'
    with ExitStack() as stack:
        stack.enter_context(patch.dict(reference.__globals__,now=record))
        for m in modules:stack.enter_context(patch.object(m,'now',record))
        first=reference(source,target)
    cursor=0
    def replay():
        nonlocal cursor
        value=ticks[cursor];cursor+=1;return value
    with ExitStack() as stack:
        stack.enter_context(patch.dict(namespace,now=replay))
        for m in modules:stack.enter_context(patch.object(m,'now',replay))
        second=namespace['resize'](source,target)
    return dict(identical=json.dumps(first,indent=2)==json.dumps(second,indent=2),clock_calls_reference=len(ticks),clock_calls_adapter=cursor)


@lru_cache(maxsize=1)
def committed_scores() -> dict:
    text=subprocess.check_output(['git','show','rules:eval/results/crello-dev/cases.csv'],cwd=REPO,text=True)
    return {r['case']:r for r in csv.DictReader(io.StringIO(text))}


def one(job:tuple)->dict:
    setup();mode,index,case,k,version=job
    name,sample,fmt,target,source=case
    os.environ['CHAMELEON_ASSETS']=str(REPO.parent/'data/crello_chameleon/assets' if sample.startswith('crello_') else REPO/'brand_kit/assets')
    dest=OUT/mode/f'{index:04d}.json'
    if dest.exists():
        data=json.loads(dest.read_text());assert data['code']==version,'immutable result belongs to different code; use a new mode'
        return data
    if mode.startswith('clock'):
        row=dict(case=name,code=version,**historical_clock(source,target));atomic(dest,row);return row
    from engine.resize import resize
    from engine import gen_candidates as gen
    from engine.select import _passes, repair
    from eval.score import score
    from eval.check import check
    os.environ.pop('GEN_OFF',None);os.environ['GEN_K']=str(k)
    # All measurements include full resize; diagnostics and reference run are outside.
    R=importlib.import_module('engine.resize');base=[]
    with operations() as measured:
        real=R.realize
        def capture(*args,**kwargs):
            out=real(*args,**kwargs);base.append(out);return out
        with patch.object(R,'realize',capture):
            t=time.process_time();w=time.perf_counter();output=resize(source,target)
            cpu=time.process_time()-t;wall=time.perf_counter()-w
    generated=list(gen.LAST.get('outputs',[]));stats={key:v for key,v in gen.LAST.items() if key!='outputs'}
    row=dict(case=name,sample=sample,code=version,k=k,bucket=bucket(source,target),cpu_s=cpu,wall_s=wall,
             sha=hashlib.sha256(canonical(output).encode()).hexdigest(),wire_sha=hashlib.sha256(json.dumps(output,indent=2).encode()).hexdigest(),passed=not check(source,target,output),
             score=score(source,target,output)['total'],generator=stats,operations=measured,
             gen_won=bool(stats.get('won_selection',False)),candidate_pass=any(_passes(source,target,o) for o in generated),
             best_generator_score=max((score(source,target,o)['total'] for o in generated if _passes(source,target,o)),default=None))
    fixed_pool=[o if _passes(source,target,o) else repair(source,target,o) for o in base+generated]
    ranked=sorted([(score(source,target,o)['total'],i,o) for i,o in enumerate(fixed_pool) if _passes(source,target,o)],key=lambda t:(-t[0],t[1]))
    unique=[]
    for value,_,o in ranked:
        if all(gen.layout_distance(o,q)>=.08 for q in unique):unique.append(o)
    row['pool_distinct']=len(unique)
    row['best_pool_score']=ranked[0][0] if ranked else None
    if mode.startswith('eval'):
        # Original rules semantics (uncapped generation defaults) remain accessible
        # only to this evaluation; GEN_OFF production now means capped/no generator.
        baseline=committed_scores().get(name)
        if baseline is not None:
            row['rules_score']=float(baseline['total'])
            row['rules_reference']='rules:eval/results/crello-dev/cases.csv'
        else:
            old=legacy()(source,target)
            row['rules_score']=score(source,target,old)['total']
            row['rules_reference']='fresh rules run (recall case absent from dev CSV)'
        row['delta']=row['score']-row['rules_score']
        os.environ['GEN_OFF']='1'
        t=time.process_time();capped=resize(source,target);row['off_cpu_s']=time.process_time()-t
        row['off_score']=score(source,target,capped)['total'];row['off_delta']=row['off_score']-row['rules_score']
        row['all16']=diagnostics(source,target)
        row['final_rules']=dict(Counter(v['rule'] for v in check(source,target,output)))
    atomic(dest,row);return row


def summary(rows:list)->dict:
    out=dict(cases=len(rows))
    if rows and 'identical' in rows[0]:
        out['identical']=sum(r['identical'] for r in rows);return out
    for key in ['cpu_s','wall_s','score','delta','off_delta','pool_distinct']:
        if key not in rows[0]:continue
        a=np.array([r[key] for r in rows]);out[key]=dict(mean=float(a.mean()),p50=float(np.median(a)),p95=float(np.quantile(a,.95)),max=float(a.max()))
    out.update(generator_pass_cases=sum(r['candidate_pass'] for r in rows),generator_wins=sum(r['gen_won'] for r in rows),
               unique_cases=sum(r['generator'].get('new_unique',0)>0 for r in rows),final_pass=sum(r['passed'] for r in rows))
    if 'delta' in rows[0]:
        out['regressions']=[dict(case=r['case'],delta=r['delta'],off_delta=r['off_delta']) for r in rows if r['delta'] < -10]
        out['off_regressions']=[dict(case=r['case'],delta=r['off_delta']) for r in rows if r['off_delta'] < -10]
        out['all16']={}
        for b in ['<0.1','0.1-0.5','0.5-1','>1']:
            rr=[r for r in rows if r['bucket']==b];fail=Counter()
            for r in rr:fail.update(r['all16']['failed_sample_rules'])
            total=sum(r['all16']['samples'] for r in rr);passing=sum(r['all16']['passing'] for r in rr)
            out['all16'][b]=dict(cases=len(rr),samples=total,passing=passing,rate=passing/total if total else None,failures=dict(fail))
    ops={}
    for r in rows:
        for key,vals in r['operations'].items():ops.setdefault(key,[]).extend(vals)
    out['operations']={key:dict(n=len(v),mean=float(np.mean(v)),p50=float(np.median(v)),p95=float(np.quantile(v,.95)),max=float(max(v))) for key,v in ops.items()}
    return out


def burn()->None:
    # One CPU-bound process; four workers plus four burns constitute 2x load.
    x=1
    while True:x=(x*1664525+1013904223)%4294967296


def main()->None:
    p=argparse.ArgumentParser();p.add_argument('mode');p.add_argument('--suite',choices=['dev','recall'],default='dev')
    p.add_argument('--n',type=int,default=0);p.add_argument('--k',type=int,default=6);p.add_argument('--jobs',type=int,default=4);p.add_argument('--load',action='store_true')
    a=p.parse_args();setup();chosen=cases(a.suite)[:a.n or None];version=snapshot();work=[(a.mode,i,c,a.k,version) for i,c in enumerate(chosen)]
    burns=[]
    if a.load:
        import multiprocessing
        for _ in range(a.jobs):
            process=multiprocessing.Process(target=burn);process.start();burns.append(process)
    rows=[];start=time.monotonic()
    try:
        with ProcessPoolExecutor(a.jobs) as pool:
            for r in pool.map(one,work,chunksize=1):
                rows.append(r)
                print(f'{a.mode} {len(rows)}/{len(work)} cpu={r.get("cpu_s",0):.3f} {r["case"]}',flush=True)
    finally:
        for process in burns:process.terminate();process.join()
    result=summary(rows);result['elapsed_s']=time.monotonic()-start
    atomic(OUT/(a.mode+'.json'),dict(summary=result,rows=rows))
    print(json.dumps(result),flush=True)
    if a.mode.startswith('clock'):assert result['identical']==len(work),result

if __name__=='__main__':main()
