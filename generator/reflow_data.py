"""Four concurrent bounded reflows over a fixed format-balanced train/val subset."""
from __future__ import annotations

import argparse
import json
import os
import pickle
import random
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np

from generator.campaigns import hashed
from generator.download import digest
from generator.engine_sample import bounded_process, version as engine_version
from generator.make_data import atomic_json
from generator.pair_data import cached_rows, raw_rows
from generator.pair_geometry import canvases, rng_for
from generator.phase2b import ROOT, promote, provenance, publish, verified


def balanced(rows: list[dict], count: int, seed: int, split: str) -> list[dict]:
    buckets = defaultdict(list)
    for row in sorted(rows, key=lambda r: r["design_hash"]):
        buckets[row["format"]].append(row)
    for fmt, values in buckets.items():
        rng_for(seed, "phase2b", split, fmt).shuffle(values)
    names = sorted(buckets)
    rng_for(seed, "phase2b", split, "format_order").shuffle(names)
    result = []
    while len(result) < count:
        for name in names:
            if buckets[name]:
                result.append(buckets[name].pop())
                if len(result) == count:
                    break
        assert any(buckets.values()) or len(result) == count
    return result


def plan(root: Path, seed: int = 2026) -> dict:
    cached = {(r["raw_shard"], r["raw_row"]): r for r in cached_rows() if len(r["groups"]) >= 2}
    for shard in range(31):
        for index, raw, _fonts, formats in raw_rows(shard, ["id", "format"]):
            if (row := cached.get((shard, index))) is not None:
                assert row["design_hash"] == hashed(str(raw["id"]))
                row["format"] = formats[raw["format"]]
    selected = []
    for split, count in (("train", 3000), ("val", 300)):
        selected.extend(balanced([r for r in cached.values() if r["split"] == split], count, seed, split))
    cases = [{"cached": r, "canvas_a": canvases(r["design_hash"], r["canvas"], seed)[0]} for r in selected]
    value = {"seed": seed, "selection": "balanced round-robin across native formats", "cases": cases}
    path = root / "reflow_plan.json"
    if path.exists():
        assert json.loads(path.read_text()) == value
    else:
        atomic_json(path, value)
    print("fixed reflow plan", json.dumps({s: dict(Counter(c["cached"]["format"] for c in cases if c["cached"]["split"] == s)) for s in ("train", "val")}), flush=True)
    return value


def shard_job(root: Path, shard: int, cases: list[dict], identity: dict) -> dict:
    dest = root / "engine" / f"shard_{shard:05d}"
    if (meta := verified(dest, identity)) is not None:
        print(f"resume verified engine shard {shard:02d}", flush=True)
        return meta
    checkpoints = root / "engine_cases" / f"shard_{shard:05d}"
    checkpoints.mkdir(parents=True, exist_ok=True)
    wanted = {c["cached"]["raw_row"]: c for c in cases}
    env = dict(os.environ, PYTHONHASHSEED="2026", OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
               CHAMELEON_CPU_CLOCK="1", CHAMELEON_CRITIC="0")
    started = time.monotonic()
    results = []
    for index, raw, fonts, formats in raw_rows(shard):
        if index not in wanted:
            continue
        case = wanted[index]
        cached = case["cached"]
        checkpoint = checkpoints / f"row_{index:05d}.json"
        case_identity = dict(identity, design_hash=cached["design_hash"])
        if checkpoint.exists():
            result = json.loads(checkpoint.read_text())
            assert result["identity"] == case_identity
        else:
            assert hashed(str(raw["id"])) == cached["design_hash"]
            output = bounded_process([sys.executable, "-u", "-m", "generator.engine_sample", "--worker"],
                                     pickle.dumps((raw, fonts, formats, cached, case["canvas_a"], 2026)), timeout=20.0, env=env)
            result = {"identity": case_identity, **provenance(), "wall_seconds": output["elapsed"],
                      "split": cached["split"], "status": "timeout", "pair": None}
            if not output["timed_out"]:
                response = json.loads(output["stdout"])
                assert output["returncode"] == 0 and response["status"] == "ok", response
                pair = promote(response["pair"])
                result.update(status="ok" if len(pair["source_groups"]) >= 2 else "source_lt2",
                              pair=pair if len(pair["source_groups"]) >= 2 else None,
                              resize_seconds=response["engine_seconds"])
            assert not checkpoint.exists(), "immutable case output already exists"
            atomic_json(checkpoint, result)
        results.append(result)
        if len(results) % 10 == 0:
            print(f"engine shard {shard:02d}: {len(results)}/{len(cases)} cases", flush=True)
    assert len(results) == len(cases)
    meta = publish(dest, [r["pair"] for r in results if r["pair"] is not None], identity,
                   {"statuses": dict(Counter(r["status"] for r in results)), "attempts": len(results),
                    "seconds": time.monotonic() - started,
                    "median_wall_seconds": float(np.median([r["wall_seconds"] for r in results]))})
    print(f"completed immutable engine shard {shard:02d}: {meta['statuses']}", flush=True)
    return meta


def run(root: Path, workers: int, limit_shards: int | None = None) -> None:
    random.seed(2026); np.random.seed(2026)
    root.mkdir(parents=True, exist_ok=True)
    planned = plan(root)
    by_shard = defaultdict(list)
    for case in planned["cases"]:
        by_shard[case["cached"]["raw_shard"]].append(case)
    identity = {"seed": 2026, "plan_sha256": digest(root / "reflow_plan.json"),
                "engine_version": engine_version(), "runner_sha256": digest(Path(__file__)),
                "storage_sha256": digest(Path(__file__).with_name("phase2b.py")), "timeout_seconds": 20}
    items = sorted(by_shard.items())[:limit_shards]
    start = time.monotonic()
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(shard_job, root, shard, cases, identity) for shard, cases in items]
        results = [f.result() for f in as_completed(futures)]
    summary = {"shards": len(results), "workers": workers, "wall_seconds": time.monotonic() - start,
               "attempts": sum(r["attempts"] for r in results), "pairs": sum(r["rows"] for r in results),
               "statuses": dict(sum((Counter(r["statuses"]) for r in results), Counter()))}
    if limit_shards is None:
        assert summary["attempts"] == 3300
    atomic_json(root / "reflow_summary.json", summary)
    print("PASS: reflow", json.dumps(summary), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--workers", type=int, choices=[1, 4], default=4)
    parser.add_argument("--limit-shards", type=int)
    args = parser.parse_args()
    run(args.root, args.workers, args.limit_shards)
