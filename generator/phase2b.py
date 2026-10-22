"""Versioned pair schema and immutable shard storage for Phase 2b."""
from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from generator.download import digest
from generator.make_data import DATA, atomic_json
from generator.pair_data import PAIR_SCHEMA

ROOT = DATA / "generator" / "phase2b"
SCHEMA = PAIR_SCHEMA.append(pa.field("source_kind", pa.string())).append(
    pa.field("source_design_hash", pa.string())).append(pa.field("target_group_indices", pa.list_(pa.int32())))
KINDS = {"stretch_uniform": "stretch", "uniform_fit": "whole_fit", "engine": "engine", "real": "real"}


def provenance() -> dict:
    repo = Path(__file__).resolve().parents[1]
    def git(*args: str) -> str:
        return subprocess.check_output(["git", *args], cwd=repo, text=True, stderr=subprocess.DEVNULL).strip()
    assert git("branch", "--show-current") == "generator"
    assert not git("diff", "HEAD", "--", "engine"), "engine must remain unchanged"
    return {"engine_commit": git("log", "-1", "--format=%H", "--", "engine"),
            "checkout_commit": git("rev-parse", "HEAD"),
            "created_utc": datetime.now(timezone.utc).isoformat(), "seed": 2026}


def promote(pair: dict) -> dict:
    return dict(pair, source_kind=KINDS[pair["method"]], source_design_hash=pair["design_hash"],
                target_group_indices=None)


def verified(path: Path, identity: dict) -> dict | None:
    if not path.exists():
        return None
    meta = json.loads((path / "metadata.json").read_text())
    assert meta["identity"] == identity, "completed shard identity changed"
    assert digest(path / "pairs.parquet") == meta["sha256"], "immutable shard checksum changed"
    assert pq.read_schema(path / "pairs.parquet").remove_metadata() == SCHEMA
    return meta


def publish(path: Path, rows: list[dict], identity: dict, extra: dict | None = None) -> dict:
    assert not path.exists(), "never overwrite a completed shard"
    stage = path.with_name(path.name + ".partial")
    if stage.exists():
        shutil.rmtree(stage)  # Only this shard's incomplete publication, never a completed cache.
    stage.mkdir(parents=True)
    meta = {"identity": identity, **provenance(), "rows": len(rows), **(extra or {})}
    arrow_meta = {k.encode(): str(v).encode() for k, v in meta.items() if k != "identity"}
    pq.write_table(pa.Table.from_pylist(rows, schema=SCHEMA.with_metadata(arrow_meta)),
                   stage / "pairs.parquet", compression="zstd", row_group_size=32)
    meta["sha256"] = digest(stage / "pairs.parquet")
    atomic_json(stage / "metadata.json", meta)
    assert not path.exists(), "never overwrite a completed shard"
    stage.rename(path)
    return meta
