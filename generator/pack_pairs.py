"""Promote existing cheap pairs without changing any source or target geometry."""
from __future__ import annotations

import argparse
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from generator.download import digest
from generator.pair_data import PHASE2
from generator.phase2b import ROOT, SCHEMA, promote, publish, verified


def run(root: Path) -> None:
    for split in ("train", "val"):
        for source in sorted((PHASE2 / "pairs" / split).glob("*.parquet")):
            destination = root / "cheap" / split / source.stem
            identity = {"seed": 2026, "source_sha256": digest(source), "packer_sha256": digest(Path(__file__)),
                        "storage_sha256": digest(Path(__file__).with_name("phase2b.py"))}
            if verified(destination, identity) is None:
                rows = [promote(r) for r in pq.read_table(source).to_pylist()]
                publish(destination, rows, identity)
            actual = pq.read_table(destination / "pairs.parquet").replace_schema_metadata(None)
            expected = pa.Table.from_pylist([promote(r) for r in pq.read_table(source).to_pylist()], schema=SCHEMA)
            assert actual.equals(expected), "cheap pair promotion changed values"
            print(f"verified source_kind promotion: {split}/{source.stem}", flush=True)
    print("PASS: cheap geometry unchanged; all promoted pairs have source_kind", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    run(parser.parse_args().root)
