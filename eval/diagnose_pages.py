"""Build the diagnosis pages served by eval.tag_server (renders and HTML in eval/results/crello-diagnose/, gitignored).

    python -m eval.diagnose_pages failures          # labelled bad although the hand scorer gives >= BAND
    python -m eval.diagnose_pages recall --jobs 4   # RECALL_N labelled cases: the engine's top distinct candidates
    python -m eval.diagnose_pages recall2 --jobs 4  # the same cases re-run by the current engine (own page and tags)
    python -m eval.diagnose_pages rerun --jobs 4    # the non-"fine" failures: labelled output next to today's pick
    python -m eval.tag_server --port 8780           # then open the pages

failures: every labelled output (eval.critic_cv rows) with hand score >= BAND and label bad: source, output, target
  size, hand score, a primary-failure dropdown (FAILURES) and a note -> eval/results/failure_tags.json.
recall: RECALL_N cases (design + target) from labelled designs, seeded: half with an aspect change of at least
  EXTREME (ratio), half moderate (MODERATE <= ratio < EXTREME), one case per design while possible. Each case re-runs
  the engine (CPU clock, so parallel jobs keep the full budget) and records every realised candidate; failing ones are
  repaired as engine.select does. Shown: the engine's pick first, then the best by hand score (geometric) that differ
  from every one already shown by at least DISTINCT (mean over elements of the centre shift plus size change, in
  canvas fractions; near-duplicates measure 0-0.04, different layouts 0.2+), up to TOP. Per case: "at least one is
  acceptable" and "best candidate" -> eval/results/recall_tags.json, with the recall summary.
Labels are only used to choose what to show; nothing is fitted.
"""

import argparse
import html
import hashlib
import json
import math
import os
import random
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from eval.critic_cv import BAND, key
from eval.tag_server import ROOT

FAILURES = ("reading order broken", "scattered grouping", "cramped / crowded", "hierarchy lost", "contrast or legibility",
            "crop or aspect problem", "other")
RECALL_N, EXTREME, MODERATE, TOP, DISTINCT, SEED = 40, 3.0, 1.25, 8, 0.08, 0
THUMB = (520, 300)
STYLE = (":root{--bg:#f6f6f4;--fg:#222;--card:#fff;--muted:#6b6b6b;--line:#ddd;--accent:#2a7}"
         "@media (prefers-color-scheme:dark){:root{--bg:#1b1b1b;--fg:#eee;--card:#262626;--muted:#a0a0a0;--line:#3a3a3a}}"
         "body{background:var(--bg);color:var(--fg);font:14px system-ui;margin:0 16px 40px}"
         ".bar{position:sticky;top:0;background:var(--bg);padding:10px 0;border-bottom:1px solid var(--line);z-index:2}"
         ".item{background:var(--card);border-radius:8px;padding:10px;margin:14px 0}.row{display:flex;flex-wrap:wrap;gap:10px;align-items:flex-start}"
         ".fig img{max-height:300px;max-width:100%;display:block;background:#ccc}.fig{max-width:100%}.m{color:var(--muted);font-size:12px}"
         ".pick{outline:3px solid var(--accent)}select,textarea{font:inherit}textarea{width:min(520px,100%);height:40px}.chip{display:inline-block;margin:2px 8px 2px 0}")


def _source(sample):
    from eval.calibrate import _source as crello_or_sample
    if sample.startswith("crello_"):
        return crello_or_sample(sample)
    os.environ["CHAMELEON_ASSETS"] = str(Path(__file__).resolve().parents[1] / "brand_kit" / "assets")
    return json.loads((Path(__file__).resolve().parents[1] / "input" / f"chameleon_sample_{sample}.json").read_text())["source"]


def _thumb(design, path):
    from eval.render import render_image
    im = render_image(design)
    im.thumbnail(THUMB)
    im.save(path)


