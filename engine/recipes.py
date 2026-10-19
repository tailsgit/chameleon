"""Layout recipes: turn an Analysis + target canvas + knobs into slot boxes.

Every recipe places "flow" units with the same column solver (`solve_column`):
units keep their source reading-order rows (a row wraps when it's too wide), and
one shared scale k (fonts = floor(source font x k), never below readable) is
binary-searched to be as large as fits, up to a cap of
`cap x sqrt(target area / source area)`. If even the readable minimum doesn't
fit, the least important unit (never the headline) is demoted to "floating" and
placed afterwards into leftover space by engine.fit.

Recipes:
  stack    single centred/left column over the whole canvas
  split    hero image in one column (left or right), everything else in the other
  strip    one row for ultra-wide banners: logo | hero | text column | CTA
  overlay  a stack confined to the quietest part of the background image
  compact  stack or strip with only the primary units (headline, CTA, logo, hero) in
           flow; everything else floats into leftover space. For tiny canvases.
  subject  a background photo whose subject a centre crop at the canvas's shape would cut off, in
           the least extreme box that keeps it at one end; everything else stacked beside it
  anchor   a big hero (>= 25% of the design) keeps its share of the canvas, flush against
           one edge; everything else is a column in the space left (text fits around the
           photo instead of both shrinking together).
  preserve   the source layout itself, changed as little as possible to fit (engine.preserve)
  retrieved  layouts of real designs of a similar shape and composition (engine.retrieve)
"""

import logging
import math
import time
from dataclasses import dataclass, field
from itertools import combinations, product

import numpy as np
from PIL import Image

from engine.analyze import PRIMARY_ROLES
from engine.fit import Sizer
from engine.preserve import preserve_plans
from engine.retrieve import retrieved
from eval.saliency import aspect_range, salient_box
from eval.render import assets_dir
from eval.score import CONTRAST_MIN_LARGE, _rel_luminance
from renderer.converter.colorutil import parse_rgba

GAP = 0.03          # vertical gap between rows, fraction of the column's shorter side
H_GAP = 0.03        # horizontal gap between strip cells, fraction of the canvas width
BISECT_STEPS = 16
HERO_SHARE = 0.25   # a hero covering this share of the source canvas gets the anchor recipe
HERO_SIDE_MAX = 0.65  # ...and at most this share of the target's width (or height) in it
COL_ASPECT = 1.5    # a box this much wider than tall may lay its units out in 2 or 3 columns...
COL_GAIN = 1.15     # ...when one column hits the readable floor and columns raise the scale this much
SUBJECT_REST = 0.25  # the subject recipe needs at least this share of the canvas beside the photo
log = logging.getLogger(__name__)


@dataclass
class Slot:
    uid: str
    x: float
    y: float
    w: float
    h: float
    fs: int | None = None
    scale: float | None = None
    slack: float = 0.0   # text: spare box height below the lines (see engine.fit.Extent)
    cols: int | None = None  # sibling row: arrangement (see engine.fit.Sizer.arrangements)


@dataclass
class Plan:
    recipe: str
    knobs: dict
    slots: list
    floating: list
    k: float
    margin: float
    sizer: Sizer = field(repr=False, default=None)


