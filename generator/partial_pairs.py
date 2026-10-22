"""Phase 2c: forced partial correspondences from existing sanitized descriptors."""
from __future__ import annotations
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
from generator.download import digest
from generator.make_data import DATA, atomic_json
from generator.match_real import compatible, maximum_matching
from generator.pair_data import cached_rows
from generator.phase2b import ROOT as PREVIOUS, SCHEMA as OLD_SCHEMA, provenance
from generator.real_pairs import candidates

ROOT = DATA / "generator" / "phase2c"
SCHEMA = OLD_SCHEMA.append(pa.field("matched", pa.list_(pa.bool_()))).append(pa.field("target_group_count", pa.int32()))
BUCKETS = ("<0.1", "0.1-0.5", "0.5-1", ">1")

def aspect_change(row: dict) -> float:
    aw, ah = row["canvas_a"]; bw, bh = row["canvas_b"]
    return math.log2((bw / bh) / (aw / ah))

def bucket(row: dict) -> str:
    value = abs(aspect_change(row))
    return BUCKETS[0 if value < .1 else 1 if value < .5 else 2 if value <= 1 else 3]

def forced_matching(a: list[dict], ak: list[dict], b: list[dict], bk: list[dict]) -> dict[int, int]:
    edges = [[j for j, (g, key) in enumerate(zip(b, bk)) if compatible(f, fk, g, key)] for f, fk in zip(a, ak)]
    best = maximum_matching(edges)
    return {i: j for i, j in best.items() if len(maximum_matching(edges, (i, j))) < len(best)}

def run() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    records, pairs = candidates()  # Metadata only; no conversion or engine execution.
    keys = {}
    for path in sorted((PREVIOUS / "real_descriptors").glob("*.json")):
        keys.update(json.loads(path.read_text())["group_keys"])
    rows = defaultdict(list)
    for left, right in pairs:
        a, b = records[left]["cached"], records[right]["cached"]
        mapping = forced_matching(a["groups"], keys[left], b["groups"], keys[right])
        if len(mapping) / len(a["groups"]) < .6 or len(mapping) / len(b["groups"]) < .6:
            continue
        assert a["split"] == b["split"] and a["campaign_hash"] == b["campaign_hash"]
        n = len(a["groups"])
        boxes = [b["groups"][mapping[i]]["box"] if i in mapping else [0., 0., 0., 0.] for i in range(n)]
        from generator.pair_geometry import outside_coordinates, outside_canvas
        row = {"design_hash": right, "source_design_hash": left, "campaign_hash": a["campaign_hash"],
               "split": a["split"], "raw_shard": b["raw_shard"], "raw_row": b["raw_row"], "source_kind": "real", "method": "real",
               "canvas_index": -1, "canvas_a": a["canvas"], "canvas_b": b["canvas"], "source_groups": a["groups"],
               "target_boxes": boxes, "target_group_indices": [mapping.get(i, -1) for i in range(n)],
               "target_regrouped": [False] * n, "target_outside_unit": [outside_coordinates(x) for x in boxes],
               "target_outside_canvas": [outside_canvas(x) for x in boxes], "has_outside_target": any(outside_canvas(x) for x in boxes),
               "matched": [i in mapping for i in range(n)], "target_group_count": len(b["groups"])}
        rows["real"].append(row)
    for path in sorted((PREVIOUS / "real").glob("*/pairs.parquet")):
        for row in pq.read_table(path).to_pylist():
            rows["real_strict"].append(dict(row, source_kind="real_strict", matched=[True]*len(row["source_groups"]), target_group_count=len(row["source_groups"])))
    summary = {}
    for kind, values in rows.items():
        summary[kind] = {}
        for split in ("train", "val"):
            selected = [r for r in values if r["split"] == split]
            total_a = sum(len(r["matched"]) for r in selected)
            total_b = sum(r["target_group_count"] for r in selected)
            matched = sum(sum(r["matched"]) for r in selected)
            summary[kind][split] = {"pairs": len(selected), "matched_fraction_a": matched / total_a,
                "matched_fraction_b": matched / total_b, "aspect_abs_log2_buckets": dict(Counter(bucket(r) for r in selected)),
                "signed_log2_min": min(map(aspect_change, selected)), "signed_log2_max": max(map(aspect_change, selected))}
            path = ROOT / f"{kind}_{split}.parquet"
            table = pa.Table.from_pylist(selected, schema=SCHEMA)
            if path.exists():
                assert pq.read_table(path).equals(table), "never replace completed pair data"
            else:
                temp = path.with_suffix(".partial"); pq.write_table(table, temp, compression="zstd", row_group_size=32); temp.rename(path)
    atomic_json(ROOT / "summary.json", {"seed": 2026, "bucket_definition": "abs(log2(aspect_B/aspect_A))", "sets": summary,
                                        "code_sha256": digest(Path(__file__)), **provenance()})
    print("PASS: Phase 2c", json.dumps(summary, sort_keys=True), flush=True)

if __name__ == "__main__":
    run()
