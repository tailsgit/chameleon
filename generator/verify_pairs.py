"""Audit pair coverage, untouched real targets, flags, and Phase 1 split membership."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import logging
import math
from collections import Counter, defaultdict
from pathlib import Path

import pyarrow.parquet as pq

from engine.analyze import full_box
from eval.crello_convert import convert
from generator.pair_data import PAIR_SCHEMA, PHASE1, PHASE2, cached_shards, raw_rows
from generator.verify_data import verify as verify_phase1


def verify(root: Path) -> dict:
    leakage = verify_phase1(PHASE1)
    logging.disable(logging.CRITICAL)
    counts: Counter = Counter()
    covered = {s: set() for s in ("train", "val")}
    eligible = Counter()
    for cached_path in cached_shards():
        shard = int(cached_path.stem.split("-")[1])
        originals = {r["raw_row"]: r for r in pq.read_table(cached_path).to_pylist()}
        for r in originals.values():
            eligible[r["split"]] += len(r["groups"]) >= 2
        pairs = defaultdict(list)
        seen = set()
        for split in covered:
            path = root / split / f"shard_{shard:05d}.parquet"
            assert pq.read_schema(path) == PAIR_SCHEMA
            for batch in pq.ParquetFile(path).iter_batches(batch_size=32):
                for pair in batch.to_pylist():
                    original = originals[pair["raw_row"]]
                    assert pair["raw_shard"] == shard
                    assert pair["split"] == original["split"] == split
                    assert pair["design_hash"] == original["design_hash"]
                    assert pair["campaign_hash"] == original["campaign_hash"]
                    assert len(original["groups"]) >= 2
                    assert pair["canvas_b"] == original["canvas"]
                    assert pair["canvas_a"] != pair["canvas_b"]
                    key = (pair["raw_row"], pair["canvas_index"], pair["method"])
                    assert key not in seen
                    seen.add(key)
                    assert pair["method"] in {"stretch_uniform", "uniform_fit"}
                    assert 0 <= pair["canvas_index"] < 4
                    n = len(pair["source_groups"])
                    assert n >= 2
                    assert all(len(pair[k]) == n for k in ("target_boxes", "target_regrouped", "target_outside_unit", "target_outside_canvas"))
                    pairs[pair["raw_row"]].append(pair)
                    covered[split].add(pair["design_hash"])
                    counts[split + "_pairs"] += 1
        for index, raw, fonts, formats in raw_rows(shard):
            if index not in pairs:
                continue
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                target, _meta, images = convert(raw, fonts, formats)
            try:
                original = originals[index]
                canonical = {tuple(g["members"]): g["box"] for g in original["groups"]}
                bw, bh = original["canvas"]
                for pair in pairs.pop(index):
                    split = pair["split"]
                    members = [m for g in pair["source_groups"] for m in g["members"]]
                    assert sorted(members) == list(range(len(target["elements"])))
                    flags = []
                    for i, g in enumerate(pair["source_groups"]):
                        assert all(math.isfinite(v) for v in g["box"])
                        assert g["char_count"] == sum(len(target["elements"][m].get("content", "")) for m in g["members"])
                        key = tuple(g["members"])
                        regrouped = key not in canonical
                        if regrouped:
                            bounds = [full_box(target["elements"][m]) for m in key]
                            x0, y0 = min(b[0] for b in bounds), min(b[1] for b in bounds)
                            x1, y1 = max(b[2] for b in bounds), max(b[3] for b in bounds)
                            expected = [x0 / bw, y0 / bh, (x1 - x0) / bw, (y1 - y0) / bh]
                        else:
                            expected = canonical[key]
                        box = pair["target_boxes"][i]
                        assert box == expected, "real target geometry changed"
                        assert all(math.isfinite(v) for v in box)
                        assert pair["target_regrouped"][i] == regrouped
                        outside = any(v < 0 or v > 1 for v in box)
                        overflow = outside or box[0] + box[2] > 1 + 1e-9 or box[1] + box[3] > 1 + 1e-9
                        assert pair["target_outside_unit"][i] == outside
                        assert pair["target_outside_canvas"][i] == overflow
                        flags.append(overflow)
                        counts[split + "_groups"] += 1
                        counts[split + "_regrouped_groups"] += regrouped
                    assert pair["has_outside_target"] == any(flags)
            finally:
                for image in images.values():
                    image.close()
        assert not pairs
        print(f"verified pair shard {shard:02d}", flush=True)
    summary = json.loads((root / "summary.json").read_text())
    for split in covered:
        assert counts[split + "_pairs"] == summary["counts"][split + "_pairs"]
        assert len(covered[split]) == summary["counts"][split + "_designs_with_pairs"]
        assert eligible[split] == summary["counts"][split + "_designs"]
    assert not covered["train"] & covered["val"]
    result = {"counts": dict(counts), "eligible_designs": dict(eligible),
              "designs_with_pairs": {s: len(v) for s, v in covered.items()},
              "designs_without_pairs": {s: eligible[s] - len(v) for s, v in covered.items()},
              "leakage": leakage, "all_real_targets_exact": True, "all_flags_correct": True}
    print("PASS: " + json.dumps(result, sort_keys=True), flush=True)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=PHASE2 / "pairs")
    verify(parser.parse_args().root)