def generate(a, tw, th, deadline=None):
    """All candidate plans for one task: every applicable recipe x its knob grid, then the
    retrieved layouts. Past `deadline` (time.monotonic()), nothing more is added."""
    sizer = Sizer(a, tw, th)
    hero = a.by_role("hero")
    has_hero = hero is not None and not hero.floating
    aspect = tw / th
    tiny = min(tw, th) < 200 or tw * th < 120_000
    plans, cut = [], []

    def add(fn, name, **knobs):
        if plans and deadline is not None and time.monotonic() > deadline:
            if not cut:
                log.info("time budget reached after %d plans", len(plans))
                cut.append(name)
            return
        plan = fn(a, sizer, tw, th, **knobs)
        if plan is not None:
            plan.recipe, plan.knobs, plan.sizer = name, knobs, sizer
            plans.append(plan)

    imgs = (0.7, 1.0, 1.4) if has_hero else (1.0,)
    orders = ("source", "hero_first") if has_hero else ("source",)
    for align, vjust, img, cap, order in product(("center", "left"), ("spread", "center"), imgs, (0.9, 1.2), orders):
        add(stack, "stack", align=align, vjust=vjust, img_mult=img, cap=cap, order=order)
    if has_hero and aspect >= 0.9:
        for side, ratio, align, vjust in product(("left", "right"), (0.4, 0.55), ("center", "left"), ("spread", "center")):
            add(split, "split", side=side, ratio=ratio, align=align, vjust=vjust, cap=1.0)
    if has_hero and big_hero(a):
        sides = [x for x, ok in (("left", aspect >= 0.8), ("right", aspect >= 0.8), ("top", aspect <= 1.25),
                                 ("bottom", aspect <= 1.25)) if ok]
        for side, align, cap in product(sides, ("center", "left"), (1.0, 1.2)):
            add(anchor, "anchor", side=side, align=align, cap=cap)
    if aspect >= 2.0:
        for hero_pos, img, align, cap in product(("left", "right"), (0.8, 1.0), ("center", "left"), (0.9, 1.2)):
            add(strip, "strip", hero_pos=hero_pos, img_mult=img, align=align, cap=cap)
    for region in quiet_regions(a, tw, th)[:2]:
        for align in ("center", "left"):
            add(stack, "overlay", align=align, vjust="center", img_mult=1.0, cap=1.0, order="source", region=region)
    bg = subject_boxes(a, tw, th)
    if bg:
        for align, cap in product(("center", "left"), (0.9, 1.2)):
            add(subject, "subject", bg=bg, align=align, cap=cap)
    if tiny:
        for align, cap in product(("center", "left"), (0.9, 1.2)):
            if aspect >= 2.0:
                add(strip, "compact", hero_pos="left", img_mult=1.0, align=align, cap=cap, primaries_only=True)
            else:
                add(stack, "compact", align=align, vjust="spread", img_mult=1.0, cap=cap, order="source", primaries_only=True)
    if cut:
        return plans
    return plans + preserve_plans(a, sizer, tw, th, deadline) + retrieved(a, sizer, tw, th, deadline)


# --- recipes ------------------------------------------------------------------

def stack(a, sizer, tw, th, align, vjust, img_mult, cap, order, primaries_only=False, region=None):
    m = margin(tw, th)
    box = region or (m, m, tw - m, th - m)
    rows, floating = flow(a, primaries_only)
    if order == "hero_first":
        hero = a.by_role("hero")
        rows = sorted(rows, key=lambda r: hero.id not in r)
    slots, k, demoted = solve_column(a, sizer, rows, box, k_cap(a, tw, th, cap), align, vjust, img_mult)
    return Plan("", {}, slots, floating + demoted, k, m)


def split(a, sizer, tw, th, side, ratio, align, vjust, cap):
    m = margin(tw, th)
    hero = a.by_role("hero")
    gap = H_GAP * tw
    bw, bh = tw - 2 * m, th - 2 * m
    img_w = ratio * (bw - gap)
    text_w = bw - gap - img_w
    s = min(img_w / max(hero.w, 1e-6), bh / max(hero.h, 1e-6))
    img_x0 = m if side == "left" else m + text_w + gap
    text_x0 = m + img_w + gap if side == "left" else m
    hero_slot = Slot(hero.id, img_x0 + (img_w - hero.w * s) / 2, m + (bh - hero.h * s) / 2, hero.w * s, hero.h * s, scale=s)
    rows, floating = flow(a, False)
    rows = [[u for u in r if u != hero.id] for r in rows]
    slots, k, demoted = solve_column(a, sizer, rows, (text_x0, m, text_x0 + text_w, th - m),
                                     k_cap(a, tw, th, cap), align, vjust, 1.0)
    return Plan("", {}, [hero_slot] + slots, floating + demoted, k, m)


