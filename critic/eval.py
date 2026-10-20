"""How well does the critic agree with the hand labels, next to the hand scorer (eval.score)?

    python -m critic.eval --model engine/data/critic.onnx            # or a PyTorch checkpoint (.pt)
    python -m critic.eval --model ... --page                         # also the 20 worst disagreements, as a page

Labels: every eval/results/**/labels.json (the review pages' Good / Okay / Bad, including the random-30 v5
set), each with the exact output it was given on; the latest verdict per (case, output) counts, as in
eval.calibrate. They are only ever read here: critic.make_data excludes every labelled design from training.

Metrics (eval.calibrate.agreement): pairwise = share of differently-labelled pairs both scores order the same
way (the hand scorer's 0.866 is this, pooled over all labels); within = the same, only among outputs of the
same design (the critic is trained to compare layouts of one design, so this is its fairer number); auc =
chance a Good output outscores a Bad one. Printed pooled and per label file.
The hand scorer includes rendered contrast (score(..., contrast=True)), cached in --cache by output hash.
Disagreement page (--page): rank each labelled output by critic score (0 = lowest, 1 = highest) and compare
with its label (bad 0, okay 0.5, good 1); the 20 largest gaps, source next to output, in --out.
"""

import argparse
import hashlib
import html
import json
import os
from pathlib import Path

import numpy as np

from eval.calibrate import RANK, _source, agreement

REPO = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get("CRITIC_DATA") or REPO.parent / "data" / "critic")
REFERENCE = 0.866  # the hand scorer's pooled pairwise agreement when the critic work started (NOTES §28)


def labelled():
    """[{file, case, sample, label, output}], latest verdict per (case, output) in each file."""
    rows = []
    for f in sorted((REPO / "eval" / "results").rglob("labels.json")):
        latest = {}
        for case, entry in json.loads(f.read_text()).items():
            for lab in [*entry.get("history", []), entry]:
                if lab.get("verdict") and lab.get("output"):
                    key = (case, json.dumps(lab["output"], sort_keys=True))
                    if key not in latest or lab.get("at", "") >= latest[key].get("at", ""):
                        latest[key] = lab
        name = f.parent.name if f.parent.name != "results" else "samples"
        rows += [{"file": name, "case": c, "sample": c.split("__")[0], "label": RANK[lab["verdict"]], "output": lab["output"]}
                 for (c, _o), lab in sorted(latest.items())]
    return rows


def hand_scores(rows, cache):
    from eval.score import score
    version = hashlib.md5((REPO / "eval" / "score.py").read_bytes()).hexdigest()
    store = json.loads(cache.read_text()) if cache.exists() else {}
    if store.get("version") != version:
        store = {"version": version, "scores": {}}
    out = []
    for r in rows:
        key = hashlib.md5(json.dumps(r["output"], sort_keys=True).encode()).hexdigest()
        if key not in store["scores"]:
            store["scores"][key] = score(_source(r["sample"]), r["output"]["canvas"], r["output"], contrast=True)["total"]
        out.append(store["scores"][key])
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(store))
    return out


def critic_scores(rows, model):
    from critic.features import encode
    from engine.analyze import analyze
    analyses = {}
    enc = []
    for r in rows:
        if r["sample"] not in analyses:
            analyses[r["sample"]] = analyze(_source(r["sample"]))
        enc.append(encode(analyses[r["sample"]], r["output"]))
    cont, cat, mask = (np.stack([e[k] for e in enc]) for k in range(3))
    if str(model).endswith(".onnx"):
        import onnxruntime as ort
        sess = ort.InferenceSession(str(model), providers=["CPUExecutionProvider"])
        return sess.run(["score"], {"cont": cont.astype(np.float32), "cat": cat.astype(np.int64), "mask": mask.astype(np.float32)})[0].tolist()
    import torch
    from critic.model import build
    ck = torch.load(model, map_location="cpu")
    net = build(ck["config"])
    net.load_state_dict(ck["model"])
    net.eval()
    with torch.no_grad():
        return net(torch.from_numpy(cont.astype(np.float32)), torch.from_numpy(cat.astype(np.int64)), torch.from_numpy(mask.astype(np.float32))).tolist()


def metrics(scores, rows):
    scores, labels = np.asarray(scores, float), np.array([r["label"] for r in rows])
    a = agreement(scores, labels)
    per = [agreement(scores[m], labels[m])["pairwise"] for m in (np.array([r["sample"] == s for r in rows]) for s in sorted({r["sample"] for r in rows}))]
    a["within"] = float(np.nanmean(per)) if any(not np.isnan(p) for p in per) else float("nan")
    return a


