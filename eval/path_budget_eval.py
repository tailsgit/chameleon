"""Default-off budget evaluation; exact old accepted PNGs are evaluation only."""
from __future__ import annotations
import argparse, copy, hashlib, json, multiprocessing, os, time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from unittest.mock import patch
import numpy as np
from typing import Any
from eval.gen_integration import REPO,MAIN,OUT,setup,cases,atomic,canonical
from eval.gen_budget_eval import burn,committed_scores,snapshot

DEST=OUT/'path_budget'


def photo_hash(im: Any) -> str:
    return hashlib.sha256(str(im.size).encode()+im.convert('RGB').tobytes()).hexdigest()


def accepted_recovery(case: str, source: dict, target: dict, records: list, guarded: list, win: dict) -> dict | None:
    old=json.loads((OUT/'diagnostic/test1_lost_rebuilds.json').read_text())['rows']
    record=next((r for r in old if r['case']==case),None)
    if record is None:return None
    from PIL import Image
    from eval.render import render_image
    from engine.select import _passes,repair
    from eval.score import score
    from eval.diagnose_pages import _dist
    oldpage=MAIN/'eval/results/crello-diagnose/recall2'
    page=next(r for r in json.loads((oldpage/'cases.json').read_text()) if r['case']==case)
    desired=Image.open(oldpage/page['cands'][record['recall2_best']-1]['img']).convert('RGB')
    def thumbnail(out):
        im=render_image(out);im.thumbnail((520,300));return im
    matches=[]
    for output,meta in records:
        relevant=any(all(meta.get(k)==m.get(k) for k in ['recipe','knobs','analysis','focal','keep_on_panel']) for m in record['identified_matches'])
        if not relevant:continue
        fixed=output if _passes(source,target,output) else repair(source,target,output)
        if photo_hash(thumbnail(fixed))==photo_hash(desired):
            matches.append(dict(path=meta,hard_rules_pass=_passes(source,target,fixed),after_guard=any(output is q for q in guarded)))
    fixed=[o if _passes(source,target,o) else repair(source,target,o) for o,_ in records]
    shown=[win]
    for value,i in sorted([(score(source,target,o)['total'],i) for i,o in enumerate(fixed)],key=lambda t:-t[0]):
        if len(shown)>=8:break
        if all(_dist(fixed[i],o)>=.08 for o in shown):shown.append(fixed[i])
    visible=[i+1 for i,o in enumerate(shown) if photo_hash(thumbnail(o))==photo_hash(desired)]
    return dict(exact_accepted_matches=matches,restored=bool(matches),after_guard=any(m['after_guard'] for m in matches),visible_candidates=visible,
                final_pick_accepted_pixels=photo_hash(thumbnail(win))==photo_hash(desired))