def _page(title, intro, data, script):
    blob = json.dumps(data).replace("</", "<\\/")
    return (f"<!doctype html><html lang=en><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
            f"<title>{html.escape(title)}</title><style>{STYLE}</style><body><h1>{html.escape(title)}</h1><p>{intro}</p>"
            f"<div class=bar id=bar></div><div id=items></div><script>const DATA={blob};{script}</script></body></html>")


SAVE_JS = """
async function load(name){try{const r=await fetch('/api/tags/'+name);return await r.json()}catch(e){return {}}}
let timer=null;function save(name,state){clearTimeout(timer);timer=setTimeout(()=>fetch('/api/tags/'+name,{method:'POST',
 headers:{'Content-Type':'application/json'},body:JSON.stringify(state)}).then(r=>{if(!r.ok)alert('save failed: '+r.status)}),300)}
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
"""


def failures():
    from critic.eval import DATA, hand_scores, labelled
    rows = labelled()
    hand = hand_scores(rows, DATA / "eval" / "hand_scores.json")
    picked = [(r, h) for r, h in zip(rows, hand) if h >= BAND and r["label"] == 0]
    dest = ROOT / "failures"
    dest.mkdir(parents=True, exist_ok=True)
    items = []
    for r, h in picked:
        iid = f"{r['file']}|{r['case']}|{key(r['output'])[:10]}"
        src_png, out_png = f"source__{r['sample']}.png", f"out__{key(r['output'])[:12]}.png"
        if not (dest / src_png).exists():
            _thumb(_source(r["sample"]), dest / src_png)
        _source(r["sample"])  # sets the asset folder for this design's images
        _thumb(r["output"], dest / out_png)
        c = r["output"]["canvas"]
        items.append({"id": iid, "case": r["case"], "file": r["file"], "hand": round(h, 1), "target": f"{c['width']}×{c['height']}",
                      "src": src_png, "out": out_png})
    script = SAVE_JS + """
const TAGS=%s;let state={};
function bar(){const c={};let n=0;for(const it of DATA){const t=(state[it.id]||{}).tag;if(t){n++;c[t]=(c[t]||0)+1}}
 document.getElementById('bar').innerHTML=`<b>${n} / ${DATA.length} tagged</b> &nbsp; `+TAGS.map(t=>`<span class=chip>${esc(t)}: <b>${c[t]||0}</b></span>`).join('')}
function set(id,field,val){const it=DATA.find(x=>x.id===id);state[id]=Object.assign(state[id]||{},{case:it.case,file:it.file,[field]:val,at:new Date().toISOString()});bar();save('failure',state)}
load('failure').then(s=>{state=s||{};document.getElementById('items').innerHTML=DATA.map((it,k)=>{const s=state[it.id]||{};
 return `<div class=item><div class=m>${k+1}. ${esc(it.case)} · ${esc(it.file)} · target ${it.target} · hand score <b>${it.hand}</b> · labelled <b>bad</b></div>
 <div class=row><div class=fig><img src="${it.src}" loading=lazy alt="source"><div class=m>source</div></div><div class=fig><img src="${it.out}" loading=lazy alt="engine output"><div class=m>engine output</div></div></div>
 <p><label>Primary failure <select onchange="set('${it.id}','tag',this.value)"><option value="">—</option>${TAGS.map(t=>`<option ${s.tag===t?'selected':''}>${esc(t)}</option>`).join('')}</select></label></p>
 <textarea placeholder="note" oninput="set('${it.id}','note',this.value)">${esc(s.note||'')}</textarea></div>`}).join('');bar()});
""" % json.dumps(FAILURES)
    intro = (f"Outputs you labelled <b>bad</b> that the hand scorer rates &ge; {BAND:g} ({len(items)}). Tag the primary failure; "
             "tags save to <code>eval/results/failure_tags.json</code> on every change.")
    (dest / "index.html").write_text(_page("Hand Scorer Misses", intro, items, script))
    print(f"failures: {len(items)} items -> {dest / 'index.html'}")


