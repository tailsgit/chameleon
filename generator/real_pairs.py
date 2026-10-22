"""Build one directed real example per inferred unordered cross-format candidate."""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import logging
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

from engine.analyze import analyze
from eval.crello_convert import convert
from generator.campaigns import hashed
from generator.download import digest
from generator.extract import group_features
from generator.make_data import atomic_json
from generator.match_real import IMAGE_ASPECT_RATIO_LIMIT, descriptors, match, text_hash
from generator.pair_data import PHASE2, cached_rows, raw_rows
from generator.pair_geometry import outside_canvas, outside_coordinates
from generator.phase2b import ROOT, publish, verified
from generator.transient import render_assets


def candidates() -> tuple[dict[str, dict], list[tuple[str, str]]]:
    cached = {(r["raw_shard"], r["raw_row"]): r for r in cached_rows() if len(r["groups"]) >= 2}
    by_key = defaultdict(list)
    records = {}
    for shard in range(31):
        for index, raw, _fonts, _formats in raw_rows(shard, ["id", "type", "text", "format"]):
            if (row := cached.get((shard, index))) is None:
                continue
            assert row["design_hash"] == hashed(str(raw["id"]))
            key = (row["split"], row["campaign_hash"], tuple(raw["type"]),
                   tuple(text_hash(t or "") for kind, t in zip(raw["type"], raw["text"]) if kind == 1))
            by_key[key].append((row["design_hash"], raw["format"]))
            records[row["design_hash"]] = {"cached": row, "format": raw["format"]}
    pairs = sorted((a, b) for values in by_key.values() for (a, fa), (b, fb) in combinations(sorted(values), 2) if fa != fb)
    assert len(pairs) == len(set(pairs))
    expected = json.loads((PHASE2 / "plan_summary.json").read_text())["exact_full_text_structure_cross_format_pairs_unordered"]
    assert dict(Counter(records[a]["cached"]["split"] for a, _b in pairs)) == expected
    needed = {h for pair in pairs for h in pair}
    return {h: r for h, r in records.items() if h in needed}, pairs


def prepare_descriptors(root: Path, records: dict, identity: dict) -> dict:
    (root / "real_descriptors").mkdir(parents=True, exist_ok=True)
    by_locator = {(r["cached"]["raw_shard"], r["cached"]["raw_row"]): h for h, r in records.items()}
    for shard in range(31):
        path = root / "real_descriptors" / f"shard_{shard:05d}.json"
        if path.exists():
            cached = json.loads(path.read_text())
            assert cached["identity"] == identity
            for h, keys in cached["group_keys"].items():
                records[h]["group_keys"] = keys
            continue
        keys = {}
        for index, raw, fonts, formats in raw_rows(shard):
            if (h := by_locator.get((shard, index))) is None:
                continue
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                design, _meta, images = convert(raw, fonts, formats)
                try:
                    with render_assets(images):
                        assert group_features(analyze(design)) == records[h]["cached"]["groups"]
                        keys[h] = descriptors(design, records[h]["cached"]["groups"])
                finally:
                    for image in images.values():
                        image.close()
            records[h]["group_keys"] = keys[h]
        assert not path.exists()
        atomic_json(path, {"identity": identity, "group_keys": keys})
        print(f"real descriptors shard {shard:02d}: {len(keys)} designs", flush=True)
    return records


def real_pair(left: dict, right: dict, mapping: list[int]) -> dict:
    a, b = left["cached"], right["cached"]
    assert a["split"] == b["split"] and a["campaign_hash"] == b["campaign_hash"]
    assert len(mapping) == len(a["groups"]) == len(b["groups"]) and sorted(mapping) == list(range(len(mapping)))
    boxes = [b["groups"][j]["box"] for j in mapping]
    return {"design_hash": b["design_hash"], "source_design_hash": a["design_hash"],
            "campaign_hash": b["campaign_hash"], "split": b["split"], "raw_shard": b["raw_shard"], "raw_row": b["raw_row"],
            "method": "real", "source_kind": "real", "canvas_index": -1, "canvas_a": a["canvas"], "canvas_b": b["canvas"],
            "source_groups": a["groups"], "target_boxes": boxes, "target_group_indices": mapping,
            "target_regrouped": [False] * len(boxes), "target_outside_unit": [outside_coordinates(box) for box in boxes],
            "target_outside_canvas": [outside_canvas(box) for box in boxes], "has_outside_target": any(outside_canvas(box) for box in boxes)}


