"""A design (source + output on its target canvas) as model input for the layout critic.

One token per output element plus one global token (first), padded to MAX_TOKENS:
  cont  float32 [MAX_TOKENS, len(CONT)]  continuous features, named and described in CONT below
  cat   int64   [MAX_TOKENS, 3]          (type, role, group) indices: TYPES, ROLES, group 0..MAX_ELEMENTS
  mask  float32 [MAX_TOKENS]             1 for the global token and real elements, 0 for padding

Roles, groups, panels and reading order come from engine.analyze on the SOURCE (element ids are shared
between source and output), so the critic sees what each element is; boxes come from the output. Boxes
are the element's x, y, width, height (not rotated bounds or laid-out text lines), as canvas fractions.
Elements beyond MAX_ELEMENTS (largest first are kept) are dropped; the converter caps Crello designs at 40.
No torch here: the engine imports this module at run time (engine.critic_score).
"""

import math
import os
from functools import lru_cache

import numpy as np
from PIL import Image

from engine.analyze import analyze

MAX_ELEMENTS = 40
MAX_TOKENS = MAX_ELEMENTS + 1
TYPES = ("pad", "global", "text", "image", "shape")
ROLES = ("none", "background", "decoration", "headline", "subhead", "body", "fineprint", "cta", "hero", "logo", "badge")
ON_PANEL_KEPT = 0.8  # share of an element's output box inside its panel's output box to count as still on it

# (name, description). Element tokens use every row; the global token uses only the rows marked "global:".
CONT = (
    ("x", "output box left / target width"),
    ("y", "output box top / target height"),
    ("w", "output box width / target width"),
    ("h", "output box height / target height"),
    ("src_x", "source box left / source width"),
    ("src_y", "source box top / source height"),
    ("src_w", "source box width / source width"),
    ("src_h", "source box height / source height"),
    ("z", "stacking rank in the output, 0 = bottom, 1 = top"),
    ("rot_sin", "sin(rotation)"),
    ("rot_cos", "cos(rotation)"),
    ("r", "colour red 0-1: text colour, shape fill, or an image's alpha-weighted mean pixel"),
    ("g", "colour green 0-1"),
    ("b", "colour blue 0-1"),
    ("lum", "relative luminance of that colour (WCAG), 0-1"),
    ("alpha", "colour alpha x element opacity (images: mean pixel alpha x opacity)"),
    ("texture", "images: RGB std of the pixels / 128 (photos high, flat cards near 0); else 0"),
    ("font", "text: font size / target height; else 0"),
    ("src_font", "text: source font size / source height; else 0"),
    ("area", "output area / target area"),
    ("src_area", "source area / source area of the canvas"),
    ("read", "reading rank of its unit in the source (engine.analyze rows), 0-1; 0 when it has none"),
    ("has_read", "1 when the element belongs to a unit in reading order"),
    ("contains", "1 when its output box fully contains another element's box"),
    ("inside", "1 when its output box lies fully inside another element's box"),
    ("overlaps", "number of other elements its output box overlaps, / 5, capped at 1"),
    ("on_panel", "1 when it sat on a panel (flat card) in the source"),
    ("panel_kept", "1 when it sat on a panel and is still >= ON_PANEL_KEPT inside that panel's output box"),
    ("off_canvas", "share of its output box outside the target canvas"),
    ("floating", "1 when the analyzer placed its unit as floating (badges, stickers)"),
    ("emphasis", "unit colour emphasis 0-1 (engine.analyze)"),
    ("g_src_aspect", "global: ln(source width / height)"),
    ("g_tgt_aspect", "global: ln(target width / height)"),
    ("g_change", "global: ln(target aspect / source aspect)"),
    ("g_scale", "global: ln(target area / source area) / 4"),
    ("g_count", "global: element count / MAX_ELEMENTS"),
)
CONT_INDEX = {n: k for k, (n, _d) in enumerate(CONT)}
N_CONT = len(CONT)


