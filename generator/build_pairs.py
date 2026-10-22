"""Stream seeded cheap-source pairs into separate train/validation Parquet shards."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import logging
import random
import time
from collections import Counter
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from engine.analyze import analyze
from eval.crello_convert import convert
from generator.campaigns import hashed
from generator.download import digest
from generator.extract import group_features
from generator.make_data import atomic_json
from generator.pair_data import PAIR_SCHEMA, PHASE2, cached_shards, raw_rows
from generator.pair_geometry import METHODS, canvases, cheap_source, pair_record
from generator.transient import render_assets


def code_version() -> str:
    root = Path(__file__).resolve().parents[1]
    files = ["generator/build_pairs.py", "generator/pair_geometry.py", "generator/pair_data.py",
             "generator/transient.py", "generator/extract.py", "engine/analyze.py", "eval/score.py",
             "eval/check.py", "eval/crello_convert.py", "renderer/converter/convert.py", "renderer/converter/assets.py"]
    return hashed("".join(digest(root / name) for name in files))


def shard_pairs(path: Path, out: Path, seed: int, version: str, limit: int | None,
                minimum_source_groups: int, only_split: str) -> dict:
    shard = int(path.stem.split("-")[1])
    marker = out / f"shard_{shard:05d}.done.json"
    if marker.exists():
        stats = json.loads(marker.read_text())
        assert stats["code_hash"] == version and stats["input_sha256"] == digest(path)
        assert stats["seed"] == seed and stats["limit"] == limit
        assert stats["minimum_source_groups"] == minimum_source_groups and stats["only_split"] == only_split
        for split in ("train", "val"):
            assert digest(out / split / f"shard_{shard:05d}.parquet") == stats["output_sha256"][split]
        print(f"resume verified pair shard {shard:02d}: {stats['pairs']} pairs", flush=True)
        return stats
    cached = {r["raw_row"]: r for r in pq.read_table(path).to_pylist()
              if len(r["groups"]) >= 2 and (only_split == "both" or r["split"] == only_split)}
    if limit is not None:
        cached = dict(list(sorted(cached.items()))[:limit])
    begin = time.monotonic()
    counts: Counter = Counter()
    minimum, maximum = np.full(4, np.inf), np.full(4, -np.inf)
    buffers = {split: [] for split in ("train", "val")}
    partials = {split: out / split / f"shard_{shard:05d}.parquet.partial" for split in buffers}
    with contextlib.ExitStack() as stack:
        writers = {split: stack.enter_context(pq.ParquetWriter(partials[split], PAIR_SCHEMA, compression="zstd")) for split in buffers}
        for index, raw, fonts, formats in raw_rows(shard):
            row = cached.get(index)
            if row is None:
                continue
            assert hashed(str(raw["id"])) == row["design_hash"]
            split = row["split"]
            emitted = 0
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                target, _meta, images = convert(raw, fonts, formats)
                try:
                    with render_assets(images):
                        assert group_features(analyze(target)) == row["groups"], "original real-target cache drift"
                        for canvas in canvases(row["design_hash"], row["canvas"], seed):
                            assert [canvas["width"], canvas["height"]] != row["canvas"]
                            for method in METHODS:
                                source = cheap_source(target, row["groups"], canvas, method, seed, row["design_hash"], canvas["index"])
                                pair = pair_record(target, row, source, method, canvas["index"])
                                assert len(pair["source_groups"]) == len(pair["target_boxes"])
                                assert all(np.isfinite(g["box"]).all() for g in pair["source_groups"])
                                counts[split + "_attempted_pairs"] += 1
                                counts[split + "_source_lt2_candidates"] += len(pair["source_groups"]) < 2
                                if len(pair["source_groups"]) < minimum_source_groups:
                                    counts[split + "_skipped_source_lt2_pairs"] += 1
                                    continue
                                boxes = np.asarray(pair["target_boxes"])
                                minimum = np.minimum(minimum, boxes.min(axis=0)); maximum = np.maximum(maximum, boxes.max(axis=0))
                                buffers[split].append(pair)
                                counts[split + "_pairs"] += 1
                                counts[split + "_outside_target_pairs"] += pair["has_outside_target"]
                                counts[split + "_regrouped_groups"] += sum(pair["target_regrouped"])
                                counts[split + "_groups"] += len(pair["source_groups"])
                                counts[split + "_source_lt2_pairs"] += len(pair["source_groups"]) < 2
                                emitted += 1
                                if len(buffers[split]) >= 32:
                                    writers[split].write_table(pa.Table.from_pylist(buffers[split], schema=PAIR_SCHEMA))
                                    buffers[split].clear()
                finally:
                    for image in images.values(): image.close()
            counts[split + "_designs"] += 1
            counts[split + "_designs_with_pairs"] += emitted > 0
            if sum(counts[k] for k in ("train_designs", "val_designs")) % 100 == 0:
                print(f"pair shard {shard:02d}: {counts['train_designs'] + counts['val_designs']}/{len(cached)} designs", flush=True)
            if counts["train_designs"] + counts["val_designs"] == len(cached):
                break
        for split, buffer in buffers.items():
            if buffer:
                writers[split].write_table(pa.Table.from_pylist(buffer, schema=PAIR_SCHEMA))
    assert counts["train_designs"] + counts["val_designs"] == len(cached)
    hashes = {}
    for split, partial in partials.items():
        dest = out / split / f"shard_{shard:05d}.parquet"
        partial.replace(dest); hashes[split] = digest(dest)
        assert counts[split + "_attempted_pairs"] == counts[split + "_designs"] * 8
        assert counts[split + "_pairs"] + counts[split + "_skipped_source_lt2_pairs"] == counts[split + "_attempted_pairs"]
    stats = {"code_hash": version, "input_sha256": digest(path), "seed": seed, "limit": limit,
             "minimum_source_groups": minimum_source_groups, "only_split": only_split,
             "output_sha256": hashes, "counts": dict(counts), "pairs": counts["train_pairs"] + counts["val_pairs"],
             "seconds": time.monotonic() - begin,
             "target_box_min": minimum.tolist() if counts["train_pairs"] + counts["val_pairs"] else [],
             "target_box_max": maximum.tolist() if counts["train_pairs"] + counts["val_pairs"] else []}
    atomic_json(marker, stats)
    print(f"completed pair shard {shard:02d}: {stats['pairs']} pairs in {stats['seconds']:.1f}s", flush=True)
    return stats


def build(out: Path, seed: int, limit: int | None, minimum_source_groups: int = 2, only_split: str = "both") -> dict:
    random.seed(seed); np.random.seed(seed)
    logging.disable(logging.CRITICAL)
    for split in ("train", "val"):
        (out / split).mkdir(parents=True, exist_ok=True)
    paths = cached_shards()
    if limit is not None:
        paths = paths[:1]
    version = code_version()
    stats = [shard_pairs(path, out, seed, version, limit, minimum_source_groups, only_split) for path in paths]
    counts: Counter = Counter()
    for row in stats:
        counts.update(row["counts"])
    bounded_stats = [s for s in stats if s["target_box_min"]]
    assert bounded_stats, "no pairs survived the source-group filter"
    result = {"seed": seed, "code_hash": version, "canvases_per_design": 4, "cheap_variants": list(METHODS),
              "minimum_source_groups": minimum_source_groups, "only_split": only_split,
              "counts": dict(counts), "seconds": sum(s["seconds"] for s in stats), "shards_per_split": len(paths),
              "parquet_bytes": sum(p.stat().st_size for p in out.rglob("*.parquet")),
              "target_box_min": np.min([s["target_box_min"] for s in bounded_stats], axis=0).tolist(),
              "target_box_max": np.max([s["target_box_max"] for s in bounded_stats], axis=0).tolist(),
              "real_campaign_pairs_used": 0, "engine_pairs_mixed_into_cheap_dataset": 0}
    if limit is None:
        plan = json.loads((PHASE2 / "plan_summary.json").read_text())
        if only_split in {"both", "train"}:
            assert counts["train_attempted_pairs"] == plan["expected_train_pairs"]
        if only_split in {"both", "val"}:
            assert counts["val_attempted_pairs"] == plan["expected_val_pairs"]
            assert counts["val_designs"] == 970
    atomic_json(out / "summary.json", result)
    print(json.dumps(result, indent=2), flush=True)
    print("PASS: streamed separate train/val pair shards", flush=True)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=PHASE2 / "pairs")
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--limit-designs", type=int)
    parser.add_argument("--min-source-groups", type=int, choices=[1, 2], default=2)
    parser.add_argument("--split", choices=["both", "train", "val"], default="both")
    args = parser.parse_args()
    build(args.out, args.seed, args.limit_designs, args.min_source_groups, args.split)
