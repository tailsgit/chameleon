"""Geometric quality score for resize() outputs (no rendering, except the
optional contrast check).

`score(source, target_canvas, output, contrast=False)` returns
    {"total": 0..100 (higher is better),
     "breakdown": {name: {"penalty": 0..1, "weight": w, "detail": str}}}
with total = 100 * (1 - sum(w * penalty) / sum(w)).

Each penalty is one function below, registered in PENALTIES with its weight,
so they can be tuned independently. All geometry uses what is actually drawn,
not the raw box: text = its laid-out lines (eval.check.text_layout, which
matches the renderer), contain images = the letterboxed asset area.

Roles are decided from the SOURCE and carried to the output by id:
  background  = element that fills the source canvas (excluded everywhere)
  decoration  = ungrouped shape with effective alpha < 0.5 (excluded everywhere)
  unit        = a group (all members merged) or an ungrouped foreground element
"""

import math
from dataclasses import dataclass
from functools import lru_cache
from itertools import combinations

import numpy as np
from PIL import Image

from eval.check import rotated_bbox, text_layout
from eval.render import ASSETS_DIR
from renderer.converter.colorutil import parse_rgba

# --- tunables -----------------------------------------------------------------
MIN_TEXT_PX_ABS = 12         # never demand less than this (the samples' own fine print is 12px)
MIN_TEXT_REL_HEIGHT = 0.015  # min readable font size as a fraction of canvas height
DECORATION_ALPHA = 0.5
EMPTY_CELL_COVERAGE = 0.02   # a ninth of the canvas with less foreground than this is "empty"
COVERAGE_LOG_RANGE = math.log(3)  # coverage 3x denser or sparser than source = full penalty
NEAR_MISS_REL = 0.02         # edges closer than 2% of the canvas side, but not aligned, are a near miss
ALIGNED_PX = 1.0
CONTRAST_MIN, CONTRAST_MIN_LARGE = 4.5, 3.0  # WCAG AA


@dataclass
class Ctx:
    source: dict
    output: dict
    src: dict          # id -> source element
    out: dict          # id -> output element
    src_box: dict      # id -> drawn box in the source (computed once: text layout is the slow part)
    out_box: dict      # id -> drawn box in the output
    units: list        # list of lists of ids (foreground only)
    sw: float
    sh: float
    tw: float
    th: float


# --- penalties ---------------------------------------------------------------

def overlap_penalty(c: Ctx):
    """New overlaps between foreground units. For each pair, overlap ratio =
    intersection / smaller unit's area. Only the increase over the same
    pair's ratio in the source counts, so designed layering (text on a
    shape, product over a circle) is free. Penalty = sum of increases, capped at 1."""
    total, worst = 0.0, []
    for a, b in combinations(c.units, 2):
        r_src = _overlap_ratio(_unit_box(c.src_box, a), _unit_box(c.src_box, b))
        r_out = _overlap_ratio(_unit_box(c.out_box, a), _unit_box(c.out_box, b))
        if r_out - r_src > 0.01:
            total += r_out - r_src
            worst.append(f"{_name(a)}~{_name(b)} +{r_out - r_src:.2f}")
    return min(1.0, total), ", ".join(worst)


def small_text_penalty(c: Ctx):
    """Text rendered smaller than max(MIN_TEXT_PX_ABS, MIN_TEXT_REL_HEIGHT *
    canvas height), but never demanding more than the element's source size
    (fine print stays fine print). Uses int(font_size), the size the renderer
    actually draws. Penalty = mean relative shortfall over text elements."""
    floor = max(MIN_TEXT_PX_ABS, MIN_TEXT_REL_HEIGHT * c.th)
    shortfalls, small = [], []
    for eid, el in c.out.items():
        if el["type"] != "text":
            continue
        need = min(floor, c.src[eid]["font_size"])
        drawn = int(el["font_size"])
        shortfalls.append(max(0.0, (need - drawn) / need))
        if drawn < need:
            small.append(f"{eid} {drawn}px<{need:.0f}")
    return (sum(shortfalls) / len(shortfalls) if shortfalls else 0.0), ", ".join(small)


