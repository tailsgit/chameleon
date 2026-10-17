"""Turn a layout plan's slots into output elements.

- Background: full canvas. A `cover` image crops; any other image keeps its aspect
  ratio, as large as fits and centred (its `fit` can't change).
- Images and rigid units: one uniform scale for every member, so aspect ratios
  are exact, and rotated members stay inside because their rotated bounds scale too.
- Text: the largest whole-number font that fits its box, measured with
  eval.check.text_layout (the renderer's own wrapping and line layout, letter spacing,
  top alignment). Never below the readable minimum unless nothing else fits.
- Floating units (corner badges, stickers, demoted low-importance units) go into the
  largest free rectangle near where they sat in the source, so they never overlap
  anything already placed. With focal=True, one that stands out by colour is centred
  in its rectangle instead of pushed towards its source side (resize() realises plans
  both ways when that matters and lets the scorer choose). Attached units (a ribbon across a card) go last,
  at the same relative spot on their host, scaled with it.
- Rotated units keep their source angle, mirrored (negated) only when they ended up
  on the mirrored side of their anchor on one axis, so the tilt still points the same
  way relative to the design. No other angle is ever produced.
- Decorations: rescaled around their relative source position and pulled fully inside.
"""

import copy
import math
from dataclasses import dataclass

import numpy as np

from engine.analyze import element_box, full_box
from eval.check import text_layout
from eval.score import MIN_TEXT_PX_ABS, MIN_TEXT_REL_HEIGHT

MIN_DIM = 1.5        # px. check() treats < 1px as a hidden element
# Text metrics differ by ~1-2% between platforms (CoreText on macOS, FreeType on Linux), so the
# same text can wrap to one more line wherever the official renderer runs. Text boxes get spare
# height (invisible, since text is top-aligned) and tight widths keep a margin.
SLACK_LINES = 0.12   # spare lines as a fraction of the line count, at least one
WIDTH_MARGIN = 1.03  # tight text boxes are this much wider than the widest line
LABEL_MARGIN = 0.97  # text inside a scaled group must fit in this fraction of its width
FLOAT_GAP = 0.5      # free-space padding around placed content, in grid cells
FLOAT_CANDIDATES = 6  # free rectangles tried exactly per floating text unit


@dataclass
class Extent:
    w: float
    h: float
    fs: int | None = None        # text units
    scale: float | None = None   # image and rigid units
    slack: float = 0.0           # text: spare box height below the lines (not part of the layout)


