"""Training data for the layout critic, from Crello TRAINING designs only.

    python -m critic.make_data --jobs 4                 # all training designs (~1,500; hours, see HANDOFF.md)
    python -m critic.make_data --limit 20 --jobs 4      # a small sample
    python -m critic.make_data --review                 # review page: 20 examples per kind, from the shards

Training designs are the converted Crello designs ($CRELLO_CHAMELEON/designs) that are NOT in
eval/crello_testset.json (dev or holdout) and whose id appears in no review labels file
(eval/results/**/labels.json): hand labels are for evaluation only and never reach training.

Every design gives up to 2 + TARGETS groups, each one positive and its negatives (a ranking loss compares
them within the group):
  original  positive: the design at its own size;  negatives: each damage (critic/damage.py) of it
  near      positive: uniform scale to a canvas of nearly the same aspect (engine.select.fallback);
            negatives: each damage of it
  engine    for TARGETS random catalogue sizes, the engine's output when it passes check() and scores at
            least POS_MIN (eval.score); negatives: each damage of it, the naive stretch (aspect change >= STRETCH_MIN),
            and up to ENGINE_LOW of the engine's own candidates scoring at least LOW_GAP points less. Skipped when the output
            doesn't qualify.
Designs are split by id (md5 % 10 == 0 -> val), so a design's groups are all in one split.

Output in --out (default $CRITIC_DATA, else ../data/critic; outside git: it holds Crello content):
  {train,val}/shard_NNNN.npz        cont [M,T,F] float16, cat [M,T,3] int8, mask [M,T] bool, group [M] int32
                                    (unique within the shard), kind [M] int8 (critic.damage.KINDS),
                                    hand [M] float32 (eval.score total, no contrast), design [M] int32
  {train,val}/shard_NNNN.jsonl.gz   one line per example: design id, group, kind, hand, target, output JSON
  index.json                        designs per split, kinds, feature names, counts, settings
"""

import argparse
import gzip
import hashlib
import json
import math
import os
import random
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get("CRITIC_DATA") or REPO.parent / "data" / "critic")
TARGETS = 2        # engine groups per design (random catalogue sizes)
POS_MIN = 88.0     # an engine output is a positive only when it passes check() and scores at least this
LOW_GAP = 8.0      # an engine candidate is a negative when it scores at least this much below the positive
ENGINE_LOW = 3
LOW_POOL = 40      # candidates scored when looking for low ones (scoring all of them is slow)
NEAR_CHANGE = 0.05  # the near group's aspect differs by at most this (ln) from the source's
STRETCH_MIN = 0.15  # naive stretch is a negative only when the aspect changes at least this much (ln): below, it looks fine
SHARD_DESIGNS = 100
REVIEW_N = 20


def training_ids():
    from eval.crello_convert import OUT as CRELLO
    from eval.crello_testset import TESTSET
    held = {d["id"] for d in json.loads(TESTSET.read_text())["designs"]}
    labelled = set()
    for f in (REPO / "eval" / "results").rglob("labels.json"):
        for case in json.loads(f.read_text()):
            if case.startswith("crello_"):
                labelled.add(case.split("__")[0][len("crello_"):])
    ids = sorted(p.stem for p in (CRELLO / "designs").glob("*.json"))
    keep = [i for i in ids if i not in held and i not in labelled]
    assert not set(keep) & (held | labelled)
    return keep


def split_of(design_id):
    return "val" if int(hashlib.md5(design_id.encode()).hexdigest(), 16) % 10 == 0 else "train"


def engine_run(source, target):
    """(winner, [candidates]): resize() with every realised candidate recorded."""
    import engine.resize as R
    made, real = [], R.realize
    def spy(*args, **kw):
        o = real(*args, **kw)
        made.append(o)
        return o
    R.realize = spy
    try:
        return R.resize(source, target), made
    finally:
        R.realize = real