def page(rows, crit, hand, dest):
    from eval.render import render_image
    pct = np.argsort(np.argsort(crit)) / max(1, len(crit) - 1)
    gap = np.abs(pct - np.array([r["label"] / 2 for r in rows]))
    dest.mkdir(parents=True, exist_ok=True)
    names = {0: "bad", 1: "okay", 2: "good"}
    parts = ["<!doctype html><meta charset=utf-8><title>Critic Disagreements</title><style>"
             ":root{--bg:#f6f6f4;--fg:#222;--card:#fff;--muted:#777}@media (prefers-color-scheme:dark){:root{--bg:#1b1b1b;--fg:#eee;--card:#262626;--muted:#999}}"
             "body{background:var(--bg);color:var(--fg);font:14px system-ui;margin:16px}.row{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:24px}"
             ".c{background:var(--card);padding:6px;border-radius:6px}.c img{max-height:300px;max-width:100%;display:block;background:#ccc}"
             ".m{color:var(--muted)}</style><h1>Critic disagreements: the 20 labelled outputs it ranks furthest from your label</h1>"
             "<p>Rank = the output's critic-score percentile among all labelled outputs (0 lowest, 1 highest). Label target: bad 0, okay 0.5, good 1.</p>"]
    for k in np.argsort(-gap)[:20]:
        r = rows[k]
        src = dest / f"source__{r['sample']}.png"
        if not src.exists():
            im = render_image(_source(r["sample"]))
            im.thumbnail((600, 300))
            im.save(src)
        im = render_image(r["output"])
        im.thumbnail((600, 300))
        im.save(dest / f"out_{k}.png")
        parts.append(f"<h3>{html.escape(r['case'])} <span class=m>({html.escape(r['file'])})</span></h3><div class=row>"
                     f"<div class=c><img src='{src.name}'><div class=m>source</div></div><div class=c><img src='out_{k}.png'>"
                     f"<div>labelled <b>{names[r['label']]}</b> · critic rank {pct[k]:.2f} (score {crit[k]:.3f}) · hand score {hand[k]:.1f}</div></div></div>")
    (dest / "index.html").write_text("\n".join(parts))
    print(f"wrote {dest / 'index.html'}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", type=Path, required=True, help="critic .onnx (critic.export) or .pt checkpoint")
    ap.add_argument("--cache", type=Path, default=DATA / "eval" / "hand_scores.json")
    ap.add_argument("--page", action="store_true")
    ap.add_argument("--out", type=Path, default=DATA / "eval" / "disagreements")
    args = ap.parse_args()
    rows = labelled()
    index = DATA / "index.json"
    if index.exists():  # labels must never have been training data
        trained = {i for ids in json.loads(index.read_text())["designs"].values() for i in ids}
        leaked = {r["sample"][len("crello_"):] for r in rows} & trained
        assert not leaked, f"labelled designs found in the training data: {sorted(leaked)[:5]}"
    hand, crit = hand_scores(rows, args.cache), critic_scores(rows, args.model)
    print(f"{len(rows)} labelled outputs in {len({r['file'] for r in rows})} label files; reference: hand scorer pooled pairwise {REFERENCE}\n")
    print(f"{'labels':<28} {'n':>4}   {'hand: pairwise within auc':<28} {'critic: pairwise within auc'}")
    groups = [("ALL (pooled)", rows)] + [(f, [r for r in rows if r["file"] == f]) for f in sorted({r["file"] for r in rows})]
    result = {}
    for name, rs in groups:
        idx = [rows.index(r) for r in rs]
        h, c = metrics([hand[k] for k in idx], rs), metrics([crit[k] for k in idx], rs)
        result[name] = {"n": len(rs), "hand": h, "critic": c}
        f = lambda m: f"{m['pairwise']:.3f}    {m['within']:.3f}   {m['auc']:.3f}"
        print(f"{name:<28} {len(rs):>4}   {f(h):<28} {f(c)}")
    a = result["ALL (pooled)"]["critic"]["pairwise"]
    print(f"\ncritic pooled pairwise {a:.3f} vs the bar {REFERENCE}: {'BEATS' if a > REFERENCE else 'below'} it")
    (DATA / "eval").mkdir(parents=True, exist_ok=True)
    (DATA / "eval" / "result.json").write_text(json.dumps({"model": str(args.model), "result": result}, indent=1, default=float))
    if args.page:
        page(rows, np.asarray(crit), np.asarray(hand), args.out)


if __name__ == "__main__":
    main()