class Sizer:
    """Measures units for one (analysis, target canvas) pair, caching text layouts."""

    def __init__(self, a, tw, th):
        self.a, self.tw, self.th = a, tw, th
        self.floor_px = max(MIN_TEXT_PX_ABS, MIN_TEXT_REL_HEIGHT * th)  # same floor the scorer uses
        self._lay = {}

    def layout(self, eid, fs, width):
        key = (eid, fs, round(width, 2))
        if key not in self._lay:
            src = self.a.els[eid]  # the renderer's TextElement needs positive dimensions
            el = dict(src, font_size=fs, width=max(width, 0.01), height=max(src["height"], 1.0))
            if src.get("letter_spacing"):
                el["letter_spacing"] = self.spacing(eid, fs)
            self._lay[key] = text_layout(el)
        return self._lay[key]

    def fits(self, eid, fs, w, h=math.inf):
        lay = self.layout(eid, fs, w)
        return lay["left"] >= -0.01 and lay["right"] <= w + 0.01 and lay["height"] <= h + 0.01

    def spacing(self, eid, fs):
        """Letter spacing (px) scales with the font, so the text keeps its look."""
        src = self.a.els[eid]
        return src.get("letter_spacing", 0) * fs / src["font_size"]

    def set_font(self, el, fs):
        el["font_size"] = fs
        if self.a.els[el["id"]].get("letter_spacing"):
            el["letter_spacing"] = self.spacing(el["id"], fs)

    def fit_width(self, eid, fs, max_w):
        """Widest box <= max_w whose wrapped lines fit horizontally, or None.
        Only letter-spaced text needs the search: the converter wraps without the
        spacing the renderer then adds, so a full line overflows by ~spacing x chars
        and only a narrower box (lines that break early) leaves enough slack."""
        if self.fits(eid, fs, max_w):
            return max_w
        if not self.a.els[eid].get("letter_spacing"):
            return None
        w = max_w
        for _ in range(40):
            w *= 0.97
            if self.fits(eid, fs, w):
                return w
        return None

    def fs_min(self, eid):
        return math.ceil(min(self.floor_px, self.a.els[eid]["font_size"]) - 1e-9)

    def read_scale(self, u):
        """Smallest uniform scale that keeps every text member readable."""
        return max((self.fs_min(i) / self.a.els[i]["font_size"] for i in u.members if self.a.els[i]["type"] == "text"),
                   default=0.0)

    def floor_scale(self, u):
        """Smallest uniform scale that keeps every member at least MIN_DIM px."""
        dims = [min(self.a.els[i]["width"], self.a.els[i]["height"]) for i in u.members]
        return max((MIN_DIM / d for d in dims if d > 0), default=0.0)

    def text_extent(self, eid, k, max_w, rescue=False):
        """Text at scale k: font = floor(source font * k) but at least the readable minimum
        (1 in rescue mode), lowered further only if a single word is wider than max_w.
        The box is shrunk to the widest line when that keeps the same wrapping."""
        src = self.a.els[eid]
        fs = max(1 if rescue else self.fs_min(eid), math.floor(src["font_size"] * k + 1e-9))
        w = self.fit_width(eid, fs, max_w)
        while w is None and fs > 1:
            fs -= 1
            w = self.fit_width(eid, fs, max_w)
        w = w or max_w  # unfixable (a word wider than max_w at 1px): check() will reject this candidate
        lay = self.layout(eid, fs, w)
        if lay["lines"]:
            tight = (max(b[2] - b[0] for b in lay["line_boxes"]) + 0.5) * WIDTH_MARGIN
            if tight < w:
                t = self.layout(eid, fs, tight)
                if t["lines"] == lay["lines"] and self.fits(eid, fs, tight):
                    w, lay = tight, t
        line = fs * src.get("line_height", 1.2)
        return Extent(w, lay["height"] + 1.0, fs=fs, slack=line * max(1, math.ceil(SLACK_LINES * lay["lines"])))

    def unit_extent(self, u, k, max_w, max_h=math.inf, img_mult=1.0, rescue=False):
        if u.kind == "text":
            return self.text_extent(u.members[0], k, max_w, rescue)
        s = k * (img_mult if u.role == "hero" else 1.0)
        if u.kind == "rigid" and not rescue:
            s = max(s, self.read_scale(u))
        s = min(s, max_w / max(u.w, 1e-6), max_h / max(u.h, 1e-6))
        s = max(s, self.floor_scale(u))
        return Extent(u.w * s, u.h * s, scale=s)


def realize(a, plan, tw, th, focal=True):
    """Build the output design for one plan."""
    sizer = plan.sizer
    out = {i: copy.deepcopy(e) for i, e in a.els.items()}
    for b in a.background:
        place_background(out[b], tw, th)

    placed = []
    for slot in plan.slots:
        u = a.units[slot.uid]
        if u.kind == "text":
            place_text(out[u.members[0]], sizer, slot, th)
        else:
            place_rigid(out, sizer, a, u, slot.scale, slot.x, slot.y)
        placed += [element_box(out[m]) for m in u.members]

    grid = Grid(tw, th, plan.margin)
    for b in placed:
        grid.mark(b)
    # hosts first: attached units are placed relative to wherever their host ended up
    for uid in sorted(plan.floating, key=lambda i: (a.units[i].host is not None, -a.units[i].importance)):
        u = a.units[uid]
        if u.host:
            place_attached(out, sizer, a, u, tw, th)
        else:
            place_floating(out, sizer, a, u, plan.k, grid, tw, th, focal)
        for m in u.members:
            grid.mark(element_box(out[m]))

    for d in a.decorations:
        place_decoration(out, sizer, a, d, tw, th)
    for u in [*a.units.values(), *a.decorations]:
        if u.rotated:
            orient(out, a, u, tw, th)

    return {"canvas": {"width": tw, "height": th}, "elements": [out[e["id"]] for e in a.source["elements"]]}


def place_background(el, tw, th):
    if el["type"] == "image" and el.get("fit", "contain") != "cover":
        s = min(tw / el["width"], th / el["height"])
        w, h = el["width"] * s, el["height"] * s
        el.update(x=(tw - w) / 2, y=(th - h) / 2, width=w, height=h)
    else:
        el.update(x=0, y=0, width=tw, height=th)


def place_text(el, sizer, slot, th):
    fs = slot.fs
    while fs > 1 and not sizer.fits(el["id"], fs, slot.w, slot.h):
        fs -= 1
    el.update(x=slot.x, y=slot.y, width=slot.w, height=max(slot.h, min(slot.h + slot.slack, th - slot.y)))
    sizer.set_font(el, fs)