def _dist(a, b):
    ea = {e["id"]: e for e in a["elements"]}
    tw, th = a["canvas"]["width"], a["canvas"]["height"]
    d = [abs((e["x"] + e["width"] / 2) - (ea[e["id"]]["x"] + ea[e["id"]]["width"] / 2)) / tw
         + abs((e["y"] + e["height"] / 2) - (ea[e["id"]]["y"] + ea[e["id"]]["height"] / 2)) / th
         + abs(e["width"] - ea[e["id"]]["width"]) / tw + abs(e["height"] - ea[e["id"]]["height"]) / th
         for e in b["elements"] if e["id"] in ea]
    return float(np.mean(d)) if d else 0.0


def _recall_case(job):
    import logging
    logging.disable(logging.WARNING)
    os.environ["CHAMELEON_CPU_CLOCK"] = "1"
    from critic.make_data import engine_run
    from engine.select import _passes, repair
    from eval.score import score
    case, sample, target, change, k, name = job
    src = _source(sample)
    win, cands = engine_run(src, target)
    contributed = 0
    generator_won = False
    if name == "recall3":
        from engine.gen_candidates import LAST
        cands.extend(LAST.get("outputs", []))
        contributed = LAST.get("new_unique", 0)
        generator_won = bool(LAST.get("won_selection", False))
    fixed = [(o, False) if _passes(src, target, o) else (repair(src, target, o), True) for o in cands]
    ranked = sorted(((score(src, target, o)["total"], j) for j, (o, _r) in enumerate(fixed)), key=lambda t: -t[0])
    shown = [(win, score(src, target, win)["total"], True, not _passes(src, target, win))]
    for s, j in ranked:
        if len(shown) == TOP:
            break
        if all(_dist(fixed[j][0], o) >= DISTINCT for o, *_ in shown):
            shown.append((fixed[j][0], s, False, fixed[j][1]))
    dest = ROOT / name
    _thumb(src, dest / f"r{k}_source.png")
    _source(sample)
    out = []
    for n, (o, s, pick, rep) in enumerate(shown, 1):
        _thumb(o, dest / f"r{k}_{n}.png")
        out.append({"n": n, "img": f"r{k}_{n}.png", "hand": round(s, 1), "pick": pick, "repaired": rep})
    return {"case": case, "sample": sample, "target": f"{target['width']}×{target['height']}", "ratio": round(change, 2),
            "extreme": change >= EXTREME, "src": f"r{k}_source.png", "cands": out, "candidates_made": len(cands),
            "raw_passing": sum(1 for _o, r in fixed if not r), "generator_unique": contributed, "generator_won": generator_won,
            "wire_sha": hashlib.sha256(json.dumps(win, indent=2).encode()).hexdigest()}


