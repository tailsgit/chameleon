"""Damaged versions of a good layout: the negatives critic.make_data pairs with it.

Each damage takes (a, output, rng) -- a = engine.analyze of the source, output = a good layout of it
(the source itself at its own size, or a good resize) -- and returns a damaged deep copy, or None when
it doesn't apply to this design (no panel, no hero, nothing aligned...). Moved elements are pulled back
inside the canvas where they fit, so most negatives are wrong in layout, not in the hard rules.
"""

import copy
import math

PANEL_OFF = 0.5  # text_off_panel must leave at most this share of the text on its panel


def _els(out):
    return {e["id"]: e for e in out["elements"]}


def box(els, ids):
    bs = [(e["x"], e["y"], e["x"] + e["width"], e["y"] + e["height"]) for i in ids if (e := els.get(i))]
    return (min(b[0] for b in bs), min(b[1] for b in bs), max(b[2] for b in bs), max(b[3] for b in bs)) if bs else None


def move(els, ids, dx, dy):
    for i in ids:
        if i in els:
            els[i]["x"] += dx
            els[i]["y"] += dy


def scale(els, ids, f, cx, cy):
    for i in ids:
        if i in els:
            e = els[i]
            e.update(x=cx + (e["x"] - cx) * f, y=cy + (e["y"] - cy) * f, width=e["width"] * f, height=e["height"] * f)
            if e["type"] == "text":
                e["font_size"] = max(1, int(round(e["font_size"] * f)))
                if e.get("letter_spacing"):
                    e["letter_spacing"] *= f


def clamp(els, ids, tw, th):
    """Shift the group back inside the canvas when it fits."""
    b = box(els, ids)
    if not b:
        return
    dx = -b[0] if b[0] < 0 else tw - b[2] if b[2] > tw else 0.0
    dy = -b[1] if b[1] < 0 else th - b[3] if b[3] > th else 0.0
    if b[2] - b[0] <= tw and b[3] - b[1] <= th:
        move(els, ids, dx, dy)


def _content(a):
    """Ids of everything but the background."""
    return [i for i in a.els if i not in set(a.background)]


def _units(a, min_members=1):
    return [u for u in list(a.units.values()) + list(a.decorations) if len(u.members) >= min_members]


def _canvas(out):
    return float(out["canvas"]["width"]), float(out["canvas"]["height"])


def bare_canvas(a, out, rng):
    """Background shrunk to part of the canvas, or (no background) the content shrunk to the middle."""
    out = copy.deepcopy(out)
    els, (tw, th) = _els(out), _canvas(out)
    bg = [i for i in a.background if i in els]
    if bg:
        f = rng.uniform(0.45, 0.65)
        for i in bg:
            e = els[i]
            e.update(width=e["width"] * f, height=e["height"] * f)
            e.update(x=rng.uniform(0, max(0.0, tw - e["width"])), y=rng.uniform(0, max(0.0, th - e["height"])))
    else:
        scale(els, _content(a), rng.uniform(0.45, 0.6), tw / 2, th / 2)
    return out


def text_off_panel(a, out, rng):
    """The text on a panel (flat card) moved beside it."""
    out = copy.deepcopy(out)
    els, (tw, th) = _els(out), _canvas(out)
    choices = [(p, [i for i in ids if i in els and els[i]["type"] == "text"]) for p, ids in a.panels.items() if p in els]
    choices = [(p, t) for p, t in choices if t]
    if not choices:
        return None
    p, texts = choices[rng.randrange(len(choices))]
    pb, tb = box(els, [p]), box(els, texts)
    side = rng.choice(("left", "right", "above", "below"))
    gap = 0.02 * min(tw, th)
    dx = {"left": pb[0] - gap - tb[2], "right": pb[2] + gap - tb[0]}.get(side, 0.0)
    dy = {"above": pb[1] - gap - tb[3], "below": pb[3] + gap - tb[1]}.get(side, 0.0)
    move(els, texts, dx, dy)
    clamp(els, texts, tw, th)
    nb = box(els, texts)
    inside = max(0.0, min(nb[2], pb[2]) - max(nb[0], pb[0])) * max(0.0, min(nb[3], pb[3]) - max(nb[1], pb[1]))
    return out if inside <= PANEL_OFF * (nb[2] - nb[0]) * (nb[3] - nb[1]) else None