def build(design_id, targets=TARGETS):
    """[(group name, target, [(kind, output, hand score, (cont, cat, mask))])] for one design."""
    from critic.damage import DAMAGES, naive_stretch
    from critic.features import encode
    from engine.analyze import analyze
    from engine.select import _passes, fallback
    from eval.crello_convert import OUT as CRELLO
    from eval.score import score

    source = json.loads((CRELLO / "designs" / f"{design_id}.json").read_text())["source"]
    a = analyze(source)
    sw, sh = source["canvas"]["width"], source["canvas"]["height"]
    rng = random.Random(design_id)
    catalogue = [t for t in json.loads((REPO / "eval" / "canvas_catalogue.json").read_text()) if (t["width"], t["height"]) != (sw, sh)]

    def example(kind, out, tgt):
        return kind, out, score(source, tgt, out)["total"], encode(a, out)

    def damaged(pos, tgt, tag):
        ex = []
        for name, f in DAMAGES.items():
            try:
                o = f(a, pos, random.Random(f"{design_id}:{tag}:{name}"))
            except Exception:  # a damage that can't read this design is just skipped
                o = None
            if o is not None:
                ex.append(example(name, o, tgt))
        return ex

    groups = []
    own = {"width": sw, "height": sh}
    groups.append(("original", own, [example("positive", source, own)] + damaged(source, own, "original")))

    s, d = rng.uniform(0.6, 1.6), rng.uniform(-NEAR_CHANGE, NEAR_CHANGE)
    near = {"width": max(50, round(sw * s * math.exp(d / 2))), "height": max(50, round(sh * s * math.exp(-d / 2)))}
    pos = fallback(source, near)
    groups.append(("near", near, [example("positive", pos, near)] + damaged(pos, near, "near")))

    for k, t in enumerate(rng.sample(catalogue, targets)):
        tgt = {"width": t["width"], "height": t["height"]}
        win, cands = engine_run(source, tgt)
        hw = score(source, tgt, win)["total"]
        if hw < POS_MIN or not _passes(source, tgt, win):
            continue
        ex = [example("positive", win, tgt)] + damaged(win, tgt, f"engine{k}")
        if abs(math.log(tgt["width"] / tgt["height"] * sh / sw)) >= STRETCH_MIN:
            ex.append(example("naive_stretch", naive_stretch(source, tgt), tgt))
        pool = random.Random(f"{design_id}:low{k}").sample(cands, min(LOW_POOL, len(cands)))
        lows = sorted(((score(source, tgt, o)["total"], j) for j, o in enumerate(pool)), key=lambda t: t[0])
        for h, j in [t for t in lows if t[0] <= hw - LOW_GAP][:ENGINE_LOW]:
            ex.append(("engine_low", pool[j], h, encode(a, pool[j])))
        groups.append((f"engine{k}:{t['name']}", tgt, ex))
    return groups


def _work(design_id, targets=TARGETS):
    try:
        return design_id, build(design_id, targets), None
    except Exception as e:  # one unreadable design must not stop a multi-hour run
        return design_id, [], f"{type(e).__name__}: {e}"


def write_shard(path, rows):
    """rows: [(design index, design id, group key, group name, target, kind, output, hand, (cont, cat, mask))]"""
    from critic.damage import KINDS
    gid = {g: k for k, g in enumerate(dict.fromkeys(r[2] for r in rows))}
    np.savez_compressed(path.with_suffix(".npz"),
                        cont=np.stack([r[8][0] for r in rows]).astype(np.float16),
                        cat=np.stack([r[8][1] for r in rows]).astype(np.int8),
                        mask=np.stack([r[8][2] for r in rows]).astype(bool),
                        group=np.array([gid[r[2]] for r in rows], np.int32),
                        kind=np.array([KINDS.index(r[5]) for r in rows], np.int8),
                        hand=np.array([r[7] for r in rows], np.float32),
                        design=np.array([r[0] for r in rows], np.int32))
    with gzip.open(path.with_suffix(".jsonl.gz"), "wt") as f:
        for r in rows:
            f.write(json.dumps({"design": r[1], "group": r[3], "kind": r[5], "hand": round(r[7], 3),
                                "target": r[4], "output": r[6]}) + "\n")