def place_rigid(out, sizer, a, u, s, x, y):
    """Scale every member of u by s about the unit's top-left corner and move that corner to (x, y)."""
    for m in u.members:
        src, el = a.els[m], out[m]
        el.update(x=x + (src["x"] - u.box[0]) * s, y=y + (src["y"] - u.box[1]) * s,
                  width=src["width"] * s, height=src["height"] * s)
        if el["type"] == "text":
            fs = max(1, math.floor(src["font_size"] * s + 1e-9))
            while fs > 1 and not sizer.fits(m, fs, el["width"] * LABEL_MARGIN, el["height"]):
                fs -= 1
            if not sizer.fits(m, fs, el["width"]):  # letter-spaced: narrow the box around its centre
                w = sizer.fit_width(m, fs, el["width"])
                if w:
                    el.update(x=el["x"] + (el["width"] - w) / 2, width=w)
            # text is top-aligned: when the font had to shrink, keep the lines centred where they were
            ideal = sizer.layout(m, src["font_size"], src["width"])["height"] * s
            actual = sizer.layout(m, fs, el["width"])["height"]
            dy = min((ideal - actual) / 2, el["height"] - actual - 1)  # never squeeze the box below the text
            if dy > 0:
                el.update(y=el["y"] + dy, height=el["height"] - dy)
            sizer.set_font(el, fs)


def place_floating(out, sizer, a, u, k, grid, tw, th, focal=True):
    ax, ay = a.anchor(u)
    ax, ay = ax * tw, ay * th
    diag = math.hypot(tw, th)
    rects = grid.free_rects()
    if u.kind == "text":
        eid = u.members[0]
        src = a.els[eid]
        want = max(sizer.fs_min(eid), math.floor(src["font_size"] * k + 1e-9))
        need = max(1.0, (u.drawn[2] - u.drawn[0]) * (u.drawn[3] - u.drawn[1])) * (want / src["font_size"]) ** 2

        def estimate(r):
            rw, rh = r[2] - r[0], r[3] - r[1]
            return min(1.0, math.sqrt(rw * rh / need), rh / (want * src.get("line_height", 1.2)))

        best = None
        for r in sorted(rects, key=lambda r: -(estimate(r) - 0.25 * _dist(r, ax, ay) / diag))[:FLOAT_CANDIDATES]:
            rw, rh = r[2] - r[0], r[3] - r[1]
            def room(fs):  # leave one spare line for other platforms' metrics
                return rh - fs * src.get("line_height", 1.2)
            fs = want
            while fs > 1 and not sizer.fits(eid, fs, rw, room(fs)):
                fs -= 1
            if not sizer.fits(eid, fs, rw, room(fs)):
                continue
            ext = sizer.text_extent(eid, fs / src["font_size"], rw, rescue=True)
            value = fs / want - 0.25 * _dist(r, ax, ay) / diag
            if best is None or value > best[0]:
                best = (value, r, ext)
        if best is None:
            ext = sizer.text_extent(eid, 0, min(tw, max(src["width"], 1)), rescue=True)
            x, y = _clamp(ax - ext.w / 2, 0, tw - ext.w), _clamp(ay - ext.h / 2, 0, th - ext.h)
        else:
            _v, r, ext = best
            # stand-out colour: centre of its zone, not pushed aside (corner-pinned units keep their corner)
            fx = (r[0] + r[2]) / 2 if focal and u.emphasis and u.corner is None and not u.rotated else ax
            x, y = _clamp(fx - ext.w / 2, r[0], r[2] - ext.w), _clamp(ay - ext.h / 2, r[1], r[3] - ext.h)
        out[eid].update(x=x, y=y, width=ext.w, height=max(ext.h, min(ext.h + ext.slack, th - y)))
        sizer.set_font(out[eid], ext.fs)
        return

    want = max(k, sizer.read_scale(u)) if u.kind == "rigid" else k
    best = None
    for r in rects:
        s = min(want, (r[2] - r[0]) / max(u.w, 1e-6), (r[3] - r[1]) / max(u.h, 1e-6))
        value = s / max(want, 1e-9) - 0.25 * _dist(r, ax, ay) / diag
        if s >= sizer.floor_scale(u) and (best is None or value > best[0]):
            best = (value, r, s)
    if best is None:
        s = min(max(sizer.floor_scale(u), 1e-3), tw / max(u.w, 1e-6), th / max(u.h, 1e-6))
        r = (0, 0, tw, th)
    else:
        _v, r, s = best
    w, h = u.w * s, u.h * s
    fx = (r[0] + r[2]) / 2 if focal and u.emphasis and u.corner is None and not u.rotated else ax  # see the text branch
    place_rigid(out, sizer, a, u, s, _clamp(fx - w / 2, r[0], r[2] - w), _clamp(ay - h / 2, r[1], r[3] - h))


