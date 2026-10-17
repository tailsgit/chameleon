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

import json
import math
from dataclasses import dataclass
from functools import lru_cache
from itertools import combinations

import numpy as np
from PIL import Image

from eval.check import _font_manager, rotated_bbox, text_layout
from eval.render import ASSETS_DIR
from renderer.converter.colorutil import parse_rgba

# --- tunables -----------------------------------------------------------------
MIN_TEXT_PX_ABS = 12         # never demand less than this (the samples' own fine print is 12px)
MIN_TEXT_REL_HEIGHT = 0.015  # min readable font size as a fraction of canvas height
DECORATION_ALPHA = 0.5
EMPTY_CELL_COVERAGE = 0.02   # a ninth of the canvas with less foreground than this is "empty"
EMPTY_NINTHS_FREE = 4        # this many empty ninths of the target are fine (margins, breathing room)
MIN_EXTENT = 0.6             # content should span at least this fraction of the target on each axis
HEADLINE_LEAD = 1.4          # the headline should look at least this much bigger than any other text...
                             # ...unless it led by less in the source
FLOAT_MAX_AREA = 0.1         # a corner-anchored unit smaller than this fraction of the canvas is floating
FLOAT_CORNER = 0.12          # "anchored" = within this fraction of the canvas side from two adjacent edges
FLOAT_DRIFT_FULL = 0.3       # drift from its corner of 30% of the canvas side = full penalty
ATTACH_MIN = 0.15            # a floating unit overlapping a bigger unit by this share of its area is attached to it
TILT_FLIP = 0.5              # a rotated unit whose tilt no longer points the way it did, relative to its anchor
ACCENT_MIN_CHROMA = 30       # CIELAB chroma: neutrals (white, black, greys) never count as colour emphasis
ACCENT_MIN_DELTA = 35        # CIELAB distance from every main-palette colour
MAIN_SHARE = 0.2             # a colour covering this share of the painted area is part of the main palette
SAME_COLOUR = 15             # CIELAB distance under which two colours are one palette entry
FOCUS_OFF_ZONE = 0.25        # emphasised unit's centre this far from its column's centre (x column width) = full penalty
ROW_GAP = 0.1                # side-by-side units closer than this (x canvas width) form one row block
FOCUS_OFF_CANVAS = 0.35      # ...or, alone in its column, this far from the canvas centre (x canvas width)
FOCUS_FREE = 0.05            # off-centre by less than this is centred
GAP_FREE, GAP_FULL = 0.1, 0.3  # an empty band between content: free up to 10% of the side, full penalty at 30%
BALANCE_FULL = 0.25          # content centre this much further off-centre than in the source = full penalty
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
    anchors: dict = None  # tuple(unit) -> None | ("corner", "top-left"...) | ("host", host unit)


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
    """The source's visually biggest text must stay clearly the biggest.
    Visual size = x-height of the drawn font x sqrt(stroke weight / 400), so a
    14px regular serif no longer "beats" a 13px bold sans. Lead = headline's
    visual size / the largest other text's. Needed lead = min(HEADLINE_LEAD,
    source lead); penalty = shortfall from it, 0 at the needed lead, 1 at parity or below."""
    texts = [i for i, e in c.src.items() if e["type"] == "text" and i in c.out]
    if len(texts) < 2:
        return 0.0, ""
    vs = {i: _visual_size(c.src[i]) for i in texts}
    head = max(texts, key=lambda i: (vs[i], c.src[i]["width"] * c.src[i]["height"]))
    need = min(HEADLINE_LEAD, vs[head] / max(max(v for i, v in vs.items() if i != head), 1e-6))
    if need <= 1:
        return 0.0, ""
    vo = {i: _visual_size(c.out[i]) for i in texts}
    other = max((i for i in texts if i != head), key=vo.get)
    lead = vo[head] / max(vo[other], 1e-6)
    p = min(1.0, max(0.0, (need - lead) / (need - 1)))
    return p, (f"headline {head} leads {other} by {lead:.2f}x (needs {need:.2f}x)" if p else "")


