"""Pick the Crello test set from the converted designs (eval/crello_convert.py).

    python -m eval.crello_testset      # writes eval/crello_testset.json (ids and sizes only, no Crello content)

About 300 designs, spread over format, element count and aspect ratio: designs
are bucketed by (format, element-count band, aspect band) and drawn round-robin
over the buckets in a seeded order, so rare kinds are not swamped by common ones.
Each design gets 3 different random catalogue sizes (never its own size).
Designs, not cases, are split: two thirds "dev" (look at it, tune on it), one
third "holdout" (only run it to check for overfitting; never tune on it).
"""

import json
import random
from collections import defaultdict

from eval.crello_convert import OUT, REPO

N_DESIGNS, SIZES_PER_DESIGN, SEED = 300, 3, 2026
TESTSET = REPO / "eval" / "crello_testset.json"
CATALOGUE = REPO / "eval" / "canvas_catalogue.json"
ELEMENT_BANDS = (3, 7, 13, 21, 41)       # [3,7) [7,13) [13,21) [21,41)
ASPECT_BANDS = (0.7, 0.95, 1.05, 1.6)    # tall | portrait | square | landscape | wide


def band(x, edges):
    return next((k for k, e in enumerate(edges) if x < e), len(edges))


def build():
    rng = random.Random(SEED)
    metas = sorted((json.loads(p.read_text())["meta"] for p in (OUT / "designs").glob("*.json")), key=lambda m: m["id"])
    buckets = defaultdict(list)
    for m in metas:
        buckets[(m["format"], band(m["elements"], ELEMENT_BANDS), band(m["aspect"], ASPECT_BANDS))].append(m)
    keys = sorted(buckets)
    rng.shuffle(keys)
    for k in keys:
        rng.shuffle(buckets[k])
    picked = []
    while len(picked) < N_DESIGNS and any(buckets.values()):
        for k in keys:
            if buckets[k] and len(picked) < N_DESIGNS:
                picked.append(buckets[k].pop())
    catalogue = json.loads(CATALOGUE.read_text())
    rng.shuffle(picked)
    designs = []
    for n, m in enumerate(picked):
        src = json.loads((OUT / "designs" / f"{m['id']}.json").read_text())["source"]["canvas"]
        sizes = [f for f in catalogue if (f["width"], f["height"]) != (src["width"], src["height"])]
        designs.append({"id": m["id"], "split": "holdout" if n % 3 == 2 else "dev", "format": m["format"],
                        "elements": m["elements"], "aspect": m["aspect"],
                        "targets": [{"name": f["name"], "width": f["width"], "height": f["height"]}
                                    for f in rng.sample(sizes, SIZES_PER_DESIGN)]})
    TESTSET.write_text(json.dumps({"_note": __doc__.strip().splitlines()[0], "seed": SEED, "designs": designs}, indent=1) + "\n")
    for split in ("dev", "holdout"):
        ds = [d for d in designs if d["split"] == split]
        print(f"{split}: {len(ds)} designs, {sum(len(d['targets']) for d in ds)} cases, "
              f"{len({d['format'] for d in ds})} formats")
    return designs


def cases(split):
    """[(case name, design id, target {name, width, height})] for one split."""
    designs = json.loads(TESTSET.read_text())["designs"]
    return [(f"crello_{d['id']}__{_slug(t['name'])}", d["id"], t) for d in designs if d["split"] == split for t in d["targets"]]


def _slug(s):
    return "".join(c if c.isalnum() else "_" for c in s.lower()).strip("_")


if __name__ == "__main__":
    build()
