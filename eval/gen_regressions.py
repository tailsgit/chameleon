"""Explain score regressions using the capped generator-OFF counterfactual."""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import json
import math
from eval.gen_integration import OUT,atomic,cases


def run(mode:str,name:str)->None:
    data=json.loads((OUT/(mode+'.json')).read_text())
    rows=data['rows'];source={c[0]:c for c in cases('dev')}
    reg=[];counts=Counter()
    for r in rows:
        if r['delta']>=-10:continue
        case=source[r['case']];a=case[4]['canvas'];b=case[3]
        ratio=(b['width']/b['height'])/(a['width']/a['height'])
        caps_sufficient=r['off_delta'] < -10
        effect=r['score']-r['off_score']
        if caps_sufficient:
            category='caps sufficient'
            if effect < -.01:category+='; generator worsens'
            elif effect > .01:category+='; generator improves'
        elif r['gen_won']:category='generator pick introduces regression'
        else:category='generator pool/guard interaction introduces regression'
        counts['caps_sufficient' if caps_sufficient else 'generator_introduced']+=1
        reg.append(dict(case=r['case'],rules_score=r['rules_score'],new_score=r['score'],off_score=r['off_score'],
                        delta=r['delta'],off_delta=r['off_delta'],generator_effect=effect,generator_won=r['gen_won'],
                        aspect_change_x=max(ratio,1/ratio),aspect_log2_abs=abs(math.log2(ratio)),
                        source_aspect=a['width']/a['height'],target_aspect=b['width']/b['height'],cause=category))
    reg.sort(key=lambda r:r['delta'])
    rescued=[r['case'] for r in rows if r['off_delta'] < -10 and r['delta'] >= -10]
    result=dict(mode=mode,count=len(reg),attribution=dict(counts),caps_off_regressions=sum(r['off_delta'] < -10 for r in rows),rescued=rescued,rows=reg)
    atomic(OUT/(name+'.json'),result)
    if reg:
        with (OUT/(name+'.csv')).open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(reg[0]));writer.writeheader();writer.writerows(reg)
    lines=[f'# {name}', '',
           f"{len(reg)} final regressions; capped-OFF has {result['caps_off_regressions']}. Caps alone already cross the threshold in {counts['caps_sufficient']}; generator effects introduce {counts['generator_introduced']}. Generator effects rescue {len(rescued)} capped-OFF regressions.",
           '', 'Aspect change is max(B/A, A/B). A generator winner includes its existing finish variant. Attribution is from the measured ON/OFF counterfactual, without changing the scorer.',
           '', '| Case ID | rules | New | Capped OFF | Change | Generator won | Aspect change | Cause |',
           '|---|---:|---:|---:|---:|---|---:|---|']
    for r in reg:
        lines.append(f"| {r['case']} | {r['rules_score']:.2f} | {r['new_score']:.2f} | {r['off_score']:.2f} | {r['delta']:+.2f} | {'yes' if r['generator_won'] else 'no'} | {r['aspect_change_x']:.3f}× | {r['cause']} |")
    (OUT/(name+'.md')).write_text('\n'.join(lines)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='rows'}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--mode',required=True);p.add_argument('--name',required=True);a=p.parse_args();run(a.mode,a.name)
