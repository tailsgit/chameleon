"""Sanitized numeric group features and a memory-mapped Phase 3 dataset."""
from __future__ import annotations
import json
import math
import shutil
from pathlib import Path
import numpy as np
import pyarrow.parquet as pq
from generator.download import digest
from generator.make_data import DATA, atomic_json
from generator.pair_data import cached_rows, PHASE1
from generator.partial_pairs import ROOT as PARTIAL, bucket, BUCKETS
from generator.phase2b import ROOT as PREVIOUS
from generator.verify_data import verify as verify_leakage

ROOT = DATA / "generator" / "phase3"
RUNS = DATA / "generator" / "runs"
MAX_GROUPS = 40
N_CONT = 16
CONT_NAMES = ["x","y","w","h","log_aspect_div4","log1p_char_count_div8","mean_log_image_aspect_div4",
              "log1p_area_share","z_order_div40","member_count_div40","part_count_div40","cols_div8",
              "floating","text_fraction","image_fraction","shape_fraction"]
KINDS = ["background", "panel", "flow_text", "image", "rigid", "row", "grid"]
ROLES = ["background", "panel", "headline", "subhead", "body", "fineprint", "cta", "hero", "logo", "badge", "decoration"]
SOURCES = ["stretch", "whole_fit", "engine", "real", "real_strict"]

def files() -> list[Path]:
    manifest = json.loads((PREVIOUS / "manifest.json").read_text())
    result = []
    for item in manifest["shards"]:
        if item["path"].startswith("real/"):
            continue
        path = PREVIOUS / item["path"]
        assert digest(path) == item["sha256"]
        result.append(path)
    return result + [PARTIAL / "real_train.parquet", PARTIAL / "real_val.parquet", PARTIAL / "real_strict_val.parquet"]

def continuous(g: dict) -> list[float]:
    types = g["types"]; n = max(len(types), 1)
    images = g["image_aspects"]
    return [*g["box"], math.log(max(g["aspect"], 1e-8)) / 4,
            math.log1p(g["char_count"]) / 8, np.mean(np.log(np.maximum(images, 1e-8))) / 4 if images else 0.,
            math.log1p(max(g["area_share"], 0)), g["z_order"] / 40, n / 40, len(g["parts"]) / 40,
            g["cols"] / 8, float(g["floating"]), *[types.count(t)/n for t in ("text", "image", "shape")]]

def canvases(row: dict) -> list[float]:
    a, b = row["canvas_a"], row["canvas_b"]
    return [math.log(a[0]/1080), math.log(a[1]/1080), math.log(b[0]/1080), math.log(b[1]/1080),
            math.log((b[0]/b[1])/(a[0]/a[1]))]

def prepare() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    paths = files(); fingerprints = {str(p): digest(p) for p in paths}
    dest = ROOT / "features"
    if dest.exists():
        assert json.loads((dest / "metadata.json").read_text())["inputs"] == fingerprints
        print("PASS: existing feature cache input hashes unchanged", flush=True); return
    leakage = verify_leakage(PHASE1)
    original = {r["design_hash"]: r for r in cached_rows()}
    n = sum(pq.ParquetFile(p).metadata.num_rows for p in paths)
    stage = ROOT / "features.partial"
    if stage.exists(): shutil.rmtree(stage)
    stage.mkdir()
    specifications = {"cont": ((n, MAX_GROUPS, N_CONT), np.float32), "cat": ((n, MAX_GROUPS, 2), np.int64),
        "valid": ((n, MAX_GROUPS), np.float32), "matched": ((n, MAX_GROUPS), np.float32),
        "target": ((n, MAX_GROUPS, 4), np.float32), "canvas": ((n, 5), np.float32),
        "size": ((n, 4), np.int32), "source": ((n,), np.int64), "split": ((n,), np.int8), "bucket": ((n,), np.int8)}
    arrays = {key: np.lib.format.open_memmap(stage / (key+".npy"), mode="w+", dtype=dtype, shape=shape) for key,(shape,dtype) in specifications.items()}
    for arr in arrays.values(): arr[:] = 0
    index = 0; counts = {}
    for path in paths:
        for batch in pq.ParquetFile(path).iter_batches(batch_size=32):
            for row in batch.to_pylist():
                a, b = original[row["source_design_hash"]], original[row["design_hash"]]
                assert a["split"] == b["split"] == row["split"]
                assert a["campaign_hash"] == b["campaign_hash"] == row["campaign_hash"]
                groups = row["source_groups"]; g = len(groups); assert 2 <= g <= MAX_GROUPS
                mask = row.get("matched", [True]*g)
                assert len(mask) == g and sum(mask) > 0
                if row["source_kind"] in {"real", "real_strict"}:
                    mapping = row["target_group_indices"]
                    js = [j for j,m in zip(mapping,mask) if m]
                    assert len(js) == len(set(js)) and sum(mask)/len(a["groups"]) >= .6 and sum(mask)/len(b["groups"]) >= .6
                    assert groups == a["groups"]
                    for box,j,m in zip(row["target_boxes"],mapping,mask):
                        assert box == b["groups"][j]["box"] if m else j == -1
                arrays["cont"][index,:g] = [continuous(v) for v in groups]
                arrays["cat"][index,:g] = [[KINDS.index(v["kind"]),ROLES.index(v["role"])] for v in groups]
                arrays["valid"][index,:g] = 1
                arrays["matched"][index,:g] = mask
                arrays["target"][index,:g] = row["target_boxes"]
                arrays["canvas"][index] = canvases(row)
                arrays["size"][index] = row["canvas_a"]+row["canvas_b"]
                arrays["source"][index] = SOURCES.index(row["source_kind"])
                arrays["split"][index] = row["split"] == "val"
                arrays["bucket"][index] = BUCKETS.index(bucket(row))
                key = row["source_kind"]+"/"+row["split"]; counts[key] = counts.get(key,0)+1
                index += 1
        print(f"features {index}/{n}",flush=True)
    assert index == n
    for key,arr in arrays.items():
        assert np.isfinite(arr).all(), key
        arr.flush()
    atomic_json(stage / "metadata.json", {"rows": n, "inputs": fingerprints, "seed":2026, "counts":counts, "leakage":leakage,
                                           "continuous_features":N_CONT,"max_groups":MAX_GROUPS})
    stage.rename(dest)
    print("PASS: features",json.dumps(counts),flush=True)

def load() -> dict[str,np.ndarray]:
    return {p.stem:np.load(p,mmap_mode="r") for p in sorted((ROOT/"features").glob("*.npy"))}

if __name__ == "__main__": prepare()