def subject(a, sizer, tw, th, bg, align, cap):
    """The background photo in `bg`'s box at one end (engine.fit.realize places it there), and a
    stack in the rest of the canvas."""
    m = margin(tw, th)
    x, y, w, h = next(iter(bg.values()))
    if h >= th - 0.5:  # the photo spans the height, at the left or right end
        region = (x + w + m, m, tw - m, th - m) if x == 0 else (m, m, x - m, th - m)
    else:
        region = (m, y + h + m, tw - m, th - m) if y == 0 else (m, m, tw - m, y - m)
    if (region[2] - region[0]) * (region[3] - region[1]) < SUBJECT_REST * tw * th:
        return None
    return stack(a, sizer, tw, th, align, "center", 1.0, cap, "source", region=region)


def subject_boxes(a, tw, th):
    """{background id: (x, y, w, h)} for a cover photo whose centre crop at the canvas's shape would cut
    off the subject its source crop shows (eval.saliency): the least extreme box shape that keeps it,
    across the canvas's short side, at the end nearer the subject."""
    out = {}
    if not _legible_beside(a):
        return out
    for b in a.background:
        e = a.els[b]
        r = aspect_range(e)
        if r is None or not r[0] <= e["width"] / e["height"] <= r[1] or r[0] <= tw / th <= r[1]:
            continue
        x0, y0, x1, y1 = salient_box(e["asset_id"])
        if tw / th > r[1]:
            w = th * r[1]
            out[b] = (0.0 if x0 + x1 < 1 else tw - w, 0.0, w, float(th))
        else:
            h = tw / r[0]
            out[b] = (0.0, 0.0 if y0 + y1 < 1 else th - h, float(tw), h)
        break  # one photo per design: the layout goes beside it
    return out


def _legible_beside(a):
    """Every free text stays readable (WCAG CONTRAST_MIN_LARGE) on what the canvas shows beside the
    photo: the lowest background shape's fill, else white. White text that sat on the photo is not."""
    fill = next((a.els[b]["fill_color"] for b in a.background if a.els[b]["type"] == "shape"), None)
    bg = np.array(parse_rgba(fill)[:3] if fill else (255, 255, 255)) / 255
    for u in a.units.values():
        if u.kind == "text":
            r, g, b, al = parse_rgba(a.els[u.members[0]].get("color"))
            fg = al * np.array([r, g, b]) / 255 + (1 - al) * bg
            lf, lb = _rel_luminance(fg), _rel_luminance(bg)
            if (max(lf, lb) + 0.05) / (min(lf, lb) + 0.05) < CONTRAST_MIN_LARGE:
                return False
    return True


def big_hero(a):
    """A photo covering HERO_SHARE of the design is its main visual, worth its own space."""
    hero = a.by_role("hero")
    return hero is not None and hero.w * hero.h >= HERO_SHARE * a.sw * a.sh


def anchor(a, sizer, tw, th, side, align, cap):
    """The hero keeps the share of the canvas it had (as large as fits that side, up to
    HERO_SIDE_MAX of the canvas width or height), flush against one canvas edge; the
    rest of the design is a column in the space left."""
    m = margin(tw, th)
    hero = a.by_role("hero")
    share = hero.w * hero.h / (a.sw * a.sh)
    s = math.sqrt(share * tw * th / (hero.w * hero.h))
    if side in ("left", "right"):
        s = min(s, th / hero.h, HERO_SIDE_MAX * tw / hero.w)
    else:
        s = min(s, tw / hero.w, HERO_SIDE_MAX * th / hero.h)
    w, h = hero.w * s, hero.h * s
    x = 0.0 if side == "left" else tw - w if side == "right" else (tw - w) / 2
    y = 0.0 if side == "top" else th - h if side == "bottom" else (th - h) / 2
    box = {"left": (w + m, m, tw - m, th - m), "right": (m, m, tw - w - m, th - m),
           "top": (m, h + m, tw - m, th - m), "bottom": (m, m, tw - m, th - h - m)}[side]
    if box[2] - box[0] < 0.2 * tw or box[3] - box[1] < 0.2 * th:
        return None
    rows, floating = flow(a, False)
    rows = [[u for u in r if u != hero.id] for r in rows]
    slots, k, demoted = solve_column(a, sizer, rows, box, k_cap(a, tw, th, cap), align, "center", 1.0)
    return Plan("", {}, [Slot(hero.id, x, y, w, h, scale=s)] + slots, floating + demoted, k, m)


