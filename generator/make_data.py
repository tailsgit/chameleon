"""Phase 1: streamed, resumable sanitized Crello group data; no model code."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import resource
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from eval.crello_convert import COLUMNS, font_names
from generator.campaigns import cluster, fingerprint, hashed
from generator.download import digest
from generator.extract import extract, raw_fingerprint

REPO = Path(__file__).resolve().parents[1]
MAIN = Path("/Volumes/Extreme/AdobeHackathon/chameleon")
DATA = Path("/Volumes/Extreme/AdobeHackathon/data")
SEED = 2026

PART = pa.struct([("members", pa.list_(pa.int32())), ("box", pa.list_(pa.float64(), 4))])
GROUP = pa.struct([
    ("members", pa.list_(pa.int32())), ("types", pa.list_(pa.string())), ("role", pa.string()),
    ("kind", pa.string()), ("engine_kind", pa.string()), ("box", pa.list_(pa.float64(), 4)),
    ("aspect", pa.float64()), ("char_count", pa.int32()), ("image_aspects", pa.list_(pa.float64())),
    ("area_share", pa.float64()), ("z_order", pa.int32()), ("floating", pa.bool_()),
    ("host_members", pa.list_(pa.int32())), ("parts", pa.list_(PART)), ("cols", pa.int32()),
])
FINGERPRINT = pa.struct([("types", pa.list_(pa.string())), ("texts", pa.list_(pa.string()))])
SCHEMA = pa.schema([
    ("design_hash", pa.string()), ("fingerprints", pa.list_(FINGERPRINT)),
    ("canvas", pa.list_(pa.int32(), 2)), ("groups", pa.list_(GROUP)), ("status", pa.string()),
    ("raw_shard", pa.int32()), ("raw_row", pa.int32()),
])
FINAL_SCHEMA = SCHEMA.append(pa.field("campaign_hash", pa.string())).append(pa.field("split", pa.string()))


def atomic_json(path: Path, value: object) -> None:
    partial = path.with_suffix(path.suffix + ".partial")
    partial.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    partial.replace(path)


def code_hash() -> str:
    paths = ["generator/make_data.py", "generator/extract.py", "generator/campaigns.py",
             "eval/crello_convert.py", "engine/analyze.py", "eval/score.py", "eval/check.py",
             "eval/render.py", "chameleon_design_schema_v0.9.json"]
    h = hashlib.sha256()
    for name in paths:
        h.update(name.encode()); h.update((REPO / name).read_bytes())
    return h.hexdigest()


def exclusion_ids() -> tuple[set[str], dict]:
    """Only references are extracted; verdicts/tags/outputs are never fitted on."""
    ids: set[str] = set()
    files = Counter()

    def walk(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                walk(key); walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
        elif isinstance(value, str):
            ids.update(re.findall(r"crello_([A-Za-z0-9-]+)(?=__|[^A-Za-z0-9-]|$)", value))

    for checkout in (REPO, MAIN):
        for path in sorted((checkout / "eval" / "results").rglob("*.json")):
            if path.name in {"labels.json", "failure_tags.json", "recall_tags.json", "recall2_tags.json"}:
                walk(json.loads(path.read_text()))
                files[path.name] += 1
        suite = json.loads((checkout / "eval" / "crello_testset.json").read_text())
        ids.update(str(d["id"]) for d in suite["designs"])
    # Reuse/check the earlier helper's ID exclusion boundary, without using labels as targets.
    from critic.make_data import training_ids
    existing = set(training_ids())
    converted = {p.stem for p in (DATA / "crello_chameleon" / "designs").glob("*.json")}
    assert converted - existing <= ids, "new exclusions lost an old exclusion"
    return ids, {"crello_designs": len(ids), "files_scanned": dict(files)}


def exclusion_records(ids: set[str]) -> list[dict]:
    records: dict[str, dict] = {}
    for design_id in sorted(ids):
        key = hashed(design_id)
        row = {"design_hash": key, "fingerprints": []}
        path = DATA / "crello_chameleon" / "designs" / f"{design_id}.json"
        if path.exists():
            row["fingerprints"].append(fingerprint(json.loads(path.read_text())["source"]["elements"]))
        records[design_id] = row
    found = set()
    for shard in sorted((DATA / "crello").glob("validation-*.parquet")):
        for batch in pq.ParquetFile(shard).iter_batches(batch_size=8, columns=["id", "type", "text"]):
            for row in batch.to_pylist():
                if row["id"] in records:
                    records[row["id"]]["fingerprints"].append(raw_fingerprint(row))
                    found.add(row["id"])
    assert all(row["fingerprints"] for row in records.values()), "excluded design has no fingerprint"
    print(f"exclusion fingerprints: {len(records)} Crello designs; {len(found)} found in raw validation", flush=True)
    result = list(records.values())
    for path in sorted((REPO / "input").glob("chameleon_sample_*.json")):
        source = json.loads(path.read_text())["source"]
        result.append({"design_hash": hashed("sample:" + path.stem), "fingerprints": [fingerprint(source["elements"])]})
    return result


def process_shard(path: Path, out: Path, version: str) -> dict:
    dest = out / (path.stem + ".parquet")
    done = out / (path.stem + ".done.json")
    if done.exists():
        stats = json.loads(done.read_text())
        assert stats["code_hash"] == version, "cache code changed; choose a fresh output directory"
        assert stats["input_bytes"] == path.stat().st_size
        assert digest(dest) == stats["sha256"], "cache checksum mismatch"
        print(f"resume verified {path.name}: {stats['rows']} rows", flush=True)
        return stats
    started = time.monotonic()
    pf = pq.ParquetFile(path)
    fonts, formats = font_names(pf)
    partial = dest.with_suffix(".parquet.partial")
    statuses: Counter = Counter()
    buffer = []
    row_index = 0
    with pq.ParquetWriter(partial, SCHEMA, compression="zstd") as writer:
        for batch in pf.iter_batches(batch_size=1, columns=COLUMNS):
            raw = batch.to_pylist()[0]
            record = extract(raw, fonts, formats)
            record.update(raw_shard=int(path.stem.split("-")[1]), raw_row=row_index)
            buffer.append(record)
            statuses[record["status"]] += 1
            row_index += 1
            if len(buffer) >= 32:
                writer.write_table(pa.Table.from_pylist(buffer, schema=SCHEMA)); buffer.clear()
            if row_index % 100 == 0:
                print(f"{path.name}: {row_index}/{pf.metadata.num_rows}; {dict(statuses)}", flush=True)
        if buffer:
            writer.write_table(pa.Table.from_pylist(buffer, schema=SCHEMA))
    assert row_index == pf.metadata.num_rows
    partial.replace(dest)
    stats = {"rows": row_index, "statuses": dict(statuses), "seconds": time.monotonic() - started,
             "sha256": digest(dest), "input_bytes": path.stat().st_size, "code_hash": version}
    atomic_json(done, stats)
    print(f"completed {path.name}: {stats['rows']} rows in {stats['seconds']:.1f}s", flush=True)
    return stats


def finalize(cache: Path, out: Path, excluded: list[dict], stats: list[dict], seed: int) -> dict:
    started = time.monotonic()
    # Only fingerprints are loaded across shards. Pixels and source text stay per-row.
    records = []
    for path in sorted(cache.glob("*.parquet")):
        records.extend(pq.read_table(path, columns=["design_hash", "fingerprints", "status"]).to_pylist())
    counts = Counter(r["status"] for r in records)
    ids = [r["design_hash"] for r in records]
    assert len(ids) == len(set(ids)), "duplicate template IDs in train data"
    components, edges = cluster([*records, *excluded])
    excluded_ids = {r["design_hash"] for r in excluded}
    banned_clusters = {components[key] for key in excluded_ids}
    direct_matches = {e["left"] if e["right"] in excluded_ids else e["right"] for e in edges if e["left"] in excluded_ids or e["right"] in excluded_ids}
    drops: Counter = Counter()
    kept = []
    for row in records:
        key = row["design_hash"]
        if key in excluded_ids:
            drops["excluded_id"] += 1
        elif components[key] in banned_clusters:
            drops["campaign_direct" if key in direct_matches else "campaign_transitive"] += 1
        elif row["status"] != "ok":
            drops["conversion_" + row["status"]] += 1
        else:
            kept.append(key)
    kept_set = set(kept)
    clusters = sorted({components[k] for k in kept}, key=lambda k: hashed(f"{seed}:{k}"))
    n_val = round(0.05 * len(clusters))
    validation = set(clusters[:n_val])
    train_ids, val_ids, train_clusters, val_clusters = set(), set(), set(), set()
    group_counts, flow_counts, all_boxes = [], [], []
    group_kinds: Counter = Counter()
    out.mkdir(parents=True, exist_ok=True)
    for source in sorted(cache.glob("*.parquet")):
        rows = []
        for row in pq.read_table(source).to_pylist():
            key = row["design_hash"]
            if key not in kept_set:
                continue
            campaign = components[key]
            split = "val" if campaign in validation else "train"
            (val_ids if split == "val" else train_ids).add(key)
            (val_clusters if split == "val" else train_clusters).add(campaign)
            row.update(campaign_hash=campaign, split=split)
            rows.append(row)
            group_counts.append(len(row["groups"]))
            flow_counts.append(sum(g["kind"] not in {"background", "panel"} and not g["floating"] for g in row["groups"]))
            for g in row["groups"]:
                all_boxes.append(g["box"]); group_kinds[g["kind"]] += 1
        destination = out / source.name
        partial = destination.with_suffix(".parquet.partial")
        pq.write_table(pa.Table.from_pylist(rows, schema=FINAL_SCHEMA), partial, compression="zstd")
        partial.replace(destination)
    assert not train_ids & val_ids
    assert not (train_ids | val_ids) & excluded_ids
    assert not train_clusters & val_clusters
    assert not (train_clusters | val_clusters) & banned_clusters
    assert len(train_ids | val_ids) == len(kept)
    examples = [e for e in edges if ((e["left"] in excluded_ids) != (e["right"] in excluded_ids)) and (e["left"] in set(ids) or e["right"] in set(ids))][:10]
    atomic_json(out.parent / "campaign_matches.json", {"examples": examples, "matched_edges": edges})
    atomic_json(out.parent / "exclusion_fingerprints.json", excluded)
    def distribution(values: list[int]) -> dict:
        return {"min": min(values), "median": float(np.median(values)), "p95": float(np.percentile(values, 95)), "max": max(values)}
    boxes = np.asarray(all_boxes)
    summary = {"raw_rows": len(records), "conversion_statuses_before_exclusion": dict(counts), "drops": dict(drops),
               "kept": len(kept), "train": len(train_ids), "val": len(val_ids), "train_campaigns": len(train_clusters),
               "val_campaigns": len(val_clusters), "excluded_design_fingerprints": len(excluded_ids), "excluded_campaigns": len(banned_clusters),
               "all_campaign_edges": len(edges), "groups": distribution(group_counts), "flow_groups": distribution(flow_counts),
               "group_kinds": dict(group_kinds), "group_total": len(all_boxes), "box_min_xywh": boxes.min(axis=0).tolist(),
               "box_max_xywh": boxes.max(axis=0).tolist(), "boxes_outside_unit_interval": int(((boxes < 0) | (boxes > 1)).any(axis=1).sum()),
               "leakage": {"train_val_designs": 0, "train_val_campaigns": 0, "excluded_designs": 0, "excluded_campaigns": 0},
               "seed": seed, "extraction_seconds": sum(s["seconds"] for s in stats), "finalize_seconds": time.monotonic() - started,
               "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
               "examples": examples}
    atomic_json(out.parent / "summary.json", summary)
    print(json.dumps(summary, indent=2), flush=True)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=DATA / "crello_chameleon")
    parser.add_argument("--out", type=Path, default=DATA / "generator" / "phase1")
    parser.add_argument("--limit-shards", type=int)
    parser.add_argument("--follow-download", action="store_true", help="process each shard as its verified download completes")
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()
    random.seed(args.seed); np.random.seed(args.seed)
    os.environ["CRELLO_CHAMELEON"] = str(DATA / "crello_chameleon")
    cache = args.out / "cache"; cache.mkdir(parents=True, exist_ok=True)
    ids, exclusion_stats = exclusion_ids()
    excluded = exclusion_records(ids)
    print(f"seed={args.seed}; {exclusion_stats}", flush=True)
    paths = sorted(args.raw.glob("train-*.parquet"))
    if args.follow_download:
        assert args.limit_shards is None
        paths = [args.raw / f"train-{index:05d}-of-00031.parquet" for index in range(31)]
    elif args.limit_shards:
        paths = paths[:args.limit_shards]
    else:
        verification = json.loads((DATA / "generator" / "download" / "verified.json").read_text())
        assert len(paths) == verification["shards"] == 31
        assert sum(pq.ParquetFile(p).metadata.num_rows for p in paths) == verification["rows"] == 19479
    assert paths, "no complete train shards available"
    version = code_hash()
    stats = []
    for path in paths:
        waiting = time.monotonic()
        while not path.exists():
            assert time.monotonic() - waiting < 1800, f"download not available within 30 minutes: {path.name}"
            print(f"waiting for verified download {path.name}", flush=True)
            time.sleep(30)
        stats.append(process_shard(path, cache, version))
    if not args.limit_shards:
        verification_path = DATA / "generator" / "download" / "verified.json"
        waiting = time.monotonic()
        while not verification_path.exists():
            assert time.monotonic() - waiting < 1800, "download verification not available"
            time.sleep(5)
        verification = json.loads(verification_path.read_text())
        assert sum(s["rows"] for s in stats) == verification["rows"] == 19479
    summary = finalize(cache, args.out / "groups", excluded, stats, args.seed)
    summary["exclusion_sources"] = exclusion_stats
    summary["disk_bytes"] = sum(p.stat().st_size for p in args.out.rglob("*") if p.is_file())
    atomic_json(args.out / "summary.json", summary)
    print(f"PASS: sanitized cache and split; {summary['disk_bytes']} bytes", flush=True)


if __name__ == "__main__":
    main()