def examples(rows: list[dict]) -> str:
    lines = ["Ten real correspondences; boxes are normalized (x, y, w, h).", ""]
    # Prefer different campaigns so the ten tables show varied correspondence.
    selected, campaigns = [], set()
    for row in sorted(rows, key=lambda r: (r["campaign_hash"], r["source_design_hash"], r["design_hash"])):
        if row["campaign_hash"] not in campaigns:
            selected.append(row); campaigns.add(row["campaign_hash"])
        if len(selected) == 10:
            break
    if len(selected) < 10:
        selected.extend(r for r in rows if r not in selected)
        selected = selected[:10]
    for i, row in enumerate(selected, 1):
        lines.extend([f"Example {i}: {row['split']}, {row['canvas_a']} → {row['canvas_b']}", "",
                      "| Group type / role | Source box | Target box |", "|---|---|---|"])
        for g, box in zip(row["source_groups"], row["target_boxes"]):
            fmt = lambda b: "(" + ", ".join(f"{v:.4f}" for v in b) + ")"
            lines.append(f"| {g['kind']} / {g['role']} | {fmt(g['box'])} | {fmt(box)} |")
        lines.append("")
    return "\n".join(lines)


def run(root: Path) -> None:
    logging.disable(logging.CRITICAL)
    identity = {"seed": 2026, "builder": digest(Path(__file__)),
                "matcher": digest(Path(__file__).with_name("match_real.py")), "image_aspect_ratio_limit": IMAGE_ASPECT_RATIO_LIMIT}
    records, pairs = candidates()
    records = prepare_descriptors(root, records, identity)
    total, compatible, retained = Counter(), Counter(), Counter()
    reasons, splits = Counter(), Counter()
    shards = defaultdict(list)
    for a, b in pairs:
        left, right = records[a], records[b]
        mapping, reason, stats = match(left, right)
        total.update(stats["total"]); compatible.update(stats["compatible"])
        reasons[reason] += 1
        if mapping is None:
            continue
        pair = real_pair(left, right, mapping)
        retained.update(stats["total"])
        splits[pair["split"]] += 1
        shards[pair["raw_shard"]].append(pair)
    all_rows = []
    for shard in range(31):
        path = root / "real" / f"shard_{shard:05d}"
        rows = shards[shard]
        shard_identity = dict(identity, shard=shard)
        if (meta := verified(path, shard_identity)) is not None:
            assert meta["rows"] == len(rows)
        else:
            publish(path, rows, shard_identity)
        all_rows.extend(rows)
    result = {"candidate_pairs": len(pairs), "candidate_pairs_by_split": dict(Counter(records[a]["cached"]["split"] for a, b in pairs)),
              "clean_pairs": dict(splits), "reasons": dict(reasons), "one_direction_per_unordered_pair": True,
              "same_canvas_survivors": sum(r["canvas_a"] == r["canvas_b"] for r in all_rows),
              "roles": {role: {"total_groups": n, "compatible_groups": compatible[role], "retained_groups": retained[role],
                                 "compatible_rate": compatible[role] / n, "retained_rate": retained[role] / n} for role, n in sorted(total.items())}}
    atomic_json(root / "real_summary.json", result)
    (root / "matched_examples.md").write_text(examples(all_rows))
    print("PASS: real matching", json.dumps(result, sort_keys=True), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    run(parser.parse_args().root)
