"""Shared sanitized pair schema, raw streaming and Phase 2 sample planning."""

from __future__ import annotations

import json
import random
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterator

import pyarrow as pa
import pyarrow.parquet as pq

from eval.crello_convert import COLUMNS, font_names
from generator.campaigns import hashed
from generator.make_data import DATA, GROUP, atomic_json
from generator.pair_geometry import canvases, rng_for

PHASE1 = DATA / "generator" / "phase1"
PHASE2 = DATA / "generator" / "phase2"
RAW = DATA / "crello_chameleon"
PAIR_SCHEMA = pa.schema([
    ("design_hash", pa.string()), ("campaign_hash", pa.string()), ("split", pa.string()),
    ("raw_shard", pa.int32()), ("raw_row", pa.int32()), ("method", pa.string()), ("canvas_index", pa.int32()),
    ("canvas_a", pa.list_(pa.int32(), 2)), ("canvas_b", pa.list_(pa.int32(), 2)),
    ("source_groups", pa.list_(GROUP)), ("target_boxes", pa.list_(pa.list_(pa.float64(), 4))),
    ("target_regrouped", pa.list_(pa.bool_())), ("target_outside_unit", pa.list_(pa.bool_())),
    ("target_outside_canvas", pa.list_(pa.bool_())), ("has_outside_target", pa.bool_()),
])


def cached_shards() -> list[Path]:
    return sorted((PHASE1 / "groups").glob("*.parquet"))


def cached_rows() -> Iterator[dict]:
    for path in cached_shards():
        for batch in pq.ParquetFile(path).iter_batches(batch_size=32):
            yield from batch.to_pylist()


def raw_rows(shard: int, columns: list[str] | None = None) -> Iterator[tuple[int, dict, list[str], list[str]]]:
    path = RAW / f"train-{shard:05d}-of-00031.parquet"
    pf = pq.ParquetFile(path)
    fonts, formats = font_names(pf)
    index = 0
    for batch in pf.iter_batches(batch_size=1, columns=columns or COLUMNS):
        yield index, batch.to_pylist()[0], fonts, formats
        index += 1


def prepare(out: Path = PHASE2, seed: int = 2026) -> dict:
    """Select 300 training designs once; count inferred real cross-format candidates.

    No real cross-format pair is emitted into the supervised pair dataset.
    Exact-full-text matching below remains an inference, not a native campaign ID.
    """
    random.seed(seed)
    out.mkdir(parents=True, exist_ok=True)
    stats: Counter = Counter()
    eligible = {}
    by_campaign = defaultdict(list)
    for row in cached_rows():
        split = row["split"]
        stats[split + "_original"] += 1
        if len(row["groups"]) < 2:
            stats[split + "_drop_lt2"] += 1
            continue
        stats[split + "_eligible"] += 1
        eligible[(row["raw_shard"], row["raw_row"])] = row
        by_campaign[(split, row["campaign_hash"])].append(tuple(row["canvas"]))
    candidates = sorted((r for r in eligible.values() if r["split"] == "train"), key=lambda r: r["design_hash"])
    sample = rng_for(seed, "engine_sample").sample(candidates, 300)
    plan = [{"index": i, "cached": row, "canvas_a": canvases(row["design_hash"], row["canvas"], seed)[0]}
            for i, row in enumerate(sample)]
    plan_path = out / "engine_plan.json"
    if plan_path.exists():
        assert json.loads(plan_path.read_text()) == {"seed": seed, "cases": plan}, "engine plan changed"
    else:
        atomic_json(plan_path, {"seed": seed, "cases": plan})
    inferred_pairs: Counter = Counter()
    inferred_clusters: Counter = Counter()
    for (split, _), sizes in by_campaign.items():
        n = sum(a != b for i, a in enumerate(sizes) for b in sizes[i + 1:])
        inferred_pairs[split] += n
        inferred_clusters[split] += bool(n)
    # Full normalized text stays in RAM; only its digest is used as a key.
    exact = defaultdict(list)
    for shard in range(31):
        for index, raw, _fonts, _formats in raw_rows(shard, ["id", "type", "text", "format", "canvas_width", "canvas_height"]):
            row = eligible.get((shard, index))
            if row is None:
                continue
            assert hashed(str(raw["id"])) == row["design_hash"]
            full_text = [hashed(" ".join(unicodedata.normalize("NFKC", t or "").casefold().split()))
                         for kind, t in zip(raw["type"], raw["text"]) if kind == 1]
            key = (row["split"], row["campaign_hash"], tuple(raw["type"]), tuple(full_text))
            exact[key].append((tuple(row["canvas"]), raw["format"]))
    exact_size_pairs: Counter = Counter()
    exact_format_pairs: Counter = Counter()
    for key, entries in exact.items():
        for i, (size, fmt) in enumerate(entries):
            for other_size, other_fmt in entries[i + 1:]:
                exact_size_pairs[key[0]] += size != other_size
                exact_format_pairs[key[0]] += fmt != other_fmt
    result = {"seed": seed, "designs": dict(stats), "canvases_per_design": 4, "cheap_variants": 2,
              "expected_train_pairs": stats["train_eligible"] * 8, "expected_val_pairs": stats["val_eligible"] * 8,
              "engine_sample": 300, "native_campaign_family_field": False,
              "inferred_cross_size_pairs_unordered": dict(inferred_pairs), "inferred_cross_size_clusters": dict(inferred_clusters),
              "exact_full_text_structure_cross_size_pairs_unordered": dict(exact_size_pairs),
              "exact_full_text_structure_cross_format_pairs_unordered": dict(exact_format_pairs),
              "real_campaign_pairs_used_for_training": 0}
    atomic_json(out / "plan_summary.json", result)
    print(json.dumps(result, indent=2), flush=True)
    return result


if __name__ == "__main__":
    prepare()