def headline_penalty(c: Ctx):
    """The source's largest text (by font size, ties by box area) must stay
    the largest. Penalty = 4 x how much bigger the largest other text is, capped at 1."""
    texts = [e for e in c.src.values() if e["type"] == "text" and e["id"] in c.out]
    if len(texts) < 2:
        return 0.0, ""
    head = max(texts, key=lambda e: (e["font_size"], e["width"] * e["height"]))["id"]
    hfs = int(c.out[head]["font_size"])
    other_id, other_fs = max(((e["id"], int(c.out[e["id"]]["font_size"])) for e in texts if e["id"] != head),
                             key=lambda t: t[1])
    if other_fs <= hfs:
        return 0.0, ""
    return min(1.0, 4 * (other_fs / max(hfs, 1) - 1)), f"{other_id} {other_fs}px > headline {head} {hfs}px"


def space_penalty(c: Ctx):
    """Poor use of space, relative to the source. Half: foreground coverage
    (union of drawn areas / canvas) drifting from the source's coverage, on a
    log scale (crowding and emptiness both count). Half: canvas ninths that
    are empty in the output beyond those empty in the source (3 extra = full)."""
    cov_s, empty_s = _coverage(c.src_box, c.units, c.sw, c.sh)
    cov_o, empty_o = _coverage(c.out_box, c.units, c.tw, c.th)
    p_cov = 0.0 if cov_s == 0 or cov_o == 0 else min(1.0, abs(math.log(cov_o / cov_s)) / COVERAGE_LOG_RANGE)
    if cov_o == 0 and cov_s > 0:
        p_cov = 1.0
    p_empty = min(1.0, max(0, empty_o - empty_s) / 3)
    return 0.5 * p_cov + 0.5 * p_empty, f"coverage {cov_s:.0%}->{cov_o:.0%}, empty ninths {empty_s}->{empty_o}"


def alignment_penalty(c: Ctx):
    """Near-miss alignments: a pair of units whose left/centre/right (or
    top/middle/bottom) differ by more than ALIGNED_PX but less than
    NEAR_MISS_REL of the canvas side, with no exact alignment on that axis.
    Penalty = near misses added over the source, per unit, capped at 1."""
    n_src = _near_misses(c.src_box, c.units, c.sw, c.sh)
    n_out = _near_misses(c.out_box, c.units, c.tw, c.th)
    return min(1.0, max(0, n_out - n_src) / max(1, len(c.units))), f"near misses {n_src}->{n_out}"


def reading_order_penalty(c: Ctx):
    """Reading order = rows top to bottom (a unit joins a row when its
    vertical centre falls inside the row), left to right within a row.
    Penalty = fraction of unit pairs whose order flipped vs the source (Kendall)."""
    src_rank = {tuple(u): i for i, u in enumerate(_reading_order(c.src_box, c.units))}
    out_order = _reading_order(c.out_box, c.units)
    pairs = list(combinations(out_order, 2))
    if not pairs:
        return 0.0, ""
    flipped = [(a, b) for a, b in pairs if src_rank[tuple(a)] > src_rank[tuple(b)]]
    return len(flipped) / len(pairs), ", ".join(f"{_name(a)} now before {_name(b)}" for a, b in flipped[:5])