def space_penalty(c: Ctx):
    """Unused target canvas, regardless of how sparse the source was:
    - extent (half): the content's bounding box should span MIN_EXTENT of the
      target on each axis (mean shortfall);
    - gap (quarter): the widest empty band running right across the content
      (a hole between a split layout's halves), beyond GAP_FREE of that side;
    - empty ninths (quarter): ninths of the target with no content, beyond EMPTY_NINTHS_FREE."""
    box = _content_box(c.out_box, c.units)
    if box is None:
        return 0.0, ""
    fx, fy = (box[2] - box[0]) / c.tw, (box[3] - box[1]) / c.th
    p_ext = (max(0.0, MIN_EXTENT - fx) + max(0.0, MIN_EXTENT - fy)) / (2 * MIN_EXTENT)
    boxes = [_unit_box(c.out_box, u) for u in c.units]
    gap = max(_widest_gap([(b[0], b[2]) for b in boxes]) / c.tw, _widest_gap([(b[1], b[3]) for b in boxes]) / c.th)
    p_gap = min(1.0, max(0.0, gap - GAP_FREE) / (GAP_FULL - GAP_FREE))
    _cov, empty = _coverage(c.out_box, c.units, c.tw, c.th)
    p_empty = max(0, empty - EMPTY_NINTHS_FREE) / (9 - EMPTY_NINTHS_FREE)
    return (0.5 * p_ext + 0.25 * p_gap + 0.25 * p_empty,
            f"content spans {fx:.0%} x {fy:.0%} of the canvas, widest inner gap {gap:.0%}, empty ninths {empty}")


def balance_penalty(c: Ctx):
    """Content huddled to one side: how much further the content box's centre
    sits from the canvas centre (as a fraction of each side, worst axis) than
    it did in the source. BALANCE_FULL more = full penalty."""
    bs, bo = _content_box(c.src_box, c.units), _content_box(c.out_box, c.units)
    if bs is None or bo is None:
        return 0.0, ""
    def off(b, w, h):
        return max(abs((b[0] + b[2]) / 2 / w - 0.5), abs((b[1] + b[3]) / 2 / h - 0.5))
    o_s, o_o = off(bs, c.sw, c.sh), off(bo, c.tw, c.th)
    return min(1.0, max(0.0, o_o - o_s) / BALANCE_FULL), f"centre offset {o_s:.0%}->{o_o:.0%}"


def floating_penalty(c: Ctx):
    """Floating elements (badges, ribbons, stamps) belong where they were
    anchored (see _float_anchor): either to another unit they partly cover (a
    ribbon across a card) or to a canvas corner.
    - Attached: drift = change of its centre's position inside the host's box,
      as fractions of the host's sides.
    - Corner: drift = change in its gaps to that corner's two edges, as
      fractions of the canvas sides.
    Per unit: drift / FLOAT_DRIFT_FULL, plus TILT_FLIP when a rotated unit's
    tilt no longer points the way it did relative to its anchor (it moved to
    the mirrored side without its angle being mirrored, or the reverse).
    Penalty = mean over floating units, each capped at 1."""
    pens, notes = [], []
    for u in c.units:
        anchor = c.anchors[tuple(u)]
        if anchor is None:
            continue
        kind, ref = anchor
        if kind == "host":
            gs, go = _rel_pos(c.src_box, u, ref), _rel_pos(c.out_box, u, ref)
            where = f"its place on {_name(ref)}"
        else:
            gs = _corner_gaps(_unit_box(c.src_box, u), ref, c.sw, c.sh)
            go = _corner_gaps(_unit_box(c.out_box, u), ref, c.tw, c.th)
            where = ref
        d = abs(go[0] - gs[0]) + abs(go[1] - gs[1])
        p = d / FLOAT_DRIFT_FULL
        if d > 0.05:
            notes.append(f"{_name(u)} drifted {d:.0%} from {where}")
        if _tilt_wrong(c, u, anchor):
            p += TILT_FLIP
            notes.append(f"{_name(u)} tilts the wrong way")
        pens.append(min(1.0, p))
    return (sum(pens) / len(pens) if pens else 0.0), ", ".join(notes)