def recall(jobs, name="recall"):
    if name == "recall3":
        # Exact recall2 cases/order, read-only reference; no labels copied.
        ref = Path(__file__).resolve().parents[2] / "chameleon/eval/results/crello-diagnose/recall2/cases.json"
        previous = json.loads(ref.read_text())
        picks = [r["case"] for r in previous]
        cases = {}
        for r in previous:
            w,h = map(int,r["target"].split("×"))
            source = _source(r["sample"])
            ratio = math.exp(abs(math.log((w/h)/(source["canvas"]["width"]/source["canvas"]["height"]))))
            cases[r["case"]] = (r["sample"], {"width":w,"height":h}, ratio)
    else:
        from critic.eval import labelled
        rows = labelled()
        cases = {}
        for r in rows:
            if r["case"] not in cases:
                src = _source(r["sample"])
                c = r["output"]["canvas"]
                ratio = math.exp(abs(math.log(c["width"] / c["height"] * src["canvas"]["height"] / src["canvas"]["width"])))
                cases[r["case"]] = (r["sample"], {"width": c["width"], "height": c["height"]}, ratio)
        rng = random.Random(SEED)
        picks = []
        for want in (lambda x: x >= EXTREME, lambda x: MODERATE <= x < EXTREME):
            pool = sorted(c for c, (_s, _t, x) in cases.items() if want(x))
            rng.shuffle(pool)
            first, used = [], set()
            for c in pool:  # one case per design first, then the rest if needed
                if cases[c][0] not in used:
                    first.append(c)
                    used.add(cases[c][0])
            chosen = (first + [c for c in pool if c not in first])[:RECALL_N // 2]
            print(f"  pool {len(pool)} cases ({len(used)} designs) -> {len(chosen)}")
            picks += chosen
    dest = ROOT / name
    dest.mkdir(parents=True, exist_ok=True)
    job = [(c, cases[c][0], cases[c][1], cases[c][2], k, name) for k, c in enumerate(picks)]
    with ProcessPoolExecutor(jobs) as ex:
        items = list(ex.map(_recall_case, job))
    script = SAVE_JS + f"const NAME={json.dumps(name)};" + """
let state={};
function summary(){let n=0,a=0,nx=0,ax=0;for(const it of DATA){const s=state[it.case];if(!s||!s.reviewed)continue;n++;if(s.acceptable)a++;
 if(it.extreme){nx++;if(s.acceptable)ax++}}const pct=(x,y)=>y?(100*x/y).toFixed(0)+'%':'–';
 const line=`reviewed ${n} / ${DATA.length} · recall ${pct(a,n)} (${a}/${n}) · recall at >= 3x ${pct(ax,nx)} (${ax}/${nx})`;
 document.getElementById('bar').innerHTML='<b>'+line+'</b>';return {reviewed:n,acceptable:a,recall:n?a/n:null,reviewed_3x:nx,acceptable_3x:ax,recall_3x:nx?ax/nx:null,line}}
function set(c,field,val){state[c]=Object.assign(state[c]||{},{[field]:val,reviewed:true,at:new Date().toISOString()});state._summary=summary();save(NAME,state)}
load(NAME).then(s=>{state=s||{};document.getElementById('items').innerHTML=DATA.map((it,k)=>{const s=state[it.case]||{};
 const opts=['', ...it.cands.map(c=>String(c.n)),'none'].map(v=>`<option value="${v}" ${s.best===v?'selected':''}>${v===''?'—':v==='none'?'none of them':'#'+v}</option>`).join('');
 return `<div class=item><div class=m>${k+1}. ${esc(it.case)} · target ${it.target} · aspect change ${it.ratio}x ${it.extreme?'<b>(&ge; 3x)</b>':''} · ${it.generator_won?'<b style="color:var(--accent)">★ GENERATOR WON</b> · ':''}${it.generator_unique?'<b>generator added a unique candidate</b> · ':''}${it.candidates_made} candidates made, ${it.raw_passing} pass the hard rules</div>
 <div class=row><div class=fig><img src="${it.src}" loading=lazy alt="source"><div class=m>source</div></div>
 ${it.cands.map(c=>`<div class=fig><img class="${c.pick?'pick':''}" src="${c.img}" loading=lazy alt="candidate ${c.n}"><div class=m>#${c.n}${c.pick?' · <b>engine pick</b>':''} · hand ${c.hand}${c.repaired?' · repaired':''}</div></div>`).join('')}</div>
 <p><label><input type=checkbox ${s.acceptable?'checked':''} onchange="set('${it.case}','acceptable',this.checked)"> at least one candidate is acceptable</label>
 &nbsp; <label>best candidate <select onchange="set('${it.case}','best',this.value)">${opts}</select></label></p></div>`}).join('');summary()});
"""
    intro = (f"{len(items)} cases from labelled designs (seed {SEED}): {sum(i['extreme'] for i in items)} with an aspect change &ge; {EXTREME:g}x, "
             f"{sum(not i['extreme'] for i in items)} moderate ({MODERATE:g}x to {EXTREME:g}x). Each row: the source, the engine's pick (green), then the "
             f"best-scoring candidates that differ clearly from those already shown (up to {TOP}). A case counts as reviewed once you touch either control. "
             f"Saves to <code>eval/results/{name}_tags.json</code>.")
    (dest / "index.html").write_text(_page("Candidate Recall" + (" (re-run)" if name != "recall" else ""), intro, items, script))
    (dest / "cases.json").write_text(json.dumps(items, indent=1))
    print(f"recall: {len(items)} cases, {sum(len(i['cands']) for i in items)} candidates shown -> {dest / 'index.html'}")


def _rerun_case(job):
    import logging
    logging.disable(logging.WARNING)
    os.environ["CHAMELEON_CPU_CLOCK"] = "1"
    from engine.resize import resize
    from eval.score import score
    iid, case, sample, bad, k = job
    src = _source(sample)
    target = {"width": bad["canvas"]["width"], "height": bad["canvas"]["height"]}
    new = resize(src, target)
    dest = ROOT / "rerun"
    _thumb(src, dest / f"f{k}_source.png")
    _thumb(bad, dest / f"f{k}_bad.png")
    _thumb(new, dest / f"f{k}_new.png")
    return {"id": iid, "case": case, "src": f"f{k}_source.png", "bad": f"f{k}_bad.png", "new": f"f{k}_new.png",
            "same": key(new) == key(bad), "bad_score": score(src, target, bad)["total"], "new_score": score(src, target, new)["total"]}


def rerun(jobs):
    """The non-"fine" failure tags: the labelled-bad output next to what the current engine picks for the same case."""
    from critic.eval import labelled
    tags = json.loads((ROOT.parent / "failure_tags.json").read_text())
    rows = {f"{r['file']}|{r['case']}|{key(r['output'])[:10]}": r for r in labelled()}
    job = [(iid, rows[iid]["case"], rows[iid]["sample"], rows[iid]["output"], k) for k, (iid, t) in enumerate(sorted(tags.items()))
           if iid in rows and not t.get("note", "").strip().lower().startswith("fine")]
    (ROOT / "rerun").mkdir(parents=True, exist_ok=True)
    with ProcessPoolExecutor(jobs) as ex:
        items = list(ex.map(_rerun_case, job))
    for it in items:
        it["note"] = tags[it["id"]].get("note", "")
    same = sum(i["same"] for i in items)
    up = sum(not i["same"] and i["new_score"] > i["bad_score"] for i in items)
    script = """const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
document.getElementById('items').innerHTML=DATA.map((it,k)=>`<div class=item><div class=m>${k+1}. ${esc(it.case)} · your note: ${esc(it.note)}</div>
 <div class=row><div class=fig><img src="${it.src}" loading=lazy alt=source><div class=m>source</div></div>
 <div class=fig><img src="${it.bad}" loading=lazy alt="labelled bad"><div class=m>labelled bad · score now ${it.bad_score}</div></div>
 <div class=fig><img class=pick src="${it.new}" loading=lazy alt="new pick"><div class=m>current engine${it.same?' · <b>same output</b>':''} · score ${it.new_score}</div></div></div></div>`).join('')"""
    intro = (f"{len(items)} failures you tagged (not 'fine'). Current engine: {same} unchanged, {len(items) - same} different "
             f"({up} of them scored higher than the labelled output by the current scorer). View only; nothing is saved.")
    (ROOT / "rerun" / "index.html").write_text(_page("Failures Re-run", intro, items, script))
    (ROOT / "rerun" / "cases.json").write_text(json.dumps(items, indent=1))
    print(f"rerun: {intro}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("page", choices=("failures", "recall", "recall2", "recall3", "rerun"))
    ap.add_argument("--jobs", type=int, default=4)
    args = ap.parse_args()
    if args.page == "failures":
        failures()
    elif args.page == "rerun":
        rerun(args.jobs)
    else:
        recall(args.jobs, args.page)


if __name__ == "__main__":
    main()
