"""Audit all four pair kinds and emit a geometry-only training-data manifest."""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import logging
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

from engine.analyze import full_box
from eval.crello_convert import convert
from generator.download import digest
from generator.make_data import atomic_json
from generator.match_real import compatible
from generator.pair_data import PHASE1, cached_rows, raw_rows
from generator.phase2b import ROOT, SCHEMA, KINDS
from generator.verify_data import verify as verify_phase1


def unique_by_cycles(groups_a: list[dict], keys_a: list[dict], groups_b: list[dict], keys_b: list[dict], mapping: list[int]) -> None:
    """Independently detect alternate perfect matchings as alternating cycles."""
    inverse = {j: i for i, j in enumerate(mapping)}
    edges = [[inverse[j] for j, (b, bk) in enumerate(zip(groups_b, keys_b))
              if j != mapping[i] and compatible(a, ak, b, bk)] for i, (a, ak) in enumerate(zip(groups_a, keys_a))]
    active, done = set(), set()
    def visit(i: int) -> None:
        assert i not in active, "ambiguous real correspondence: alternating cycle"
        if i in done:
            return
        active.add(i)
        for j in edges[i]:
            visit(j)
        active.remove(i); done.add(i)
    for i in range(len(edges)):
        visit(i)


def audit_engine_targets(rows: dict[int, list[dict]], shard: int, cached: dict) -> None:
    for index, raw, fonts, formats in raw_rows(shard):
        if index not in rows:
            continue
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            design, _meta, images = convert(raw, fonts, formats)
        try:
            for pair in rows.pop(index):
                original = cached[pair["design_hash"]]
                canonical = {tuple(g["members"]): g["box"] for g in original["groups"]}
                bw, bh = original["canvas"]
                assert sorted(m for g in pair["source_groups"] for m in g["members"]) == list(range(len(design["elements"])))
                for g, box, changed in zip(pair["source_groups"], pair["target_boxes"], pair["target_regrouped"]):
                    assert g["char_count"] == sum(len(design["elements"][m].get("content", "")) for m in g["members"])
                    if tuple(g["members"]) in canonical:
                        expected = canonical[tuple(g["members"])]
                        assert not changed
                    else:
                        bounds = [full_box(design["elements"][m]) for m in g["members"]]
                        x, y = min(b[0] for b in bounds), min(b[1] for b in bounds)
                        expected = [x / bw, y / bh, (max(b[2] for b in bounds) - x) / bw, (max(b[3] for b in bounds) - y) / bh]
                        assert changed
                    assert box == expected, "engine pair target was changed or clipped"
        finally:
            for image in images.values():
                image.close()
    assert not rows