def emphasis_penalty(c: Ctx):
    """Units that stand out by colour (see `emphasis`) belong in a focal
    position: the end of the reading path (last in row or column order), or
    the centre of their column (the units stacked above or below them). A
    row of side-by-side units (a row of badges) is judged as one block. Alone
    in its column, a unit is judged against the canvas centre instead.
    Floating units are judged by floating_penalty. Penalty = off-focus amount,
    averaged with each unit's emphasis strength as weight."""
    sal = emphasis(c.source)
    units = [u for u in c.units if c.anchors[tuple(u)] is None]
    if not units:
        return 0.0, ""
    last = {tuple(_reading_order(c.out_box, units)[-1]), tuple(_reading_order(c.out_box, units, columns=True)[-1])}
    boxes = {tuple(u): _unit_box(c.out_box, u) for u in units}
    num = den = 0.0
    off = []
    for u in units:
        w = max(sal.get(i, 0.0) for i in u)
        if w == 0 or tuple(u) in last:
            continue
        row = _row_block(boxes, tuple(u), ROW_GAP * c.tw)
        b = _content_box(boxes, [[k] for k in row])
        cx = (b[0] + b[2]) / 2
        col = [boxes[k] for k in boxes if k not in row and min(b[2], boxes[k][2]) > max(b[0], boxes[k][0])]
        if col:
            z = _content_box({0: b, **{k + 1: v for k, v in enumerate(col)}}, [[k] for k in range(len(col) + 1)])
            rel, full = abs(cx - (z[0] + z[2]) / 2) / max(z[2] - z[0], 1e-6), FOCUS_OFF_ZONE
        else:
            rel, full = abs(cx - c.tw / 2) / c.tw, FOCUS_OFF_CANVAS
        p = min(1.0, max(0.0, rel - FOCUS_FREE) / (full - FOCUS_FREE))
        num, den = num + w * p, den + w
        if p > 0.2:
            off.append(f"{_name(u)} off-focus {p:.2f}")
    return (num / den if den else 0.0), ", ".join(off)


def alignment_penalty(c: Ctx):
    """Half: near-miss alignments, i.e. a pair of units whose left/centre/right
    (or top/middle/bottom) differ by more than ALIGNED_PX but less than
    NEAR_MISS_REL of the canvas side, with no exact alignment on that axis;
    near misses added over the source, per unit, capped at 1. Half: lost
    alignments, i.e. pairs aligned in the source (a row of badges, a centred
    stack) that share no edge or centre on either axis in the output; as a
    share of the source's aligned pairs (a row may become a column)."""
    n_src = _near_misses(c.src_box, c.units, c.sw, c.sh)
    n_out = _near_misses(c.out_box, c.units, c.tw, c.th)
    p_near = min(1.0, max(0, n_out - n_src) / max(1, len(c.units)))
    aligned = [(a, b) for a, b in combinations(c.units, 2)
               if _aligned(_unit_box(c.src_box, a), _unit_box(c.src_box, b))]
    lost = [(a, b) for a, b in aligned if not _aligned(_unit_box(c.out_box, a), _unit_box(c.out_box, b))]
    p_lost = len(lost) / len(aligned) if aligned else 0.0
    return 0.5 * p_near + 0.5 * p_lost, (f"near misses {n_src}->{n_out}, lost alignments {len(lost)}/{len(aligned)}"
                                         + "".join(f", {_name(a)}|{_name(b)}" for a, b in lost[:4]))


def reading_order_penalty(c: Ctx):
    """Source reading order = rows top to bottom (a unit joins a row when its
    vertical centre falls inside the row), left to right within a row. The
    output may be read either that way or column by column (a unit joins a
    column when its horizontal centre falls inside it; columns left to right,
    top to bottom within one), so a side-by-side layout that reads correctly
    down each column is not punished. Floating units are judged by
    floating_penalty instead. Penalty = fraction of unit pairs whose order
    flipped vs the source (Kendall), under the better of the two readings."""
    units = [u for u in c.units if c.anchors[tuple(u)] is None]
    src_rank = {tuple(u): i for i, u in enumerate(_reading_order(c.src_box, units))}
    best = None
    for order in (_reading_order(c.out_box, units), _reading_order(c.out_box, units, columns=True)):
        pairs = list(combinations(order, 2))
        if not pairs:
            return 0.0, ""
        flipped = [(a, b) for a, b in pairs if src_rank[tuple(a)] > src_rank[tuple(b)]]
        if best is None or len(flipped) < len(best[0]):
            best = flipped, len(pairs)
    flipped, n = best
    return len(flipped) / n, ", ".join(f"{_name(a)} now before {_name(b)}" for a, b in flipped[:5])