def make(out, limit, jobs, targets):
    from critic.damage import KINDS
    from critic.features import CONT, MAX_TOKENS
    from eval.crello_convert import OUT as CRELLO
    os.environ["CHAMELEON_ASSETS"] = str(CRELLO / "assets")
    os.environ["CHAMELEON_CPU_CLOCK"] = "1"  # parallel workers keep the engine's full time budget (engine/clock.py)
    ids = training_ids()
    if limit:
        ids = random.Random(0).sample(ids, min(limit, len(ids)))
    by_split = {s: [i for i in ids if split_of(i) == s] for s in ("train", "val")}
    counts, errors = Counter(), {}
    for split, sids in by_split.items():
        d = out / split
        d.mkdir(parents=True, exist_ok=True)
        for old in d.glob("shard_*"):
            old.unlink()
        index = {i: k for k, i in enumerate(sids)}
        rows, shard = [], 0
        with ProcessPoolExecutor(jobs, initializer=_quiet) as ex:
            for n, (did, groups, err) in enumerate(ex.map(_work, sids, [targets] * len(sids)), 1):
                if err:
                    errors[did] = err
                for g, (gname, tgt, exs) in enumerate(groups):
                    if len(exs) < 2:  # a positive with no negative teaches nothing
                        continue
                    for kind, o, h, enc in exs:
                        rows.append((index[did], did, f"{did}:{g}", gname, tgt, kind, o, h, enc))
                        counts[(split, kind)] += 1
                    counts[(split, "groups")] += 1
                if n % SHARD_DESIGNS == 0 or n == len(sids):
                    if rows:
                        write_shard(d / f"shard_{shard:04d}", rows)
                        shard += 1
                    rows = []
                    print(f"{split}: {n}/{len(sids)} designs, {counts[(split, 'groups')]} groups", flush=True)
    (out / "index.json").write_text(json.dumps({
        "designs": by_split, "kinds": KINDS, "features": [n for n, _d in CONT], "max_tokens": MAX_TOKENS,
        "counts": {f"{s}/{k}": v for (s, k), v in sorted(counts.items())}, "errors": errors,
        "settings": {"targets": targets, "pos_min": POS_MIN, "low_gap": LOW_GAP, "engine_low": ENGINE_LOW}}, indent=1))
    print(json.dumps({f"{s}/{k}": v for (s, k), v in sorted(counts.items())}, indent=1))
    if errors:
        print(f"{len(errors)} designs failed (see index.json)")


def _quiet():
    import logging
    logging.disable(logging.WARNING)


def review(out):
    """out/review/index.html: REVIEW_N random examples of each kind, source next to the example."""
    import html
    from eval.crello_convert import OUT as CRELLO
    from eval.render import render_image
    os.environ["CHAMELEON_ASSETS"] = str(CRELLO / "assets")
    by_kind = {}
    for f in sorted(out.glob("*/shard_*.jsonl.gz")):
        with gzip.open(f, "rt") as fh:
            for line in fh:
                r = json.loads(line)
                by_kind.setdefault(r["kind"], []).append(r)
    dest = out / "review"
    dest.mkdir(exist_ok=True)
    rng = random.Random(0)
    parts = ["<!doctype html><meta charset=utf-8><title>Critic Training Data</title><style>"
             ":root{--bg:#f6f6f4;--fg:#222;--card:#fff;--muted:#777}@media (prefers-color-scheme:dark){:root{--bg:#1b1b1b;--fg:#eee;--card:#262626;--muted:#999}}"
             "body{background:var(--bg);color:var(--fg);font:14px system-ui;margin:16px}.row{display:flex;flex-wrap:wrap;gap:10px}"
             ".c{background:var(--card);padding:6px;border-radius:6px}.c img{max-height:220px;max-width:100%;display:block;background:#ccc}"
             ".m{font-size:12px;color:var(--muted)}</style><h1>Critic training data: examples per kind</h1>"]
    for kind, rs in sorted(by_kind.items()):
        parts.append(f"<h2>{html.escape(kind)} ({len(rs)} in the shards)</h2><div class=row>")
        for k, r in enumerate(rng.sample(rs, min(REVIEW_N, len(rs)))):
            src = dest / f"source__{r['design']}.png"
            if not src.exists():
                im = render_image(json.loads((CRELLO / "designs" / f"{r['design']}.json").read_text())["source"])
                im.thumbnail((440, 220))
                im.save(src)
            im = render_image(r["output"])
            im.thumbnail((440, 220))
            im.save(dest / f"{kind}_{k}.png")
            parts.append(f"<div class=c><div class=row><img src='{src.name}' loading=lazy><img src='{kind}_{k}.png' loading=lazy></div>"
                         f"<div class=m>{r['design']} · {html.escape(r['group'])} · hand {r['hand']}</div></div>")
        parts.append("</div>")
    (dest / "index.html").write_text("\n".join(parts))
    print(f"wrote {dest / 'index.html'}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--limit", type=int, help="only this many training designs (random, seeded)")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--targets", type=int, default=TARGETS, help="engine groups per design")
    ap.add_argument("--review", action="store_true", help="only build the review page from existing shards")
    args = ap.parse_args()
    if args.review:
        review(args.out)
    else:
        make(args.out, args.limit, args.jobs, args.targets)
    return 0


if __name__ == "__main__":
    sys.exit(main())
