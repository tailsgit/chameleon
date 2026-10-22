"""Numeric-only explanation of remaining generator visibility failures."""
from __future__ import annotations
import argparse
import json
from engine.analyze import analyze
from engine.gen_candidates import predict,project,fit_sample
from eval.check import check,_is_hidden
from eval.gen_integration import OUT,atomic,cases,setup


def run(mode:str)->None:
    setup();rows=json.loads((OUT/(mode+'.json')).read_text())['rows']
    sources={c[0]:c for c in cases('dev')};evidence=[]
    for row in rows:
        if row['all16']['passing']==16:continue
        case=sources[row['case']];target,source=case[3:];a=analyze(source);groups,raw=predict(a,target)
        out=fit_sample(a,target,groups,project(groups,raw[0],target['width'],target['height']),0)
        for error in check(source,target,out):
            eid=error['id'];unit=next((u for u in [*a.units.values(),*a.decorations] if eid in u.members),None)
            src=a.els[eid]
            item=dict(case=row['case'],target=target,error=error,source_size=[src['width'],src['height']])
            if unit:
                visible=[a.els[m] for m in unit.members if not _is_hidden(a.els[m])]
                minimum=max((max(1/e['width'],1/e['height']) for e in visible),default=0.)
                maximum=min(target['width']/unit.w,target['height']/unit.h)
                item.update(unit_size=[unit.w,unit.h],members=len(unit.members),parts=len(unit.parts),
                            minimum_scale_for_1px=minimum,maximum_canvas_fit_scale=maximum,
                            required_unit_size=[unit.w*minimum,unit.h*minimum],
                            visibility_floor_fits_source_arrangement=minimum<=maximum)
            evidence.append(item)
    atomic(OUT/'remaining_hidden_v3.json',evidence)
    print(json.dumps(evidence,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--mode',default='eval_dev8_v3');a=p.parse_args();run(a.mode)
