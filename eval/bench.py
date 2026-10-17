"""Benchmark engine.resize over every sample design x every catalogue size.

    python -m eval.bench              # check + geometric score, ~ms per case
    python -m eval.bench --render     # also render each case + a contact sheet
    python -m eval.bench --contrast   # also the render-based contrast penalty

Writes eval/results/summary.md, eval/results/cases.csv and, with --render,
eval/results/renders/*.png + eval/results/contact_sheet.png.
"""

import argparse
import copy
import csv
import json
import statistics
import subprocess
import time
import traceback
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw

from engine.resize import resize
from eval.check import check, text_layout
from eval.score import PENALTIES, score

REPO = Path(__file__).resolve().parents[1]
CATALOGUE = REPO / "eval" / "canvas_catalogue.json"
SAMPLES = sorted((REPO / "input").glob("chameleon_sample_*.json"))
CELL, THUMB = 230, 200


def slug(s):
    return "".join(c if c.isalnum() else "_" for c in s.lower()).strip("_")


def run(render=False, contrast=False, out_dir=REPO / "eval" / "results"):
    commit = _commit()  # before writing results, which would make the tree look dirty
    out_dir.mkdir(parents=True, exist_ok=True)
    formats = json.loads(CATALOGUE.read_text())
    tasks = [(p.stem.replace("chameleon_sample_", ""), json.loads(p.read_text())) for p in SAMPLES]
    if render:
        from eval.render import render_image
        (out_dir / "renders").mkdir(exist_ok=True)
    _warm_up(tasks[0][1]["source"], render)
    if render:
        for sample, task in tasks:  # the original designs, for side-by-side review
            render_image(task["source"]).save(out_dir / "renders" / f"source__{sample}.png")

    rows, thumbs = [], []
    for sample, task in tasks:
        for fmt in formats:
            target = {"width": fmt["width"], "height": fmt["height"]}
            case = f"{sample}__{slug(fmt['name'])}"
            row = {"case": case, "sample": sample, "format": fmt["name"], "width": fmt["width"], "height": fmt["height"]}
            try:
                t = time.perf_counter()
                output = resize(copy.deepcopy(task["source"]), target)
                row["resize_ms"] = (time.perf_counter() - t) * 1000
            except Exception:
                row.update(passed=False, violations=1, rules="crash", total=0.0, error=traceback.format_exc(limit=1))
                rows.append(row)
                continue

            t = time.perf_counter()
            v = check(task["source"], target, output)
            row["check_ms"] = (time.perf_counter() - t) * 1000
            t = time.perf_counter()
            s = score(task["source"], target, output, contrast=contrast)
            row["score_ms"] = (time.perf_counter() - t) * 1000

            row.update(passed=not v, violations=len(v), rules=";".join(f"{x['rule']}:{x['id']}" for x in v),
                       total=s["total"], **{k: b["penalty"] for k, b in s["breakdown"].items()})
            if render:
                t = time.perf_counter()
                img = render_image(output)
                row["render_ms"] = (time.perf_counter() - t) * 1000
                img.save(out_dir / "renders" / f"{case}.png")
                thumbs.append((sample, fmt["name"], img, row))
            rows.append(row)

    _write_csv(rows, out_dir / "cases.csv")
    summary = _summary(rows, formats, render, contrast, commit)
    (out_dir / "summary.md").write_text(summary)
    if render:
        _contact_sheet(thumbs, [t[0] for t in tasks], [f["name"] for f in formats], out_dir / "contact_sheet.png")
    print(summary)
    return rows


def _warm_up(source, render):
    """Font loading and first-call imports take ~1s; keep them out of the per-case timings."""
    text_layout(next(e for e in source["elements"] if e["type"] == "text"))
    if render:
        from eval.render import render_image
        render_image(source)


def _write_csv(rows, path):
    cols = ["case", "sample", "format", "width", "height", "passed", "violations", "total",
            *PENALTIES, "rules", "resize_ms", "check_ms", "score_ms", "render_ms", "error"]
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.4g}" if isinstance(v, float) else v) for k, v in r.items()})


def _commit():
    try:
        return subprocess.run(["git", "describe", "--always", "--dirty"], cwd=REPO, capture_output=True,
                              text=True).stdout.strip() or "?"
    except OSError:
        return "?"