def run(root: Path) -> dict:
    leakage = verify_phase1(PHASE1)
    logging.disable(logging.CRITICAL)
    cached = {r["design_hash"]: r for r in cached_rows()}
    plan = json.loads((root / "reflow_plan.json").read_text())
    planned = {c["cached"]["design_hash"]: c for c in plan["cases"]}
    assert len(planned) == 3300
    assert Counter(c["cached"]["split"] for c in planned.values()) == {"train": 3000, "val": 300}
    descriptors = {}
    for path in sorted((root / "real_descriptors").glob("*.json")):
        descriptors.update(json.loads(path.read_text())["group_keys"])
    counts = Counter()
    distances = defaultdict(list)
    seen = set()
    manifest = []
    engine_rows = defaultdict(lambda: defaultdict(list))
    paths = sorted((root / "cheap").glob("*/*/pairs.parquet")) + sorted((root / "engine").glob("*/pairs.parquet")) + sorted((root / "real").glob("*/pairs.parquet"))
    assert len(paths) == 124, "expected 62 cheap, 31 engine, and 31 real shards"
    for path in paths:
        meta = json.loads((path.parent / "metadata.json").read_text())
        assert digest(path) == meta["sha256"]
        assert len(meta["engine_commit"]) == 40
        datetime.fromisoformat(meta["created_utc"])
        schema = pq.read_schema(path)
        assert schema.remove_metadata() == SCHEMA
        assert schema.metadata[b"engine_commit"].decode() == meta["engine_commit"]
        nrows = 0
        for batch in pq.ParquetFile(path).iter_batches(batch_size=32):
            for pair in batch.to_pylist():
                nrows += 1
                kind, split = pair["source_kind"], pair["split"]
                assert KINDS[pair["method"]] == kind
                source, target = cached[pair["source_design_hash"]], cached[pair["design_hash"]]
                assert source["split"] == target["split"] == split
                assert source["campaign_hash"] == target["campaign_hash"] == pair["campaign_hash"]
                assert len(source["groups"]) >= 2 and len(target["groups"]) >= 2
                assert pair["canvas_b"] == target["canvas"]
                assert (pair["raw_shard"], pair["raw_row"]) == (target["raw_shard"], target["raw_row"])
                groups, boxes = pair["source_groups"], pair["target_boxes"]
                assert len(groups) == len(boxes) >= 2
                assert all(len(pair[k]) == len(groups) for k in ("target_regrouped", "target_outside_unit", "target_outside_canvas"))
                key = (kind, source["design_hash"], target["design_hash"], pair["canvas_index"])
                assert key not in seen, "duplicate pair"
                seen.add(key)
                flags = []
                for i, (g, box) in enumerate(zip(groups, boxes)):
                    assert all(math.isfinite(v) for v in [*g["box"], *box])
                    outside = any(v < 0 or v > 1 for v in box)
                    overflow = outside or box[0] + box[2] > 1 + 1e-9 or box[1] + box[3] > 1 + 1e-9
                    assert pair["target_outside_unit"][i] == outside
                    assert pair["target_outside_canvas"][i] == overflow
                    flags.append(overflow)
                assert pair["has_outside_target"] == any(flags)
                if kind == "real":
                    mapping = pair["target_group_indices"]
                    assert source["design_hash"] < target["design_hash"], "one canonical direction per candidate"
                    assert groups == source["groups"] and pair["canvas_a"] == source["canvas"]
                    assert len(mapping) == len(groups) == len(target["groups"])
                    assert sorted(mapping) == list(range(len(groups)))
                    assert not any(pair["target_regrouped"])
                    for i, j in enumerate(mapping):
                        assert boxes[i] == target["groups"][j]["box"]
                        assert compatible(groups[i], descriptors[source["design_hash"]][i], target["groups"][j], descriptors[target["design_hash"]][j])
                    unique_by_cycles(groups, descriptors[source["design_hash"]], target["groups"], descriptors[target["design_hash"]], mapping)
                else:
                    assert source["design_hash"] == target["design_hash"]
                    assert pair["target_group_indices"] is None
                    if kind == "engine":
                        case = planned[target["design_hash"]]
                        assert pair["canvas_a"] == [case["canvas_a"]["width"], case["canvas_a"]["height"]]
                        engine_rows[pair["raw_shard"]][pair["raw_row"]].append(pair)
                counts[(kind, split)] += 1
                distances[(kind, split)].append(float(np.abs(np.asarray([g["box"] for g in groups]) - np.asarray(boxes)).mean()))
        assert nrows == meta["rows"]
        manifest.append({"path": str(path.relative_to(root)), "sha256": meta["sha256"], "rows": nrows})
        print(f"audited {path.relative_to(root)}: {nrows}", flush=True)
    for shard, rows in sorted(engine_rows.items()):
        audit_engine_targets(rows, shard, cached)
        print(f"verified exact engine targets in raw shard {shard:02d}", flush=True)
    statuses, case_distances = Counter(), []
    case_ids = set()
    for path in sorted((root / "engine_cases").glob("*/*.json")):
        case = json.loads(path.read_text())
        h = case["identity"]["design_hash"]
        assert h in planned and h not in case_ids
        case_ids.add(h)
        statuses[case["status"]] += 1
        case_distances.append(case["wall_seconds"])
    assert case_ids == set(planned)
    assert statuses["ok"] == counts[("engine", "train")] + counts[("engine", "val")]
    reflow = json.loads((root / "reflow_summary.json").read_text())
    real = json.loads((root / "real_summary.json").read_text())
    assert real["candidate_pairs"] == 18492
    for split in ("train", "val"):
        assert counts[("real", split)] == real["clean_pairs"].get(split, 0)
    results = {kind: {split: {"pairs": counts[(kind, split)],
                            "median_box_l1": float(np.median(distances[(kind, split)])) if distances[(kind, split)] else None}
                      for split in ("train", "val")} for kind in ("stretch", "whole_fit", "engine", "real")}
    result = {"seed": 2026, "kinds": results, "leakage": leakage, "reflow_statuses": dict(statuses),
              "reflow_median_wall_seconds": float(np.median(case_distances)), "reflow_wall_seconds": reflow["wall_seconds"],
              "real_train_below_5000": counts[("real", "train")] < 5000,
              "real_matching": real, "all_real_and_engine_targets_exact": True, "all_flags_correct": True,
              "logical_parquet_bytes": sum(p.stat().st_size for p in paths)}
    atomic_json(root / "manifest.json", {"seed": 2026, "source_kind_tokens": ["stretch", "whole_fit", "engine", "real"],
                                          "inference_source_kind": "real", "shards": manifest})
    atomic_json(root / "report.json", result)
    print("PASS: Phase 2b", json.dumps(result, sort_keys=True), flush=True)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    run(parser.parse_args().root)