def strip(a, sizer, tw, th, hero_pos, img_mult, align, cap, primaries_only=False):
    m = margin(tw, th)
    x0, y0, x1, y1 = m, m, tw - m, th - m
    H, W = y1 - y0, x1 - x0
    gap = H_GAP * tw
    kc = k_cap(a, tw, th, cap)
    rows, floating = flow(a, primaries_only)
    in_flow = {u for r in rows for u in r}

    def cell(role):
        u = a.by_role(role)
        return u if u is not None and u.id in in_flow and u.kind != "text" else None

    logo, hero, cta = cell("logo"), cell("hero"), cell("cta")
    scales = {}
    if logo:
        scales[logo.id] = min(0.6 * H / max(logo.h, 1e-6), 1.5 * kc)
    if hero:
        scales[hero.id] = img_mult * H / max(hero.h, 1e-6)
    if cta:
        scales[cta.id] = min(0.6 * H / max(cta.h, 1e-6), max(kc, sizer.read_scale(cta)))
    fixed = {u.id: u for u in (logo, hero, cta) if u}
    text_rows = [[u for u in r if u not in fixed] for r in rows]
    text_rows = [r for r in text_rows if r]

    n_cells = len(fixed) + (1 if text_rows else 0)
    fixed_w = sum(fixed[i].w * s for i, s in scales.items())
    room = W - gap * (n_cells - 1)
    min_text = 0.35 * W if text_rows else 0
    if fixed_w > room - min_text and fixed_w > 0:
        f = max(0.05, (room - min_text) / fixed_w)
        scales = {i: max(s * f, sizer.floor_scale(fixed[i])) for i, s in scales.items()}
        fixed_w = sum(fixed[i].w * s for i, s in scales.items())
    text_w = max(1.0, room - fixed_w) if text_rows else 0

    order = [logo, hero, "TEXT", cta] if hero_pos == "left" else [logo, "TEXT", hero, cta]
    order = [c for c in order if c is not None and (c != "TEXT" or text_rows)]
    if not text_rows:  # spread the fixed cells evenly instead
        gap = (W - fixed_w) / max(1, len(order) - 1) if len(order) > 1 else 0
    slots, x, k, demoted = [], x0 if len(order) > 1 or text_rows else x0 + (W - fixed_w) / 2, kc, []
    for c in order:
        if c == "TEXT":
            sl, k, demoted = solve_column(a, sizer, text_rows, (x, y0, x + text_w, y1), kc, align, "center", img_mult)
            slots += sl
            x += text_w + gap
        else:
            s = scales[c.id]
            slots.append(Slot(c.id, x, y0 + (H - c.h * s) / 2, c.w * s, c.h * s, scale=s))
            x += c.w * s + gap
    return Plan("", {}, slots, floating + demoted, k, m)


# --- shared solver ------------------------------------------------------------

def solve_column(a, sizer, rows, box, kc, align, vjust, img_mult):
    """Lay rows of units out top to bottom in `box` at the largest shared scale <= kc.
    Returns (slots, k, demoted unit ids). In a wide box where one column would hit the
    readable floor, 2 or 3 columns are tried too (units in reading order down each column,
    columns left to right, cut where the columns' heights are most even); they win with
    fewer demoted units, or COL_GAIN more scale."""
    best = _solve(a, sizer, rows, box, kc, align, vjust, img_mult, 1)
    if box[2] - box[0] < COL_ASPECT * (box[3] - box[1]) or not _at_floor(a, sizer, rows, *best[1:]):
        return best
    for cols in (2, 3):
        res = _solve(a, sizer, rows, box, kc, align, vjust, img_mult, cols)
        if res[0] and (len(res[2]) < len(best[2]) or len(res[2]) == len(best[2]) and res[1] >= COL_GAIN * best[1]):
            best = res
    return best