def _summary(rows, formats, render, contrast, commit):
    def mean(xs):
        xs = [x for x in xs if x is not None]
        return statistics.mean(xs) if xs else float("nan")

    def ms(key):
        xs = [r[key] for r in rows if key in r]
        return f"mean {statistics.mean(xs):.2f} ms, median {statistics.median(xs):.2f} ms, max {max(xs):.2f} ms" if xs else "n/a"

    passed = sum(r["passed"] for r in rows)
    by_rule = Counter()
    cases_by_rule = Counter()
    for r in rows:
        rules = [x.split(":")[0] for x in r["rules"].split(";") if x]
        by_rule.update(rules)
        cases_by_rule.update(set(rules))
    penalties = [k for k in PENALTIES if any(k in r for r in rows)]

    out = [f"# Benchmark summary\n",
           f"Engine commit `{commit}`, {len(rows)} cases ({len(rows) // len(formats)} samples x {len(formats)} formats), "
           f"render={'yes' if render else 'no'}, contrast={'yes' if contrast else 'no'}.\n",
           f"- **Cases passing every hard rule: {passed}/{len(rows)}**",
           f"- **Average score: {mean(r['total'] for r in rows):.2f}** / 100\n",
           "## Violations by rule\n", "| rule | violations | cases |", "|---|---|---|"]
    out += [f"| {rule} | {n} | {cases_by_rule[rule]} |" for rule, n in by_rule.most_common()] or ["| (none) | 0 | 0 |"]
    out += ["\n## Average penalty (0 = perfect, 1 = worst)\n", "| " + " | ".join(penalties) + " |",
            "|" + "---|" * len(penalties),
            "| " + " | ".join(f"{mean(r.get(k) for r in rows):.3f}" for k in penalties) + " |"]
    samples = sorted({r["sample"] for r in rows})
    out += ["\n## Score by format\n", "| format | size | " + " | ".join(samples) + " | passed |",
            "|---|---|" + "---|" * (len(samples) + 1)]
    for f in formats:
        fr = [r for r in rows if r["format"] == f["name"]]
        cells = [f"{next(r['total'] for r in fr if r['sample'] == s):.1f}" for s in samples]
        out.append(f"| {f['name']} | {f['width']}x{f['height']} | " + " | ".join(cells) + f" | {sum(r['passed'] for r in fr)}/{len(fr)} |")
    out += ["\n## Timings (per case, this machine)\n", f"- resize: {ms('resize_ms')}", f"- check: {ms('check_ms')}",
            f"- score: {ms('score_ms')}" + (" (incl. contrast render)" if contrast else ""), f"- render: {ms('render_ms')}"]
    return "\n".join(out) + "\n"


def _contact_sheet(thumbs, samples, formats, path):
    label_h = 28
    sheet = Image.new("RGB", (CELL * len(formats) + 110, (CELL + label_h) * len(samples) + 10), "white")
    d = ImageDraw.Draw(sheet)
    for sample, fmt, img, row in thumbs:
        r, c = samples.index(sample), formats.index(fmt)
        x0, y0 = 110 + c * CELL, 5 + r * (CELL + label_h)
        t = img.copy()
        t.thumbnail((THUMB, THUMB))
        sheet.paste(t, (x0 + (CELL - t.width) // 2, y0 + (THUMB - t.height) // 2))
        d.rectangle([x0 + (CELL - t.width) // 2 - 1, y0 + (THUMB - t.height) // 2 - 1,
                     x0 + (CELL + t.width) // 2, y0 + (THUMB + t.height) // 2], outline="#999")
        mark = "PASS" if row["passed"] else f"{row['violations']} viol"
        d.text((x0 + 4, y0 + THUMB + 3), f"{fmt[:24]}", fill="black")
        d.text((x0 + 4, y0 + THUMB + 15), f"{row['total']:.1f}  {mark}", fill="#2F855A" if row["passed"] else "#C53030")
        if c == 0:
            d.text((5, y0 + THUMB // 2), sample, fill="black")
    sheet.save(path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--render", action="store_true", help="render every case to PNG + contact sheet")
    ap.add_argument("--contrast", action="store_true", help="include the render-based contrast penalty")
    args = ap.parse_args()
    run(render=args.render, contrast=args.contrast)