def contrast_penalty(c: Ctx):
    """(Optional, renders once.) Render the output without its text, then for
    each text element compare its colour (alpha-composited) with the pixels
    under its drawn lines. Contrast = WCAG ratio against the 10th-percentile
    worst pixel. Penalty per element = shortfall below 4.5 (3.0 for >=24px or
    bold >=19px), scaled to 0..1; total = mean."""
    from eval.render import render_image, render_scale

    no_text = {"canvas": c.output["canvas"], "elements": [e for e in c.output["elements"] if e["type"] != "text"]}
    img = np.asarray(render_image(no_text), dtype=np.float64) / 255
    s = render_scale(c.output)
    lum = _rel_luminance(img)
    pens, low = [], []
    for eid, el in c.out.items():
        if el["type"] != "text":
            continue
        x0, y0, x1, y1 = (int(round(v * s)) for v in _drawn_box(el))
        x0, y0 = max(x0, 0), max(y0, 0)
        x1, y1 = min(x1, img.shape[1]), min(y1, img.shape[0])
        if x1 <= x0 or y1 <= y0:
            continue
        r, g, b, a = parse_rgba(el.get("color"))
        bg = img[y0:y1, x0:x1].reshape(-1, 3)
        fg = a * np.array([r, g, b]) / 255 + (1 - a) * bg
        lf, lb = _rel_luminance(fg), lum[y0:y1, x0:x1].reshape(-1)
        ratio = (np.maximum(lf, lb) + 0.05) / (np.minimum(lf, lb) + 0.05)
        worst = float(np.percentile(ratio, 10))
        fs = int(el["font_size"])
        need = CONTRAST_MIN_LARGE if fs >= 24 or (el.get("font_weight") == "bold" and fs >= 19) else CONTRAST_MIN
        pens.append(max(0.0, min(1.0, (need - worst) / (need - 1))))
        if worst < need:
            low.append(f"{eid} {worst:.1f}:1")
    return (sum(pens) / len(pens) if pens else 0.0), ", ".join(low)


PENALTIES = {  # name: (function, weight, needs_render)
    "overlap": (overlap_penalty, 3.0, False),
    "small_text": (small_text_penalty, 3.0, False),
    "headline": (headline_penalty, 1.5, False),
    "space": (space_penalty, 1.5, False),
    "alignment": (alignment_penalty, 1.0, False),
    "reading_order": (reading_order_penalty, 1.0, False),
    "contrast": (contrast_penalty, 2.0, True),
}


def score(source: dict, target_canvas: dict, output: dict, contrast: bool = False) -> dict:
    c = _context(source, target_canvas, output)
    breakdown = {}
    for name, (fn, weight, needs_render) in PENALTIES.items():
        if needs_render and not contrast:
            continue
        p, detail = fn(c)
        breakdown[name] = {"penalty": round(p, 4), "weight": weight, "detail": detail}
    wsum = sum(b["weight"] for b in breakdown.values())
    total = 100 * (1 - sum(b["weight"] * b["penalty"] for b in breakdown.values()) / wsum)
    return {"total": round(total, 2), "breakdown": breakdown}


# --- helpers -----------------------------------------------------------------

def _context(source, target_canvas, output):
    src = {e["id"]: e for e in source["elements"]}
    out = {}
    for e in output["elements"]:  # first occurrence wins; check.py reports duplicates
        if e.get("id") in src and e["id"] not in out:
            out[e["id"]] = e
    sw, sh = source["canvas"]["width"], source["canvas"]["height"]
    fg = [i for i in out if not _is_background(src[i], sw, sh) and not _is_decoration(src[i])]
    groups: dict = {}
    for i in fg:
        groups.setdefault(src[i].get("group_id") or ("__" + i), []).append(i)
    units = list(groups.values())
    return Ctx(source, output, src, out, {i: _drawn_box(src[i]) for u in units for i in u},
               {i: _drawn_box(out[i]) for u in units for i in u}, units, sw, sh,
               target_canvas["width"], target_canvas["height"])


def _is_background(el, cw, ch):
    return el["x"] <= 1 and el["y"] <= 1 and el["x"] + el["width"] >= cw - 1 and el["y"] + el["height"] >= ch - 1


def _is_decoration(el):
    if el["type"] != "shape" or el.get("group_id"):
        return False
    return el.get("opacity", 1) * parse_rgba(el.get("fill_color"))[3] < DECORATION_ALPHA