def encode_design(source, output):
    """Analyse the source, then encode (cont, cat, mask). Use encode() to reuse one analysis."""
    return encode(analyze(source), output)


def encode(a, output):
    cont = np.zeros((MAX_TOKENS, N_CONT), np.float32)
    cat = np.zeros((MAX_TOKENS, 3), np.int64)
    mask = np.zeros(MAX_TOKENS, np.float32)
    tw, th = float(output["canvas"]["width"]), float(output["canvas"]["height"])
    sw, sh = float(a.sw), float(a.sh)
    els = [e for e in output["elements"] if e["id"] in a.els]
    els = sorted(sorted(els, key=lambda e: -e["width"] * e["height"])[:MAX_ELEMENTS], key=lambda e: e.get("z_index", 0))
    info = _source_info(a)

    g = cont[0]
    g[CONT_INDEX["g_src_aspect"]] = math.log(sw / sh)
    g[CONT_INDEX["g_tgt_aspect"]] = math.log(tw / th)
    g[CONT_INDEX["g_change"]] = math.log(tw / th) - math.log(sw / sh)
    g[CONT_INDEX["g_scale"]] = math.log(tw * th / (sw * sh)) / 4
    g[CONT_INDEX["g_count"]] = len(els) / MAX_ELEMENTS
    cat[0, 0], mask[0] = TYPES.index("global"), 1.0

    boxes = np.array([[e["x"], e["y"], e["x"] + e["width"], e["y"] + e["height"]] for e in els], float).reshape(-1, 4)
    rel = _relations(boxes)
    out_box = {e["id"]: b for e, b in zip(els, boxes)}
    n = max(1, len(els) - 1)
    for k, e in enumerate(els):
        t, s, f = k + 1, a.els[e["id"]], cont[k + 1]
        role, group, read, floating, emphasis, panel = info.get(e["id"], ("none", 0, None, False, 0.0, None))
        cat[t] = (TYPES.index(e["type"]) if e["type"] in TYPES else TYPES.index("shape"), ROLES.index(role), group)
        mask[t] = 1.0
        x0, y0, x1, y1 = boxes[k]
        f[0:4] = (x0 / tw, y0 / th, (x1 - x0) / tw, (y1 - y0) / th)
        f[4:8] = (s["x"] / sw, s["y"] / sh, s["width"] / sw, s["height"] / sh)
        f[CONT_INDEX["z"]] = k / n
        rot = math.radians(e.get("rotation", 0) or 0)
        f[CONT_INDEX["rot_sin"]], f[CONT_INDEX["rot_cos"]] = math.sin(rot), math.cos(rot)
        r, gg, b, al, tex = _colour(e)
        f[CONT_INDEX["r"]], f[CONT_INDEX["g"]], f[CONT_INDEX["b"]] = r, gg, b
        f[CONT_INDEX["lum"]] = _luminance(r, gg, b)
        f[CONT_INDEX["alpha"]] = al * float(e.get("opacity", 1.0) if e.get("opacity") is not None else 1.0)
        f[CONT_INDEX["texture"]] = tex
        if e["type"] == "text":
            f[CONT_INDEX["font"]] = e["font_size"] / th
            f[CONT_INDEX["src_font"]] = s["font_size"] / sh
        f[CONT_INDEX["area"]] = (x1 - x0) * (y1 - y0) / (tw * th)
        f[CONT_INDEX["src_area"]] = s["width"] * s["height"] / (sw * sh)
        if read is not None:
            f[CONT_INDEX["read"]], f[CONT_INDEX["has_read"]] = read, 1.0
        f[CONT_INDEX["contains"]], f[CONT_INDEX["inside"]], f[CONT_INDEX["overlaps"]] = rel[k]
        if panel is not None:
            f[CONT_INDEX["on_panel"]] = 1.0
            if panel in out_box:
                f[CONT_INDEX["panel_kept"]] = float(_inside(boxes[k], out_box[panel]) >= ON_PANEL_KEPT)
        vis = max(0.0, min(x1, tw) - max(x0, 0.0)) * max(0.0, min(y1, th) - max(y0, 0.0))
        f[CONT_INDEX["off_canvas"]] = 1 - vis / max((x1 - x0) * (y1 - y0), 1e-9)
        f[CONT_INDEX["floating"]], f[CONT_INDEX["emphasis"]] = float(floating), emphasis
    return cont, cat, mask


