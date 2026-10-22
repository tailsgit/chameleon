"""Download pinned raw Crello train shards with HTTP resume and SHA256 checks."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pyarrow.parquet as pq
import yaml

REVISION = "7997e2f434ee4aa73cf4cdf22c5954cb175872e1"
BASE = "https://huggingface.co"
DATA = Path("/Volumes/Extreme/AdobeHackathon/data")


def fetch_json(url: str) -> dict | list:
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.load(response)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def download(entry: dict, destination: Path) -> None:
    expected = entry["lfs"]["oid"]
    size = entry["size"]
    if destination.exists():
        assert destination.stat().st_size == size, destination.name
        assert digest(destination) == expected, destination.name
        print(f"verified existing {destination.name}", flush=True)
        return
    partial = destination.with_suffix(".parquet.partial")
    for attempt in range(6):
        offset = partial.stat().st_size if partial.exists() else 0
        assert offset <= size, (partial.name, offset, size)
        if offset == size:
            break
        url = f"{BASE}/datasets/cyberagent/crello/resolve/{REVISION}/{entry['path']}"
        request = urllib.request.Request(url, headers={"Range": f"bytes={offset}-"} if offset else {})
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                if offset:
                    assert response.status == 206, "server did not honor resume"
                    assert response.headers["Content-Range"].startswith(f"bytes {offset}-"), "bad resume range"
                print(f"download {destination.name}: {offset}/{size} bytes (attempt {attempt + 1})", flush=True)
                last = offset
                with partial.open("ab") as stream:
                    while block := response.read(8 << 20):
                        stream.write(block)
                        offset += len(block)
                        if offset - last >= 64 << 20:
                            print(f"  {destination.name}: {offset}/{size}", flush=True)
                            last = offset
            if offset == size:
                break
        except (OSError, TimeoutError) as error:
            print(f"retry {destination.name}: {type(error).__name__}; retained partial", flush=True)
            if attempt == 5:
                raise RuntimeError(f"download failed: {destination.name}") from None
            time.sleep(min(2 ** attempt, 30))
    assert partial.stat().st_size == size, destination.name
    assert digest(partial) == expected, f"SHA256 mismatch: {destination.name}"
    partial.replace(destination)
    print(f"verified {destination.name}: {pq.ParquetFile(destination).metadata.num_rows} rows", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=DATA / "crello_chameleon")
    parser.add_argument("--out", type=Path, default=DATA / "generator" / "download")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    args.raw.mkdir(parents=True, exist_ok=True)
    args.out.mkdir(parents=True, exist_ok=True)
    tree = fetch_json(f"{BASE}/api/datasets/cyberagent/crello/tree/{REVISION}?recursive=true&limit=1000")
    entries = sorted((e for e in tree if e["path"].startswith("data/train-") and e["path"].endswith(".parquet")), key=lambda e: e["path"])
    with urllib.request.urlopen(f"{BASE}/datasets/cyberagent/crello/raw/{REVISION}/README.md", timeout=60) as response:
        card = response.read().decode()
    metadata = yaml.safe_load(card.split("---", 2)[1])
    expected_rows = next(s["num_examples"] for s in metadata["dataset_info"]["splits"] if s["name"] == "train")
    manifest = {"dataset": "cyberagent/crello", "revision": REVISION, "expected_rows": expected_rows,
                "bytes": sum(e["size"] for e in entries), "files": [{"name": Path(e["path"]).name, "bytes": e["size"], "sha256": e["lfs"]["oid"]} for e in entries]}
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"pinned {REVISION}: {len(entries)} shards, {manifest['bytes']} bytes, card expects {expected_rows} rows", flush=True)
    started = time.monotonic()
    def one(entry: dict) -> int:
        path = args.raw / Path(entry["path"]).name
        download(entry, path)
        return pq.ParquetFile(path).metadata.num_rows

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        rows = sum(pool.map(one, entries))
    assert rows == expected_rows, (rows, expected_rows)
    summary = {"rows": rows, "shards": len(entries), "seconds": time.monotonic() - started}
    (args.out / "verified.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(f"PASS: {summary}", flush=True)


if __name__ == "__main__":
    main()