@lru_cache(maxsize=64)
def _asset_size(asset_id):
    try:
        with Image.open(ASSETS_DIR / asset_id) as im:
            return im.size
    except (OSError, TypeError):
        return None  # missing asset: renderer draws a placeholder filling the box


def _drawn_box(el):
    """Absolute (x0, y0, x1, y1) of what the renderer actually paints."""
    if el.get("rotation", 0):
        return rotated_bbox(el)
    x, y, w, h = el["x"], el["y"], el["width"], el["height"]
    if el["type"] == "text":
        lay = text_layout(el)
        if not lay["lines"]:
            return (x, y, x, y)
        return (x + lay["left"], y, x + lay["right"], y + lay["height"])
    if el["type"] == "image" and el.get("fit", "contain") == "contain" and w > 0 and h > 0:
        size = _asset_size(el.get("asset_id"))
        if size:
            k = min(w / size[0], h / size[1])
            nw, nh = size[0] * k, size[1] * k
            return (x + (w - nw) / 2, y + (h - nh) / 2, x + (w + nw) / 2, y + (h + nh) / 2)
    return (x, y, x + w, y + h)


def _unit_box(boxes_by_id, unit):
    boxes = [boxes_by_id[i] for i in unit]
    return (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))


def _area(b):
    return max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])


def _overlap_ratio(a, b):
    inter = _area((max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])))
    smaller = min(_area(a), _area(b))
    return inter / smaller if smaller > 0 else 0.0


def _coverage(boxes, units, cw, ch, res=192):
    k = res / max(cw, ch)
    gw, gh = max(3, round(cw * k)), max(3, round(ch * k))
    mask = np.zeros((gh, gw), dtype=bool)
    for u in units:
        for i in u:
            x0, y0, x1, y1 = boxes[i]
            mask[max(0, int(y0 * k)):max(0, math.ceil(y1 * k)), max(0, int(x0 * k)):max(0, math.ceil(x1 * k))] = True
    empty = sum(
        mask[r * gh // 3:(r + 1) * gh // 3, q * gw // 3:(q + 1) * gw // 3].mean() < EMPTY_CELL_COVERAGE
        for r in range(3) for q in range(3)
    )
    return float(mask.mean()), int(empty)


def _near_misses(boxes_by_id, units, cw, ch):
    boxes = [_unit_box(boxes_by_id, u) for u in units]
    n = 0
    for a, b in combinations(boxes, 2):
        for axis, dim in ((0, cw), (1, ch)):
            lo, hi = axis, axis + 2
            ds = [abs(a[lo] - b[lo]), abs((a[lo] + a[hi]) - (b[lo] + b[hi])) / 2, abs(a[hi] - b[hi])]
            if min(ds) > ALIGNED_PX and any(d < NEAR_MISS_REL * dim for d in ds):
                n += 1
    return n


def _reading_order(boxes_by_id, units):
    items = sorted(((_unit_box(boxes_by_id, u), u) for u in units), key=lambda t: t[0][1])
    rows = []
    for box, u in items:
        cy = (box[1] + box[3]) / 2
        if rows and rows[-1]["top"] <= cy <= rows[-1]["bottom"]:
            rows[-1]["items"].append((box, u))
            rows[-1]["bottom"] = max(rows[-1]["bottom"], box[3])
        else:
            rows.append({"top": box[1], "bottom": box[3], "items": [(box, u)]})
    return [u for row in rows for _box, u in sorted(row["items"], key=lambda t: t[0][0])]


def _rel_luminance(rgb):
    lin = np.where(rgb <= 0.03928, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    return lin[..., 0] * 0.2126 + lin[..., 1] * 0.7152 + lin[..., 2] * 0.0722


def _name(unit):
    return unit[0] if len(unit) == 1 else "[" + "+".join(unit) + "]"
