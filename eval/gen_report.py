"""Assemble external Phase 4 CSVs/report from immutable per-case measurements."""
from __future__ import annotations
import csv
import json
from pathlib import Path
import numpy as np
from eval.gen_integration import OUT,REPO,atomic


def read(name:str)->dict:
    return json.loads((OUT/(name+'.json')).read_text())


def run()->None:
    dev=read('eval_dev_v2');recall=read('eval_recall6_v2')
    variants=[read('recall4_v2'),recall,read('recall8_v2')]
    primary={r['case']:r['wire_sha'] for r in recall['rows']}
    determinant={}
    for name in ['repeat6_v2','load6_v2']:
        other={r['case']:r['wire_sha'] for r in read(name)['rows']}
        assert set(primary)==set(other) and len(other)==40
        determinant[name]=[case for case in primary if primary[case]!=other[case]]
    historical=json.loads((OUT/'historical_regressions.json').read_text())
    old={r['case'] for r in historical}
    rows=dev['rows'];regressions=[r for r in rows if r['delta'] < -10]
    overlap=[r['case'] for r in regressions if r['case'] in old]
    result=dict(dev=dev['summary'],recall=recall['summary'],
                determinism=determinant,clock=read('clock50_bytes')['summary'],
                legacy_ordinary_clock_mismatches=read('off')['summary']['mismatches'],
                historical_regressions=len(historical),new_regressions=len(regressions),overlap=overlap)
    fields=['case','sample','bucket','k','score','rules_score','delta','off_score','off_delta',
            'passed','candidate_pass','gen_won','pool_distinct','best_pool_score','cpu_s','wall_s','wire_sha']
    with (OUT/'cases.csv').open('w',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=fields+['gen_passing_of_16','gen_samples','generator_unique']);writer.writeheader()
        for r in rows:
            line={key:r[key] for key in fields}
            line.update(gen_passing_of_16=r['all16']['passing'],gen_samples=r['all16']['samples'],generator_unique=r['generator']['new_unique'])
            writer.writerow(line)
    with (OUT/'regressions.csv').open('w',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=['case','rules_score','score','delta','off_delta','historical_rules_regression']);writer.writeheader()
        for r in regressions:writer.writerow({**{k:r[k] for k in ['case','rules_score','score','delta','off_delta']},'historical_rules_regression':r['case'] in old})
    lines=['# Phase 4 measured report','',
           'Integration only in `chameleon-int` / `gen-integration`. No scorer/weight changes, CP-SAT projection, downloads, Docker runs or merges.',
           '', '## Caps and timing','',
           'Per case: 4 recipe attempts on the tight analysis (family round-robin), 4 retrieval plans shared across analyses, existing 4 preserve variants per analysis unchanged, 16 base realizations plus at most K generator realizations, and 3 contrast renders. Solver parameters unchanged.',
           '', '| Cases | K | CPU p50 | CPU p95 | CPU max | Wall p50 | Wall max |',
           '|---|---:|---:|---:|---:|---:|---:|']
    for name,k,data in [('600 dev',6,dev),('40 recall',4,variants[0]),('40 recall',6,recall),('40 recall',8,variants[2])]:
        t=data['summary'];cpu=t['cpu_s'];wall=t['wall_s']
        lines.append(f"| {name} | {k} | {cpu['p50']:.3f} | {cpu['p95']:.3f} | {cpu['max']:.3f} | {wall['p50']:.3f} | {wall['max']:.3f} |")
    s=dev['summary'];r=recall['summary']
    lines += ['', '## Quality against committed rules CSV','',
              f"600 dev: mean hand-score change {s['delta']['mean']:+.3f}; {len(regressions)} regressions (>10-point drops). Capped generator-OFF: mean change {s['off_delta']['mean']:+.3f}; {len(s['off_regressions'])} regressions. Reference is the committed rules CSV, same geometric hand scorer.",
              f"Historical rules-vs-v5: 46 regressions. {len(overlap)} of the new regressions overlap that list; {len(regressions)-len(overlap)} are outside it. See historical_regressions.md, regressions.csv and cases.csv for every case ID.",
              f"Dev final hard-rule passes {s['final_pass']}/600; generator contributes a passing candidate {s['generator_pass_cases']}/600 and wins selection {s['generator_wins']}/600. Recall equivalents: {r['final_pass']}/40, {r['generator_pass_cases']}/40, {r['generator_wins']}/40.",
              '', '## K effect on candidate coverage (40 recall cases)','',
              'These are candidate-coverage/hand-score proxies; human acceptable-layout recall awaits recall3 labeling.',
              '', '| K | Cases with passing generator | Cases with unique generator contribution | Generator wins | Mean distinct passing layouts | Mean final hand score |',
              '|---:|---:|---:|---:|---:|---:|']
    for k,data in zip([4,6,8],variants):
        q=data['summary'];lines.append(f"| {k} | {q['generator_pass_cases']}/40 | {q['unique_cases']}/40 | {q['generator_wins']}/40 | {q['pool_distinct']['mean']:.2f} | {q['score']['mean']:.2f} |")
    lines += ['', '## All 16 samples after local repair','',
              'Denominator includes samples rejected by prefilter/dedup. These diagnostic fits run outside measured production-case time.',
              '', '| Suite | Absolute log2 aspect-change bucket | Passing / samples | Pass rate | Remaining hard-rule failures (sample counts) |',
              '|---|---|---:|---:|---|']
    low=[]
    for name,data in [('600 dev',dev),('40 recall',recall)]:
        for b,q in data['summary']['all16'].items():
            rate='—' if q['rate'] is None else f"{100*q['rate']:.2f}%"
            failures=', '.join(f'{key}: {value}' for key,value in sorted(q['failures'].items(),key=lambda t:-t[1])) or 'none'
            lines.append(f"| {name} | {b} | {q['passing']}/{q['samples']} | {rate} | {failures} |")
            if b in ['0.5-1','>1'] and q['rate'] is not None and q['rate']<.5:low.append((name,b,q['rate']))
    lines += ['', f"Big-change buckets below 50%: {low if low else 'none'}. No CP-SAT projection was added.",
              '', '## Determinism','',
              f"40 identical cases: repeated-run mismatches {len(determinant['repeat6_v2'])}; 2x-load mismatches {len(determinant['load6_v2'])}. Hashes cover the exact JSON bytes emitted by engine/main.py, including key order. Load is four evaluation workers plus four CPU-burn workers.",
              'Historical flag-off adapter: 50/50 byte-identical with recorded clock replay. Two ordinary-clock mismatches remain documented as legacy timing sensitivity. Current GEN_OFF intentionally uses count caps and is compared by score instead.',
              '', '## New regressions','', '| Case ID | rules | Integration | Change | Caps-only change | Historical regression |',
              '|---|---:|---:|---:|---:|---|']
    for q in regressions:lines.append(f"| {q['case']} | {q['rules_score']:.2f} | {q['score']:.2f} | {q['delta']:+.2f} | {q['off_delta']:+.2f} | {'yes' if q['case'] in old else 'no'} |")
    lines += ['', '## Calibration evidence','',
              'calibrate_v1.json contains the original 600-case per-operation timings. eval_dev_v2.json contains measurements under the final caps. Selection render count changed from the old maximum of 10 to 3; the hand-score formula and weights did not change.',
              '', 'Recall3: `chameleon-int/eval/results/crello-diagnose/recall3/index.html`; same 40 cases/order as recall2, with a unique-generator marker.']
    (OUT/'report.md').write_text('\n'.join(lines)+'\n');atomic(OUT/'report.json',result)
    assert all(not v for v in determinant.values()),determinant
    assert s['cpu_s']['max']<=10,s['cpu_s']
    assert r['cpu_s']['max']<=10,r['cpu_s']
    print('PASS final gates',json.dumps(dict(max_cpu=s['cpu_s']['max'],regressions=len(regressions),determinism=determinant)),flush=True)

if __name__=='__main__':
    from eval.gen_integration import atomic
    run()