def place_attached(out, sizer, a, u, tw, th):
    """Same relative spot on the host, scaled like the host (never below readable, never off-canvas)."""
    host = a.units[u.host]
    hb = _union_boxes([element_box(out[m]) for m in host.members])
    s = (hb[2] - hb[0]) / max(host.drawn[2] - host.drawn[0], 1e-6)
    s = min(max(s, sizer.floor_scale(u)), tw / max(u.w, 1e-6), th / max(u.h, 1e-6))
    cx, cy = hb[0] + u.rel[0] * (hb[2] - hb[0]), hb[1] + u.rel[1] * (hb[3] - hb[1])
    # u.rel is about the drawn centre; place_rigid positions the full box
    dx = ((u.drawn[0] + u.drawn[2]) / 2 - u.box[0]) * s
    dy = ((u.drawn[1] + u.drawn[3]) / 2 - u.box[1]) * s
    w, h = u.w * s, u.h * s
    place_rigid(out, sizer, a, u, s, _clamp(cx - dx, 0, tw - w), _clamp(cy - dy, 0, th - h))


def orient(out, a, u, tw, th):
    """Source angle, negated when u sits on the mirrored side of its anchor on exactly one axis.
    Only for units whose rotated members share one centre: mirroring an off-centre member's
    angle without mirroring its offset would tear the unit apart."""
    from engine.analyze import side_of
    rot = [m for m in u.members if a.els[m].get("rotation", 0)]
    centres = [(a.els[m]["x"] + a.els[m]["width"] / 2, a.els[m]["y"] + a.els[m]["height"] / 2) for m in rot]
    if max(math.dist(centres[0], c) for c in centres) > 0.02 * max(u.w, u.h):
        return
    anchor = _union_boxes([element_box(out[m]) for m in a.units[u.host].members]) if u.host else (0, 0, tw, th)
    now = side_of(_union_boxes([element_box(out[m]) for m in u.members]), anchor)
    flip = u.side[0] * now[0] * u.side[1] * now[1]
    for m in rot:
        out[m]["rotation"] = a.els[m]["rotation"] * flip


def _union_boxes(boxes):
    return (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))


def place_decoration(out, sizer, a, d, tw, th):
    s = math.sqrt(tw * th / (a.sw * a.sh))
    s = min(s, 0.95 * tw / max(d.w, 1e-6), 0.95 * th / max(d.h, 1e-6))
    ax, ay = a.anchor(d)
    w, h = d.w * s, d.h * s
    place_rigid(out, sizer, a, d, s, _clamp(ax * tw - w / 2, 0, tw - w), _clamp(ay * th - h / 2, 0, th - h))


class Grid:
    """Occupancy grid over the canvas, for finding free rectangles."""

    def __init__(self, tw, th, margin):
        self.tw, self.th, self.margin = tw, th, margin
        self.cell = max(min(tw, th) / 24, max(tw, th) / 160)
        self.occ = np.zeros((math.ceil(th / self.cell), math.ceil(tw / self.cell)), dtype=bool)

    def mark(self, b, pad=FLOAT_GAP):
        c = self.cell
        r0, r1 = max(0, math.floor(b[1] / c - pad)), max(0, math.ceil(b[3] / c + pad))
        c0, c1 = max(0, math.floor(b[0] / c - pad)), max(0, math.ceil(b[2] / c + pad))
        self.occ[r0:r1, c0:c1] = True

    def free_rects(self):
        """Maximal empty rectangles (histogram method), in px, clipped to the margin box."""
        rows, cols = self.occ.shape
        heights = np.zeros(cols, dtype=int)
        found = set()
        for r in range(rows):
            heights = np.where(self.occ[r], 0, heights + 1)
            stack = []
            for col in range(cols + 1):
                cur = int(heights[col]) if col < cols else 0
                start = col
                while stack and stack[-1][1] >= cur:
                    sc, sh = stack.pop()
                    if sh > 0:
                        found.add((sc, r - sh + 1, col, r + 1))
                    start = sc
                stack.append((start, cur))
        c, m = self.cell, self.margin
        rects = []
        for c0, r0, c1, r1 in found:
            x0, y0 = max(c0 * c, m), max(r0 * c, m)
            x1, y1 = min(c1 * c, self.tw - m), min(r1 * c, self.th - m)
            if x1 - x0 > 1 and y1 - y0 > 1:
                rects.append((x0, y0, x1, y1))
        return rects


def _dist(r, x, y):
    return math.hypot(_clamp(x, r[0], r[2]) - x, _clamp(y, r[1], r[3]) - y)


def _clamp(v, lo, hi):
    return lo if hi < lo else min(max(v, lo), hi)
