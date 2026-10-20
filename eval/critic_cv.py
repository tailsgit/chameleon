"""Judge any layout scorer against the hand labels, with leave-one-label-file-out cross-validation.

    python -m eval.critic_cv                                   # baseline: the hand scorer (eval.score, contrast on)
    python -m eval.critic_cv --scores my_scores.json           # {output key: score}; key = md5 of the output JSON (sorted keys)
    python -m eval.critic_cv --scorer mypkg.mod:fn             # fn(row) -> float, or fn(train_rows, test_rows) -> [float]

Labels: every eval/results/**/labels.json (latest verdict per (case, output), as critic.eval.labelled). Each row is
{file, case, sample, label (0 bad, 1 okay, 2 good), output}. Labels are only ever evaluated against, never fitted on,
except by a scorer that takes (train_rows, test_rows), which sees only the training folds' rows.

Folds: one per label file, but grouped by source design: a design labelled in several files goes to the fold of the
file holding most of its rows (ties: the first file by name), so no design is in two folds. A two-argument scorer is
fitted on the other folds and scores the held-out one; a plain scorer just scores every row.

Metrics (all on held-out scores, pooled over folds, and per fold):
  pooled     pairwise agreement over all differently-labelled pairs (eval.calibrate.agreement; the 0.830 figure)
  within     pairwise agreement only between outputs of the same design: pair-weighted, and the mean over designs
  auc        bad vs rest (okay + good), over all outputs and inside the band where the hand score >= BAND
  top1_bad   share of designs (with 2+ labelled outputs) whose highest-scored output is labelled bad; "avoidable"
             counts only designs that have at least one non-bad output
Hand scores come from the critic.eval cache (../data/critic/eval/hand_scores.json), so a baseline run takes seconds.
"""

import argparse
import hashlib
import importlib
import inspect
import json
import time
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

import numpy as np

from critic.eval import DATA, hand_scores, labelled
from eval.calibrate import agreement

BAND = 85.0


def key(output):
    return hashlib.md5(json.dumps(output, sort_keys=True).encode()).hexdigest()


def folds(rows):
    """{fold name: [row index]}, one fold per label file, each design in exactly one fold."""
    per = defaultdict(Counter)
    for r in rows:
        per[r["sample"]][r["file"]] += 1
    home = {d: min(c.items(), key=lambda t: (-t[1], t[0]))[0] for d, c in per.items()}
    out = defaultdict(list)
    for i, r in enumerate(rows):
        out[home[r["sample"]]].append(i)
    return dict(sorted(out.items()))


def auc(scores, bad):
    pos, neg = scores[~bad], scores[bad]  # rest should outscore bad
    if not len(pos) or not len(neg):
        return float("nan")
    return float(np.mean([(p > n) + 0.5 * (p == n) for p in pos for n in neg]))


def metrics(scores, rows, hand):
    scores, lab, hand = np.asarray(scores, float), np.array([r["label"] for r in rows]), np.asarray(hand, float)
    by = defaultdict(list)
    for i, r in enumerate(rows):
        by[r["sample"]].append(i)
    right = n = 0.0
    per = []
    top, avoid = [], []
    for idx in by.values():
        pairs = [(i, j) for i, j in combinations(idx, 2) if lab[i] != lab[j]]
        if pairs:
            ok = sum(1.0 if np.sign(scores[i] - scores[j]) == np.sign(lab[i] - lab[j]) else 0.5 if scores[i] == scores[j] else 0.0
                     for i, j in pairs)
            right, n = right + ok, n + len(pairs)
            per.append(ok / len(pairs))
        if len(idx) >= 2:
            bad = lab[max(idx, key=lambda i: scores[i])] == 0
            top.append(bad)
            if any(lab[i] > 0 for i in idx):
                avoid.append(bad)
    bad = lab == 0
    band = hand >= BAND
    return {"n": len(rows), "pooled": agreement(scores, lab)["pairwise"] if len(set(lab)) > 1 else float("nan"),
            "within_pairs": int(n), "within_pair": right / n if n else float("nan"), "within_designs": len(per),
            "within_mean": float(np.mean(per)) if per else float("nan"),
            "auc": auc(scores, bad), "band_n": int(band.sum()), "band_auc": auc(scores[band], bad[band]),
            "top1_designs": len(top), "top1_bad": float(np.mean(top)) if top else float("nan"),
            "top1_avoidable_designs": len(avoid), "top1_bad_avoidable": float(np.mean(avoid)) if avoid else float("nan")}


def evaluate(rows, hand, scorer):
    """Held-out scores for every row, and {fold: metrics}."""
    fs = folds(rows)
    fitted = callable(scorer) and len(inspect.signature(scorer).parameters) == 2
    held = np.zeros(len(rows))
    for name, idx in fs.items():
        if fitted:
            train = [rows[i] for i in range(len(rows)) if i not in set(idx)]
            held[idx] = scorer(train, [rows[i] for i in idx])
        else:
            held[idx] = [scorer(rows[i]) for i in idx]
    return held, {name: metrics(held[idx], [rows[i] for i in idx], hand[idx]) for name, idx in fs.items()}, fs


def report(title, pooled, per):
    f = lambda v: "  nan" if v != v else f"{v:.3f}"
    print(f"\n{title}")
    print(f"  {'fold':<26}{'n':>4} {'pooled':>7} {'within(pair)':>13} {'within(mean)':>13} {'auc':>6} {'band auc':>9} {'top1 bad':>9}")
    for name, m in [("ALL (held-out, pooled)", pooled)] + list(per.items()):
        print(f"  {name:<26}{m['n']:>4} {f(m['pooled']):>7} {f(m['within_pair']):>7} ({m['within_pairs']:>3}) {f(m['within_mean']):>7} ({m['within_designs']:>2})"
              f" {f(m['auc']):>6} {f(m['band_auc']):>6} ({m['band_n']:>3}) {f(m['top1_bad']):>5} ({m['top1_designs']:>2})")
    print(f"  top-1 bad among designs with a non-bad option: {f(pooled['top1_bad_avoidable'])} ({pooled['top1_avoidable_designs']} designs)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scores", type=Path, help="JSON {output key: score}")
    ap.add_argument("--scorer", help="module:function")
    ap.add_argument("--cache", type=Path, default=DATA / "eval" / "hand_scores.json")
    args = ap.parse_args()
    t = time.time()
    rows = labelled()
    hand = np.array(hand_scores(rows, args.cache))
    hk = {key(r["output"]): h for r, h in zip(rows, hand)}
    held, per, fs = evaluate(rows, hand, lambda r: hk[key(r["output"])])
    moved = sum(1 for name, idx in fs.items() for i in idx if rows[i]["file"] != name)
    print(f"{len(rows)} labelled outputs, {len({r['sample'] for r in rows})} designs, {len(fs)} folds"
          f" ({moved} rows moved to another file's fold so each design is in one fold)")
    report("hand scorer (baseline)", metrics(held, rows, hand), per)
    if args.scores or args.scorer:
        if args.scores:
            table = json.loads(args.scores.read_text())
            scorer = lambda r: table[key(r["output"])]
            title = str(args.scores)
        else:
            mod, fn = args.scorer.split(":")
            scorer, title = getattr(importlib.import_module(mod), fn), args.scorer
        held, per, _ = evaluate(rows, hand, scorer)
        report(title, metrics(held, rows, hand), per)
    print(f"\n({time.time() - t:.1f} s)")


if __name__ == "__main__":
    main()