def contrast_penalty(c: Ctx):
    """(Optional, renders twice.) Render the design without its text, then for
    each text element compare its colour (alpha-composited) with the pixels
    under its drawn lines. Contrast = WCAG ratio against the 10th-percentile
    worst pixel. Only contrast the layout lost counts: the bar is 4.5 (3.0 for
    >=24px or bold >=19px), or the element's contrast in the source if that
    was already lower (white on the brand's orange badge is the designer's
    choice, not ours). Penalty per element = shortfall below the bar, scaled to 0..1; total = mean."""
    src_ratio = _contrast_ratios(json.dumps(c.source, sort_keys=True))
    pens, low = [], []
    for eid, worst in _contrast_ratios(json.dumps(c.output, sort_keys=True)).items():
        el = c.out[eid]
        fs = int(el["font_size"])
        need = CONTRAST_MIN_LARGE if fs >= 24 or (el.get("font_weight") == "bold" and fs >= 19) else CONTRAST_MIN
        need = min(need, src_ratio.get(eid, need))
        pens.append(max(0.0, min(1.0, (need - worst) / max(need - 1, 1e-6))))
        if worst < need:
            low.append(f"{eid} {worst:.1f}:1 (source {src_ratio.get(eid, float('nan')):.1f}:1)")
    return (sum(pens) / len(pens) if pens else 0.0), ", ".join(low)


@lru_cache(maxsize=8)  # the engine scores many candidates against one source: render it once
def _contrast_ratios(design_json):
    """{text id: 10th-percentile WCAG ratio of its colour against what is drawn under its lines}."""
    from eval.render import render_image, render_scale

    design = json.loads(design_json)
    no_text = {"canvas": design["canvas"], "elements": [e for e in design["elements"] if e["type"] != "text"]}
    img = np.asarray(render_image(no_text), dtype=np.float64) / 255
    s = render_scale(design)
    lum = _rel_luminance(img)
    out = {}
    for el in design["elements"]:
        if el["type"] != "text" or el.get("id") in out:
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
        out[el["id"]] = float(np.percentile(ratio, 10))
    return out


PENALTIES = {  # name: (function, weight, needs_render). Weights fitted to the hand labels: python -m eval.calibrate --fit
    "overlap": (overlap_penalty, 0.5, False),
    "small_text": (small_text_penalty, 1.5, False),
    "headline": (headline_penalty, 1.2, False),
    "space": (space_penalty, 2.6, False),
    "balance": (balance_penalty, 1.5, False),
    "floating": (floating_penalty, 1.2, False),
    "emphasis": (emphasis_penalty, 1.0, False),  # fit leaves it at the floor (labels predate it); kept by request
    "alignment": (alignment_penalty, 0.5, False),
    "reading_order": (reading_order_penalty, 0.5, False),
    "contrast": (contrast_penalty, 0.5, True),
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
    c = Ctx(source, output, src, out, {i: _drawn_box(src[i]) for u in units for i in u},
            {i: _drawn_box(out[i]) for u in units for i in u}, units, sw, sh,
            target_canvas["width"], target_canvas["height"])
    c.anchors = {tuple(u): _float_anchor(c, u) for u in units}
    return c


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


def _reading_order(boxes_by_id, units, columns=False):
    """Rows top to bottom, left to right within a row; or with columns=True,
    the same with the axes swapped."""
    lo, hi = (0, 2) if columns else (1, 3)
    items = sorted(((_unit_box(boxes_by_id, u), u) for u in units), key=lambda t: t[0][lo])
    rows = []
    for box, u in items:
        mid = (box[lo] + box[hi]) / 2
        if rows and rows[-1]["top"] <= mid <= rows[-1]["bottom"]:
            rows[-1]["items"].append((box, u))
            rows[-1]["bottom"] = max(rows[-1]["bottom"], box[hi])
        else:
            rows.append({"top": box[lo], "bottom": box[hi], "items": [(box, u)]})
    return [u for row in rows for _box, u in sorted(row["items"], key=lambda t: t[0][1 - lo])]


def _aligned(a, b):
    """Share a left, centre or right edge, or a top, middle or bottom edge (within ALIGNED_PX)."""
    return any(abs(a[lo] - b[lo]) <= ALIGNED_PX or abs(a[hi] - b[hi]) <= ALIGNED_PX
               or abs((a[lo] + a[hi]) - (b[lo] + b[hi])) / 2 <= ALIGNED_PX for lo, hi in ((0, 2), (1, 3)))


def _widest_gap(spans):
    """Widest stretch between the first start and the last end that no span covers."""
    spans = sorted(spans)
    gap, reach = 0.0, spans[0][1] if spans else 0.0
    for lo, hi in spans[1:]:
        gap = max(gap, lo - reach)
        reach = max(reach, hi)
    return gap


def _content_box(boxes_by_id, units):
    boxes = [_unit_box(boxes_by_id, u) for u in units]
    if not boxes:
        return None
    return (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))