def _source_info(a):
    """element id -> (role, group, reading rank 0-1 or None, floating, emphasis, panel id or None)."""
    read = [uid for row in a.rows for uid in row]
    ranks = {uid: k / max(1, len(read) - 1) for k, uid in enumerate(read)}
    order = read + [uid for uid in a.units if uid not in ranks]
    on = {j: p for p, ids in a.panels.items() for j in ids}
    info = {}
    for gid, uid in enumerate(order, start=1):
        u = a.units[uid]
        for m in u.members:
            info[m] = (u.role if u.role in ROLES else "none", min(gid, MAX_ELEMENTS),
                       ranks.get(uid), u.floating, float(u.emphasis), on.get(m))
    gid = len(order)
    for u in a.decorations:
        gid += 1
        for m in u.members:
            info[m] = ("decoration", min(gid, MAX_ELEMENTS), None, False, 0.0, on.get(m))
    for m in a.background:
        info[m] = ("background", 0, None, False, 0.0, None)
    for p in a.panels:  # panels are fitted around their content, outside the units
        info.setdefault(p, ("none", 0, None, False, 0.0, None))
    return info


def _relations(boxes):
    """Per box: (contains another, inside another, overlap count / 5 capped at 1)."""
    if not len(boxes):
        return np.zeros((0, 3))
    x0, y0, x1, y1 = (boxes[:, k][:, None] for k in range(4))
    X0, Y0, X1, Y1 = (boxes[:, k][None, :] for k in range(4))
    contains = (x0 <= X0) & (y0 <= Y0) & (x1 >= X1) & (y1 >= Y1)
    overlap = (np.minimum(x1, X1) > np.maximum(x0, X0)) & (np.minimum(y1, Y1) > np.maximum(y0, Y0))
    np.fill_diagonal(contains, False)
    np.fill_diagonal(overlap, False)
    return np.stack([contains.any(1), contains.any(0), np.minimum(overlap.sum(1) / 5, 1.0)], 1).astype(float)


def _inside(b, ref):
    w = max(0.0, min(b[2], ref[2]) - max(b[0], ref[0]))
    h = max(0.0, min(b[3], ref[3]) - max(b[1], ref[1]))
    return w * h / max((b[2] - b[0]) * (b[3] - b[1]), 1e-9)


def _colour(e):
    """(r, g, b, alpha, texture), each 0-1."""
    if e["type"] == "image":
        return _image_stats(e.get("asset_id", ""))
    r, g, b, al = _rgba(e.get("color") if e["type"] == "text" else e.get("fill_color"))
    return r, g, b, al, 0.0


def _rgba(value):
    from renderer.converter.colorutil import parse_rgba
    r, g, b, al = parse_rgba(value)
    return r / 255, g / 255, b / 255, float(al)


@lru_cache(maxsize=4096)
def _image_stats(asset_id):
    from eval.render import assets_dir
    try:
        im = Image.open(os.path.join(assets_dir(), asset_id)).convert("RGBA").resize((16, 16))
    except (OSError, ValueError):
        return 0.5, 0.5, 0.5, 1.0, 0.0
    px = np.asarray(im, float) / 255
    w = px[..., 3].reshape(-1)
    rgb = px[..., :3].reshape(-1, 3)
    if w.sum() < 1e-6:
        return 0.5, 0.5, 0.5, 0.0, 0.0
    mean = (rgb * w[:, None]).sum(0) / w.sum()
    std = math.sqrt((((rgb - mean) ** 2).sum(1) * w).sum() / w.sum() / 3) * 255 / 128
    return float(mean[0]), float(mean[1]), float(mean[2]), float(w.mean()), min(1.0, std)


def _luminance(r, g, b):
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in (r, g, b)]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