def _at_floor(a, sizer, rows, k, demoted):
    """Something was demoted, or some flowing text is already at its readable minimum."""
    texts = [a.units[u].members[0] for r in rows for u in r if a.units[u].kind == "text" and u not in demoted]
    return bool(demoted) or any(math.floor(a.els[t]["font_size"] * k + 1e-9) <= sizer.fs_min(t) for t in texts)


def _solve(a, sizer, rows, box, kc, align, vjust, img_mult, cols):
    rows = [list(r) for r in rows if r]
    demoted = []
    while rows:
        res = _column(a, sizer, rows, box, kc, align, vjust, img_mult, rescue=False, cols=cols)
        if res:
            return res[0], res[1], demoted
        victims = [u for r in rows for u in r if a.units[u].role != "headline"
                   and not (a.units[u].role == "hero" and big_hero(a))]  # a big photo is never demoted
        if not victims:
            break
        v = min(victims, key=lambda u: a.units[u].importance)
        demoted.append(v)
        rows = [[u for u in r if u != v] for r in rows]
        rows = [r for r in rows if r]
    if rows:  # only the headline is left and even it doesn't fit at a readable size
        res = _column(a, sizer, rows, box, kc, align, vjust, img_mult, rescue=True, cols=cols)
        if res:
            return res[0], res[1], demoted
        demoted += [u for r in rows for u in r]
    return [], 0.0, demoted


def _column(a, sizer, rows, box, kc, align, vjust, img_mult, rescue, cols=1):
    x0, y0, x1, y1 = box
    W, H = x1 - x0, y1 - y0
    if W <= 1 or H <= 1:
        return None
    gap = max(2.0, GAP * min(W, H))
    col_gap = max(gap, H_GAP * W)
    cw = (W - col_gap * (cols - 1)) / cols

    def measure(k):
        if cols > 1:  # newspaper columns: here `lines` are the columns
            ext = [(uid, sizer.unit_extent(a.units[uid], k, cw, img_mult=img_mult, rescue=rescue)) for r in rows for uid in r]
            if len(ext) < cols:
                return [ext], math.inf
            height = lambda c: sum(e.h for _u, e in c) + gap * (len(c) - 1) + c[-1][1].slack
            cuts = min(combinations(range(1, len(ext)), cols - 1),
                       key=lambda cut: sorted((height(ext[i:j]) for i, j in zip((0, *cut), (*cut, len(ext)))), reverse=True))
            lines = [ext[i:j] for i, j in zip((0, *cuts), (*cuts, len(ext)))]
            return lines, max(height(c) for c in lines)
        lines = []
        for row in rows:
            cur, used = [], 0.0
            for uid in row:
                e = sizer.unit_extent(a.units[uid], k, W, img_mult=img_mult, rescue=rescue)
                need = e.w + (gap if cur else 0)
                if cur and used + need > W:
                    lines.append(cur)
                    cur, used, need = [], 0.0, e.w
                cur.append((uid, e))
                used += need
            lines.append(cur)
        total = sum(max(e.h for _u, e in ln) for ln in lines) + gap * (len(lines) - 1)
        # the last row's spare text height must fit too; earlier rows' slack only overlaps empty box area
        return lines, total + max(e.slack for _u, e in lines[-1])

    lines, total = measure(kc)
    k = kc
    if total > H:
        lo = 0.005
        lines, total = measure(lo)
        if total > H:
            return None
        hi = kc
        for _ in range(BISECT_STEPS):
            mid = (lo + hi) / 2
            if measure(mid)[1] <= H:
                lo = mid
            else:
                hi = mid
        k = lo
        lines, total = measure(k)

    if cols > 1:
        return [s for j, c in enumerate(lines) for s in _stack_cell(c, x0 + j * (cw + col_gap), y0, cw, H, gap, align, vjust)], k
    extra = H - total
    n = len(lines)
    if vjust == "spread":
        pad = extra / (n + 1)
        y, step = y0 + pad, gap + pad
    else:
        y, step = y0 + extra / 2, gap
    slots = []
    for ln in lines:
        lh = max(e.h for _u, e in ln)
        lw = sum(e.w for _u, e in ln) + gap * (len(ln) - 1)
        # left-aligned: what is drawn lines up with the column edge, not the (wider) box
        x = x0 + (W - lw) / 2 if align == "center" else max(0.0, x0 - ln[0][1].inset)
        for uid, e in ln:
            slots.append(Slot(uid, x, y + (lh - e.h) / 2, e.w, e.h, fs=e.fs, scale=e.scale, slack=e.slack, cols=e.cols))
            x += e.w + gap
        y += lh + step
    return slots, k


