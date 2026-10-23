"""Frozen labelled-pick evidence; no inferred acceptable labels."""
import sys,os,json,hashlib,csv,subprocess
from pathlib import Path
from PIL import Image
from typing import Any
from eval.gen_integration import setup,cases,REPO,MAIN,OUT as ROOT,atomic
PAGE=REPO/'eval/results/crello-diagnose/recall3'
OLDPAGE=MAIN/'eval/results/crello-diagnose/recall2'
OUT=ROOT/'path_budget'

def pixels(im: Any) -> str:
    return hashlib.sha256(str(im.size).encode()+im.convert('RGB').tobytes()).hexdigest()

def thumb(output: dict) -> Any:
    from eval.render import render_image
    im=render_image(output);im.thumbnail((520,300));return im

def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

def run() -> None:
    setup();os.environ['GEN_ON']='1';os.environ.pop('GEN_OFF',None);os.environ['GEN_K']='8'
    from eval.score import score
    from engine.analyze import analyze
    from engine.fit import Sizer,realize
    from engine.select import _passes,repair,_tier
    from engine.retrieve import retrieved
    from engine.preserve import preserve_plans
    # Compile exact pre-decision resize; later pool edits must not change labelled evidence.
    code=subprocess.check_output(['git','show','d3aedcc:engine/resize.py'],cwd=REPO,text=True);ns={'__name__':'_frozen_labelled_resize'};exec(compile(code,'d3aedcc:engine/resize.py','exec'),ns)
    page={r['case']:r for r in json.loads((PAGE/'cases.json').read_text())};old={r['case']:r for r in json.loads((OLDPAGE/'cases.json').read_text())}
    tags=json.loads((REPO/'eval/results/recall3_tags.json').read_text());lost=json.loads((OUT.parent/'diagnostic/test1_lost_rebuilds.json').read_text())['rows'];known={r['case']:r for r in lost}
    rows=[];termrows=[];details=[]
    for c in cases('recall'):
        name,sample,fmt,target,source=c
        if not page[name]['generator_won'] or tags[name].get('acceptable'):continue
        os.environ['CHAMELEON_ASSETS']=str(REPO.parent/'data/crello_chameleon/assets' if sample.startswith('crello_') else REPO/'brand_kit/assets')
        if name not in known:
            continue
        bad=ns['resize'](source,target)
        assert hashlib.sha256(json.dumps(bad,indent=2).encode()).hexdigest()==page[name]['wire_sha'],name
        bad_scores={str(contrast):score(source,target,bad,contrast=contrast) for contrast in [False,True]}
        good=None;path=None
        if name in known:
            info=known[name];path=info['identified_matches'][0];a=analyze(source,tight=path['analysis']=='tight');s=Sizer(a,target['width'],target['height'])
            pp=retrieved(a,s,target['width'],target['height'],limit=30) if path['recipe']=='retrieved' else preserve_plans(a,s,target['width'],target['height'])
            p=next(p for p in pp if p.knobs==path['knobs'])
            good=realize(a,p,target['width'],target['height'],focal=path['focal'],keep_on_panel=path['keep_on_panel'])
            if not _passes(source,target,good):good=repair(source,target,good)
            image=Image.open(OLDPAGE/old[name]['cands'][info['recall2_best']-1]['img']).convert('RGB')
            assert pixels(thumb(good))==pixels(image),(name,'acceptable comparator mismatch')
        good_scores={str(contrast):score(source,target,good,contrast=contrast) for contrast in [False,True]} if good else None
        row=dict(case=name,comparison_status='confirmed acceptable recall2 comparator; absent from labelled recall3 capped pool' if good else 'unknown: no labelled acceptable comparator',
          bad_geometry_score=bad_scores['False']['total'],bad_rendered_score=bad_scores['True']['total'],bad_safety_tier=tuple(bool(v) for v in _tier(source,target,bad)),
          acceptable_geometry_score=good_scores['False']['total'] if good else None,acceptable_rendered_score=good_scores['True']['total'] if good else None,
          acceptable_safety_tier=tuple(bool(v) for v in _tier(source,target,good)) if good else None,terms_favouring_bad='')
        for stage in ['False','True']:
            bs=bad_scores[stage];gs=good_scores[stage] if good else None;wsum=sum(b['weight'] for b in bs['breakdown'].values())
            for term,v in bs['breakdown'].items():
                gv=gs['breakdown'][term] if gs else None;delta=100*v['weight']*(gv['penalty']-v['penalty'])/wsum if gv else None
                termrows.append(dict(case=name,stage='rendered' if stage=='True' else 'geometry',term=term,weight=v['weight'],
                  bad_penalty=v['penalty'],acceptable_penalty=gv['penalty'] if gv else None,points_favouring_bad=delta,
                  favours_bad=delta>0 if delta is not None else None,bad_detail=v['detail'],acceptable_detail=gv['detail'] if gv else None))
        row['terms_favouring_bad']=','.join(r['term'] for r in termrows if r['case']==name and r['stage']=='rendered' and r['favours_bad'])
        rows.append(row);details.append(dict(summary=row,bad=bad_scores,acceptable=good_scores,acceptable_path=path))
        print(name,row['comparison_status'],flush=True)
    assert len(rows)==2 and all(r['acceptable_geometry_score'] is not None for r in rows)
    write_csv(OUT/'scorer_confirmed_cases.csv',rows);write_csv(OUT/'scorer_confirmed_terms.csv',termrows);atomic(OUT/'scorer_pairs.json',json.loads(json.dumps(dict(reference_commit='d3aedcc',cases=details),default=lambda x:x.item())))

if __name__=='__main__':run()