def _float_anchor(c, unit):
    """What a floating unit is pinned to in the source, or None if it isn't floating.
    Small units only (< FLOAT_MAX_AREA of the canvas). Attached: it covers
    ATTACH_MIN..90% of a bigger unit (more is plain layering) or covers any of
    it while rotated -> ("host", that unit). Otherwise rotated, or within
    FLOAT_CORNER of two adjacent edges -> ("corner", "top-left" etc.)."""
    b = _unit_box(c.src_box, unit)
    if _area(b) >= FLOAT_MAX_AREA * c.sw * c.sh:
        return None
    rotated = any(c.src[i].get("rotation", 0) for i in unit)
    best, share = None, 0.0
    for v in c.units:
        vb = _unit_box(c.src_box, v)
        if v is unit or _area(vb) <= _area(b):
            continue
        r = _area((max(b[0], vb[0]), max(b[1], vb[1]), min(b[2], vb[2]), min(b[3], vb[3]))) / max(_area(b), 1e-9)
        if r > share:
            best, share = v, r
    if best is not None and share >= ATTACH_MIN and (share < 0.9 or rotated):
        return ("host", best)
    left, right = b[0] <= FLOAT_CORNER * c.sw, b[2] >= (1 - FLOAT_CORNER) * c.sw
    top, bottom = b[1] <= FLOAT_CORNER * c.sh, b[3] >= (1 - FLOAT_CORNER) * c.sh
    if left == right or top == bottom:  # spans the canvas, or not at an edge: only a rotated unit floats
        if not rotated:
            return None
        cx, cy = (b[0] + b[2]) / 2 / c.sw, (b[1] + b[3]) / 2 / c.sh
        left, top = cx < 0.5, cy < 0.5
    return ("corner", ("top" if top else "bottom") + "-" + ("left" if left else "right"))


def _row_block(boxes, key, max_gap):
    """`key` plus every unit reachable through side-by-side neighbours: vertical
    centre inside the other's span, not overlapping horizontally, gap under max_gap."""
    block, todo = {key}, [key]
    while todo:
        a = boxes[todo.pop()]
        for k, b in boxes.items():
            if k in block:
                continue
            same_row = a[1] <= (b[1] + b[3]) / 2 <= a[3] or b[1] <= (a[1] + a[3]) / 2 <= b[3]
            gap = max(a[0], b[0]) - min(a[2], b[2])  # negative = they overlap horizontally: stacked, not side by side
            if same_row and -ALIGNED_PX <= gap < max_gap:
                block.add(k)
                todo.append(k)
    return block


def _rel_pos(boxes, unit, host):
    """Centre of `unit` as a fraction of `host`'s box."""
    b, h = _unit_box(boxes, unit), _unit_box(boxes, host)
    return (((b[0] + b[2]) / 2 - h[0]) / max(h[2] - h[0], 1e-6), ((b[1] + b[3]) / 2 - h[1]) / max(h[3] - h[1], 1e-6))


def _side(b, ref):
    """Which side of the point `ref` the centre of box b is on: (+-1, +-1)."""
    return (1 if (b[0] + b[2]) / 2 >= ref[0] else -1, 1 if (b[1] + b[3]) / 2 >= ref[1] else -1)


def _tilt_wrong(c, unit, anchor):
    """A rotated unit should keep its source angle, negated exactly when it moved to the
    mirrored side of its anchor on one axis (mirroring on both is a half-turn: same angle)."""
    rot = [i for i in unit if c.src[i].get("rotation", 0)]
    if not rot:
        return False
    def centre(boxes, w, h):
        if anchor[0] == "host":
            hb = _unit_box(boxes, anchor[1])
            return ((hb[0] + hb[2]) / 2, (hb[1] + hb[3]) / 2)
        return (w / 2, h / 2)
    ss = _side(_unit_box(c.src_box, unit), centre(c.src_box, c.sw, c.sh))
    so = _side(_unit_box(c.out_box, unit), centre(c.out_box, c.tw, c.th))
    flip = ss[0] * so[0] * ss[1] * so[1]
    i = rot[0]
    return math.copysign(1, c.out[i].get("rotation", 0) or 0.0) != math.copysign(1, c.src[i]["rotation"]) * flip


