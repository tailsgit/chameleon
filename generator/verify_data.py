"""Independently check persisted feature schema, finite geometry and split leakage."""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path

import pyarrow.parquet as pq

from generator.campaigns import cluster
from generator.make_data import FINAL_SCHEMA, DATA, exclusion_ids
from generator.campaigns import hashed


def verify(root: Path) -> dict:
    assigned = {}
    groups = Counter()
    ids = {"train": set(), "val": set()}
    campaigns = {"train": set(), "val": set()}
    for path in sorted((root / "groups").glob("*.parquet")):
        assert pq.read_schema(path) == FINAL_SCHEMA, "unexpected persisted fields"
        for batch in pq.ParquetFile(path).iter_batches(batch_size=32):
            for row in batch.to_pylist():
                split = row["split"]
                assert split in ids
                assert row["design_hash"] not in ids[split], "duplicate design"
                ids[split].add(row["design_hash"])
                campaigns[split].add(row["campaign_hash"])
                assert re.fullmatch("[a-f0-9]{64}", row["design_hash"])
                assert re.fullmatch("[a-f0-9]{64}", row["campaign_hash"])
                for fp in row["fingerprints"]:
                    assert all(t in {"image", "text", "shape"} for t in fp["types"])
                    assert all(re.fullmatch("[a-f0-9]{64}", text) for text in fp["texts"])
                for group in row["groups"]:
                    assert all(math.isfinite(v) for v in group["box"])
                    assert all(v > 0 for v in group["box"][2:])
                    assert group["char_count"] >= 0
                    groups[split] += 1
                assigned[row["design_hash"]] = row["campaign_hash"]
    excluded = json.loads((root / "exclusion_fingerprints.json").read_text())
    # Rebuild the full closure, retaining links through rejected/dropped designs.
    fingerprints = []
    for path in sorted((root / "cache").glob("*.parquet")):
        fingerprints.extend(pq.read_table(path, columns=["design_hash", "fingerprints"]).to_pylist())
    components, _ = cluster(fingerprints + excluded)
    assert all(components[key] == value for key, value in assigned.items()), "campaign assignment differs from full closure"
    excluded_ids = {r["design_hash"] for r in excluded}
    current_ids, _ = exclusion_ids()
    assert {hashed(key) for key in current_ids} <= excluded_ids, "exclusion sources changed during preprocessing"
    excluded_clusters = {components[key] for key in excluded_ids}
    train_clusters = {components[key] for key in ids["train"]}
    val_clusters = {components[key] for key in ids["val"]}
    assert not ids["train"] & ids["val"]
    assert not (ids["train"] | ids["val"]) & excluded_ids
    assert not train_clusters & val_clusters
    assert not (train_clusters | val_clusters) & excluded_clusters
    assert not campaigns["train"] & campaigns["val"]
    summary = json.loads((root / "summary.json").read_text())
    assert len(ids["train"]) == summary["train"]
    assert len(ids["val"]) == summary["val"]
    assert sum(groups.values()) == summary["group_total"]
    result = {"train_designs": len(ids["train"]), "val_designs": len(ids["val"]), "groups": dict(groups),
              "train_val_design_overlap": 0, "train_val_campaign_overlap": 0,
              "excluded_design_overlap": 0, "excluded_campaign_overlap": 0}
    print(f"PASS: {json.dumps(result, sort_keys=True)}")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DATA / "generator" / "phase1")
    verify(parser.parse_args().root)
