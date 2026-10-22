"""Deterministic source perturbations and real-target group correspondence."""

from __future__ import annotations

import copy
import json
import math
import random
from pathlib import Path

from engine.analyze import analyze, full_box
from engine.fit import place_background
from generator.campaigns import hashed
from generator.extract import group_features

REPO = Path(__file__).resolve().parents[1]
METHODS = ("stretch_uniform", "uniform_fit")
JITTER_POSITION = 0.01
JITTER_LOG_SCALE = 0.03


def rng_for(seed: int, *parts: object) -> random.Random:
    return random.Random(int(hashed(":".join(map(str, (seed, *parts)))), 16))


def canvases(key: str, canvas_b: list[int], seed: int) -> list[dict]:
    catalogue = json.loads((REPO / "eval/canvas_catalogue.json").read_text())
    eligible = [c for c in catalogue if [c["width"], c["height"]] != canvas_b]
    rng = rng_for(seed, key, "canvases")
    chosen = rng.sample(eligible, 3)
    aspect = math.exp(rng.uniform(math.log(0.25), math.log(4.0)))
    area = 1080 ** 2
    w, h = round(math.sqrt(area * aspect)), round(math.sqrt(area / aspect))
    w = max(math.ceil(0.25 * h), min(w, 4 * h))
    if [w, h] == canvas_b:
        h += 1
        w = max(math.ceil(0.25 * h), min(w, 4 * h))
    return [dict(c, index=i) for i, c in enumerate([*chosen, {"name": "random_aspect", "width": w, "height": h}])]


def outside_coordinates(box: list[float]) -> bool:
    return any(v < 0 or v > 1 for v in box)


def outside_canvas(box: list[float]) -> bool:
    x, y, w, h = box
    return outside_coordinates(box) or x + w > 1 + 1e-9 or y + h > 1 + 1e-9


def cheap_source(target: dict, groups_b: list[dict], canvas_a: dict, method: str,
                 seed: int, design_hash: str, canvas_index: int) -> dict:
    assert method in METHODS
    bw, bh = target["canvas"]["width"], target["canvas"]["height"]
    aw, ah = canvas_a["width"], canvas_a["height"]
    sx, sy = aw / bw, ah / bh
    scale = min(sx, sy)
    ox, oy = (aw - bw * scale) / 2, (ah - bh * scale) / 2
    source = {"canvas": {"width": aw, "height": ah}, "elements": copy.deepcopy(target["elements"])}
    rng = rng_for(seed, design_hash, canvas_index, method, "jitter")
    for g in groups_b:
        if g["kind"] == "background":
            for index in g["members"]:
                place_background(source["elements"][index], aw, ah, bw, bh)
            continue
        x, y, w, h = g["box"]
        cx, cy = (x + w / 2) * bw, (y + h / 2) * bh
        k = scale * math.exp(rng.uniform(-JITTER_LOG_SCALE, JITTER_LOG_SCALE))
        if method == "stretch_uniform":
            tx, ty = cx * sx, cy * sy
        else:
            tx, ty = ox + cx * scale, oy + cy * scale
        tx += rng.uniform(-JITTER_POSITION, JITTER_POSITION) * aw
        ty += rng.uniform(-JITTER_POSITION, JITTER_POSITION) * ah
        for index in g["members"]:
            original, el = target["elements"][index], source["elements"][index]
            el.update(x=tx + (original["x"] - cx) * k, y=ty + (original["y"] - cy) * k,
                      width=original["width"] * k, height=original["height"] * k)
            if el["type"] == "text":
                el["font_size"] = max(1.0, original["font_size"] * k)
                if "letter_spacing" in el:
                    el["letter_spacing"] = original["letter_spacing"] * k
    assert [e["id"] for e in source["elements"]] == [e["id"] for e in target["elements"]]
    return source


def aligned_targets(target: dict, groups_b: list[dict], source_groups: list[dict]) -> tuple[list[list[float]], list[bool]]:
    """Target boxes are real-B extents of the members of each source-A unit.

    Exact canonical membership reuses the untouched Phase 1 box (including row
    padding). Newly merged/split source groups use unions of the actual B element
    bounds. No target coordinate is clipped, stretched or jittered.
    """
    canonical = {tuple(g["members"]): g["box"] for g in groups_b}
    bw, bh = target["canvas"]["width"], target["canvas"]["height"]
    boxes, changed = [], []
    for g in source_groups:
        members = tuple(g["members"])
        if members in canonical:
            box = list(canonical[members])
            changed.append(False)
        else:
            bounds = [full_box(target["elements"][i]) for i in members]
            x0, y0 = min(b[0] for b in bounds), min(b[1] for b in bounds)
            x1, y1 = max(b[2] for b in bounds), max(b[3] for b in bounds)
            box = [x0 / bw, y0 / bh, (x1 - x0) / bw, (y1 - y0) / bh]
            changed.append(True)
        boxes.append(box)
    assert all(math.isfinite(v) for b in boxes for v in b)
    return boxes, changed


def pair_record(target: dict, cached: dict, source: dict, method: str, canvas_index: int) -> dict:
    assert [e["id"] for e in source["elements"]] == [e["id"] for e in target["elements"]]
    for a, b in zip(source["elements"], target["elements"]):
        assert a.get("content") == b.get("content"), "synthetic source changed text"
        assert a.get("asset_id") == b.get("asset_id"), "synthetic source changed imagery"
    source_groups = group_features(analyze(source))
    boxes, changed = aligned_targets(target, cached["groups"], source_groups)
    return {"design_hash": cached["design_hash"], "campaign_hash": cached["campaign_hash"], "split": cached["split"],
            "raw_shard": cached["raw_shard"], "raw_row": cached["raw_row"], "method": method, "canvas_index": canvas_index,
            "canvas_a": [source["canvas"]["width"], source["canvas"]["height"]], "canvas_b": cached["canvas"],
            "source_groups": source_groups, "target_boxes": boxes, "target_regrouped": changed,
            "target_outside_unit": [outside_coordinates(b) for b in boxes],
            "target_outside_canvas": [outside_canvas(b) for b in boxes],
            "has_outside_target": any(outside_canvas(b) for b in boxes)}