def _stack_cell(col, x0, y0, W, H, gap, align, vjust):
    """One newspaper column: its units top to bottom in (x0, y0, W, H), spread or centred."""
    total = sum(e.h for _u, e in col) + gap * (len(col) - 1) + col[-1][1].slack
    extra = H - total
    pad = extra / (len(col) + 1) if vjust == "spread" else 0.0
    y = y0 + (pad if vjust == "spread" else extra / 2)
    slots = []
    for uid, e in col:
        x = x0 + (W - e.w) / 2 if align == "center" else max(0.0, x0 - e.inset)
        slots.append(Slot(uid, x, y, e.w, e.h, fs=e.fs, scale=e.scale, slack=e.slack, cols=e.cols))
        y += e.h + gap + pad
    return slots


# --- helpers ------------------------------------------------------------------

def flow(a, primaries_only):
    """(rows of flow unit ids, floating unit ids)."""
    floating = [uid for uid, u in a.units.items() if u.floating]
    rows = []
    for r in a.rows:
        keep = [u for u in r if not primaries_only or a.units[u].role in PRIMARY_ROLES]
        floating += [u for u in r if u not in keep]
        if keep:
            rows.append(keep)
    return rows, floating


def margin(tw, th):
    return max(2.0, 0.05 * min(tw, th))


def k_cap(a, tw, th, cap):
    return cap * math.sqrt(tw * th / (a.sw * a.sh))


def quiet_regions(a, tw, th):
    """Candidate text regions (60% bands and the centre), quietest first, judged by
    the mean gradient of the background image as the renderer will crop it.
    Empty when there is no background image (nothing to be quiet against)."""
    bg = next((a.els[i] for i in a.background if a.els[i]["type"] == "image"), None)
    path = assets_dir() / bg["asset_id"] if bg else None
    if not path or not path.is_file():
        return []
    try:
        img = Image.open(path).convert("L")
    except OSError:
        return []
    s = max(tw / img.width, th / img.height)  # same centred cover crop as the renderer
    cw, ch = tw / s, th / s
    img = img.crop((round((img.width - cw) / 2), round((img.height - ch) / 2),
                    round((img.width + cw) / 2), round((img.height + ch) / 2)))
    gw = 64
    gh = max(2, round(gw * th / tw))
    g = np.asarray(img.resize((gw, gh)), dtype=np.float64) / 255
    busy = np.abs(np.diff(g, axis=1))[:-1, :] + np.abs(np.diff(g, axis=0))[:, :-1]
    m = margin(tw, th)
    regions = {
        "top": (0, 0, 1, 0.6), "bottom": (0, 0.4, 1, 1), "left": (0, 0, 0.6, 1),
        "right": (0.4, 0, 1, 1), "centre": (0.15, 0.15, 0.85, 0.85),
    }
    scored = []
    for fx0, fy0, fx1, fy1 in regions.values():
        r0, r1 = int(fy0 * (gh - 1)), max(int(fy0 * (gh - 1)) + 1, int(fy1 * (gh - 1)))
        c0, c1 = int(fx0 * (gw - 1)), max(int(fx0 * (gw - 1)) + 1, int(fx1 * (gw - 1)))
        box = (max(m, fx0 * tw), max(m, fy0 * th), min(tw - m, fx1 * tw), min(th - m, fy1 * th))
        scored.append((float(busy[r0:r1, c0:c1].mean()), box))
    return [box for _b, box in sorted(scored)]