def shrunken_hero(a, out, rng):
    """The hero image (else the largest image unit) shrunk about its centre."""
    hero = a.by_role("hero") or max((u for u in a.units.values() if u.kind == "image"),
                                    key=lambda u: u.w * u.h, default=None)
    if hero is None:
        return None
    out = copy.deepcopy(out)
    els = _els(out)
    b = box(els, hero.members)
    if not b:
        return None
    scale(els, hero.members, rng.uniform(0.35, 0.6), (b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
    return out


def split_group(a, out, rng):
    """One member of a group (a rigid unit, or a part of a sibling row / grid) pulled away from the rest."""
    groups = [[list(p[0]) for p in u.parts] for u in a.units.values() if len(u.parts) >= 2]
    groups += [[[m] for m in u.members] for u in _units(a, 2) if not u.parts]
    if not groups:
        return None
    out = copy.deepcopy(out)
    els, (tw, th) = _els(out), _canvas(out)
    parts = groups[rng.randrange(len(groups))]
    part = parts[rng.randrange(len(parts))]
    ang, dist = rng.uniform(0, 2 * math.pi), rng.uniform(0.15, 0.35)
    move(els, part, math.cos(ang) * dist * tw, math.sin(ang) * dist * th)
    clamp(els, part, tw, th)
    return out


def corner_crowding(a, out, rng):
    """All content shrunk towards one corner of the canvas."""
    out = copy.deepcopy(out)
    els, (tw, th) = _els(out), _canvas(out)
    m = 0.04 * min(tw, th)
    cx, cy = rng.choice((m, tw - m)), rng.choice((m, th - m))
    scale(els, _content(a), rng.uniform(0.4, 0.6), cx, cy)
    return out


def random_overlap(a, out, rng):
    """One unit moved on top of another."""
    units = [u for u in _units(a) if u.w * u.h > 0.005 * a.sw * a.sh]
    if len(units) < 2:
        return None
    out = copy.deepcopy(out)
    els, (tw, th) = _els(out), _canvas(out)
    u, v = rng.sample(units, 2)
    bu, bv = box(els, u.members), box(els, v.members)
    if not bu or not bv:
        return None
    jx, jy = rng.uniform(-0.05, 0.05) * tw, rng.uniform(-0.05, 0.05) * th
    move(els, u.members, (bv[0] + bv[2] - bu[0] - bu[2]) / 2 + jx, (bv[1] + bv[3] - bu[1] - bu[3]) / 2 + jy)
    clamp(els, u.members, tw, th)
    return out


def misalignment(a, out, rng):
    """Units that shared a left, centre or right edge each nudged sideways by 2-6% of the width."""
    out = copy.deepcopy(out)
    els, (tw, th) = _els(out), _canvas(out)
    units = [(u, box(els, u.members)) for u in a.units.values()]
    units = [(u, b) for u, b in units if b]
    tol = 0.005 * tw
    aligned = set()
    for i, (u, b) in enumerate(units):
        for v, c in units[i + 1:]:
            if any(abs(p - q) <= tol for p, q in ((b[0], c[0]), (b[2], c[2]), ((b[0] + b[2]) / 2, (c[0] + c[2]) / 2))):
                aligned |= {u.id, v.id}
    pick = [u for u, _b in units if u.id in aligned] or [u for u, _b in units if u.kind == "text"]
    if len(pick) < 2:
        return None
    for u in pick:
        move(els, u.members, rng.choice((-1, 1)) * rng.uniform(0.02, 0.06) * tw, 0.0)
        clamp(els, u.members, tw, th)
    return out


def reading_order(a, out, rng):
    """A unit of the first reading row and one of the last swap vertical positions."""
    rows = [r for r in a.rows if r]
    if len(rows) < 2:
        return None
    out = copy.deepcopy(out)
    els = _els(out)
    u, v = a.units[rng.choice(rows[0])], a.units[rng.choice(rows[-1])]
    bu, bv = box(els, u.members), box(els, v.members)
    if not bu or not bv:
        return None
    move(els, u.members, 0.0, bv[1] - bu[1])
    move(els, v.members, 0.0, bu[1] - bv[1])
    tw, th = _canvas(out)
    clamp(els, u.members, tw, th)
    clamp(els, v.members, tw, th)
    return out


def naive_stretch(source, target):
    """Every box scaled by the width and height ratios independently, fonts by the smaller (no repair)."""
    sx, sy = target["width"] / source["canvas"]["width"], target["height"] / source["canvas"]["height"]
    out = {"canvas": dict(width=target["width"], height=target["height"]), "elements": copy.deepcopy(source["elements"])}
    for e in out["elements"]:
        e.update(x=e["x"] * sx, y=e["y"] * sy, width=e["width"] * sx, height=e["height"] * sy)
        if e["type"] == "text":
            e["font_size"] = max(1, int(e["font_size"] * min(sx, sy)))
    return out


DAMAGES = {f.__name__: f for f in (bare_canvas, text_off_panel, shrunken_hero, split_group, corner_crowding,
                                   random_overlap, misalignment, reading_order)}
KINDS = ("positive", *DAMAGES, "naive_stretch", "engine_low")  # example kinds, by index in the shards