@lru_cache(maxsize=32)
def _emphasis_cached(source_json):
    source = json.loads(source_json)
    cw, ch = source["canvas"]["width"], source["canvas"]["height"]
    painted = []  # (lab colour, area)
    own = {}      # element id -> lab colour
    for el in source["elements"]:
        b = _drawn_box(el)
        area = _area((max(b[0], 0), max(b[1], 0), min(b[2], cw), min(b[3], ch)))
        if el["type"] == "image":
            rgb = _asset_mean_rgb(el.get("asset_id"))
            if rgb is not None:
                painted.append((_lab(rgb), area))
            continue
        r, g, bl, a = parse_rgba(el.get("color") if el["type"] == "text" else el.get("fill_color"))
        a *= el.get("opacity", 1)
        if a < DECORATION_ALPHA:
            continue
        lab = _lab((r, g, bl))
        own[el["id"]] = lab
        painted.append((lab, area * (0.3 if el["type"] == "text" else 1.0) * a))  # text: roughly its ink
    palette = []  # [lab, area], greedy clusters
    for lab, area in sorted(painted, key=lambda t: -t[1]):
        hit = next((p for p in palette if _delta(p[0], lab) < SAME_COLOUR), None)
        if hit:
            hit[1] += area
        else:
            palette.append([lab, area])
    total = sum(p[1] for p in palette) or 1.0
    main = [p[0] for p in palette if p[1] / total >= MAIN_SHARE]
    out = {}
    for i, lab in own.items():
        chroma = math.hypot(lab[1], lab[2])
        share = sum(p[1] for p in palette if _delta(p[0], lab) < SAME_COLOUR) / total
        d = min((_delta(lab, m) for m in main), default=0.0)
        if chroma >= ACCENT_MIN_CHROMA and d >= ACCENT_MIN_DELTA and share < MAIN_SHARE:
            out[i] = round(min(1.0, d / 70), 3)
    return out


def emphasis(source):
    """{element id: 0..1} for elements whose own colour (text colour, shape fill)
    stands out from the design's main palette: saturated (CIELAB chroma >=
    ACCENT_MIN_CHROMA), at least ACCENT_MIN_DELTA from every colour that covers
    MAIN_SHARE of the painted area, and not itself that common. Images count
    towards the palette (by their mean colour) but are never emphasised by colour.
    Strength = distance from the nearest main colour / 70, capped at 1."""
    return _emphasis_cached(json.dumps(source, sort_keys=True))


@lru_cache(maxsize=64)
def _asset_mean_rgb(asset_id):
    try:
        with Image.open(ASSETS_DIR / asset_id) as im:
            im = im.convert("RGBA").resize((32, 32))
            px = np.asarray(im, dtype=np.float64)
    except (OSError, TypeError, ValueError):
        return None
    a = px[..., 3:] / 255
    if a.sum() == 0:
        return None
    return tuple(float(v) for v in (px[..., :3] * a).sum((0, 1)) / a.sum())


def _lab(rgb):
    """sRGB 0..255 -> CIELAB (D65)."""
    c = np.asarray(rgb, dtype=np.float64) / 255
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    x, y, z = (np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]]) @ c
               / np.array([0.95047, 1.0, 1.08883]))
    f = lambda t: t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    return (116 * f(y) - 16, 500 * (f(x) - f(y)), 200 * (f(y) - f(z)))


def _delta(a, b):
    return math.dist(a, b)


def _corner_gaps(b, corner, w, h):
    gx = b[0] / w if corner.endswith("left") else (w - b[2]) / w
    gy = b[1] / h if corner.startswith("top") else (h - b[3]) / h
    return gx, gy


@lru_cache(maxsize=256)
def _font_metrics(family, bold, size):
    import skia
    style = "bold" if bold else "regular"
    tf = skia.Typeface.MakeFromData(_font_manager().lookup(family, style, style))
    return skia.Font(tf, size).getMetrics().fXHeight, tf.fontStyle().weight()


def _visual_size(el):
    """How big a text looks: x-height at the size the renderer draws, times sqrt(weight / 400)."""
    xh, weight = _font_metrics(el["font_family"], el.get("font_weight") == "bold", int(el["font_size"]))
    return xh * math.sqrt(max(weight, 100) / 400)


def _rel_luminance(rgb):
    lin = np.where(rgb <= 0.03928, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    return lin[..., 0] * 0.2126 + lin[..., 1] * 0.7152 + lin[..., 2] * 0.0722


def _name(unit):
    return unit[0] if len(unit) == 1 else "[" + "+".join(unit) + "]"