def one(job: tuple) -> dict:
    mode,index,case,version=job;setup();os.environ.pop('GEN_ON',None);os.environ['GEN_OFF']='1'
    name,sample,fmt,target,source=case
    os.environ['CHAMELEON_ASSETS']=str(REPO.parent/'data/crello_chameleon/assets' if sample.startswith('crello_') else REPO/'brand_kit/assets')
    file=DEST/mode/f'{index:04d}.json'
    if file.exists():
        data=json.loads(file.read_text());assert data['version']==version,'use a fresh mode for changed code';return data
    import engine.resize as R
    from engine.candidate_budget import LAST
    from eval.score import score
    from eval.check import check
    records=[];analyses=[];guarded=[]
    original_analyze,original_realize,original_select=R.analyze,R.realize,R.select
    def analyze(*a,**kw):
        result=original_analyze(*a,**kw);analyses.append(result);return result
    def realize(a,p,*args,**kw):
        out=original_realize(a,p,*args,**kw)
        records.append((out,dict(recipe=p.recipe,knobs=p.knobs,analysis='tight' if a is analyses[0] else 'plain',
            focal=kw.get('focal',True),keep_on_panel=kw.get('keep_on_panel',True))))
        return out
    def select(source,target,outputs,*a,**kw):
        guarded.extend(outputs);return original_select(source,target,outputs,*a,**kw)
    with patch.object(R,'analyze',analyze),patch.object(R,'realize',realize),patch.object(R,'select',select):
        t=time.process_time();w=time.perf_counter();output=R.resize(source,target);cpu=time.process_time()-t;wall=time.perf_counter()-w
    assert len(records)==LAST['total'],(name,len(records),LAST)
    baseline=committed_scores().get(name)
    row=dict(case=name,sample=sample,version=version,cpu_s=cpu,wall_s=wall,score=score(source,target,output)['total'],
         rules_score=float(baseline['total']) if baseline else None,
         wire_sha=hashlib.sha256(json.dumps(output,indent=2).encode()).hexdigest(),
         pool_sha=hashlib.sha256(json.dumps(sorted(canonical(o) for o,_ in records)).encode()).hexdigest(),
         passed=not check(source,target,output),budget=copy.deepcopy(LAST),families=dict(Counter(m['recipe'] for _,m in records)),
         onnxruntime_imported='onnxruntime' in __import__('sys').modules)
    row['delta']=row['score']-row['rules_score'] if baseline else None
    if not mode.startswith('dev'):
        row['accepted_recovery']=accepted_recovery(name,source,target,records,guarded,output)
    row=json.loads(json.dumps(row,default=lambda x:x.item()));atomic(file,row)
    return row


def main() -> None:
    p=argparse.ArgumentParser();p.add_argument('mode');p.add_argument('--suite',choices=['recall','dev'],default='dev')
    p.add_argument('--jobs',type=int,default=4);p.add_argument('--top',type=int,default=0);p.add_argument('--load',action='store_true');p.add_argument('--n',type=int,default=0)
    a=p.parse_args();setup();cc=cases(a.suite)
    if a.top:
        prior=json.loads((OUT/'eval_dev8_v3.json').read_text())['rows'];order=[r['case'] for r in sorted(prior,key=lambda r:r['cpu_s'],reverse=True)[:a.top]]
        by={c[0]:c for c in cc};cc=[by[name] for name in order]
    cc=cc[:a.n or None]
    version=hashlib.sha256((snapshot()+Path(__file__).read_text()+json.dumps(dict(load=a.load,jobs=a.jobs))).encode()).hexdigest()
    jobs=[(a.mode,i,c,version) for i,c in enumerate(cc)];burns=[];rows=[];start=time.monotonic()
    if a.load:
        for _ in range(a.jobs):
            process=multiprocessing.Process(target=burn);process.start();burns.append(process)
    try:
        with ProcessPoolExecutor(a.jobs) as pool:
            for r in pool.map(one,jobs,chunksize=1):
                rows.append(r);print(f'{a.mode} {len(rows)}/{len(cc)} cpu={r["cpu_s"]:.3f} {r["case"]}',flush=True)
    finally:
        for b in burns:b.terminate();b.join()
    summary=dict(cases=len(rows),elapsed_s=time.monotonic()-start)
    for key in ['cpu_s','wall_s','score','delta']:
        values=[r[key] for r in rows if r[key] is not None]
        if values:summary[key]=dict(mean=float(np.mean(values)),p50=float(np.median(values)),p95=float(np.quantile(values,.95)),max=float(max(values)))
    summary['regressions']=[dict(case=r['case'],rules_score=r['rules_score'],new_score=r['score'],delta=r['delta']) for r in rows if r['delta'] is not None and r['delta'] < -10]
    summary['final_pass']=sum(r['passed'] for r in rows);summary['onnxruntime_imported']=any(r['onnxruntime_imported'] for r in rows)
    atomic(DEST/f'{a.mode}.json',dict(summary=summary,rows=rows));print(json.dumps(summary),flush=True)

if __name__=='__main__':main()
