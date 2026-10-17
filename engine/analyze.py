"""Understand a source design before re-laying it out.

Everything here works from geometry, element types and text content only, with no
knowledge of particular designs or ids. Steps:

1. Background: elements that cover the whole canvas (within 1% of each side) and sit
   at the bottom of the stacking order.
2. Rigid units (union-find; each unit then moves and scales as one piece):
   - elements sharing a group_id
   - text whose drawn lines sit >= 90% inside a lower shape that covers
     < 25% of the canvas (a button or badge)
   - a non-text element >= 90% inside such a shape (an icon on a card)
   - a decoration whose area is >= 80% inside a content unit (tight layering)
3. Decorations: ungrouped shapes that contain nothing and are faint (effective
   alpha < 0.5), lines, or bleed off the canvas. They are not laid out, only
   re-anchored afterwards.
4. Roles, each with a confidence (rules in `_assign_roles`):
   headline / subhead / body / fineprint / cta / logo / hero / badge / decoration.
5. Importance = role base x (0.8 + 0.2 x confidence) + up to 0.1 for relative area,
   + up to EMPHASIS_BOOST for a unit whose colour stands out from the palette
   (eval.score.emphasis: saturated and far from the main colours).
   Floating units that partly cover a bigger unit (a ribbon across a card) are
   attached to it: `host` and their centre's position inside it (`rel`).
   Every unit records which side of its anchor (host centre, else canvas centre)
   it sits on (`side`), so a rotated unit moved to the mirrored side can mirror its tilt.
6. Relationships: containment pairs, shared alignment edges/centres, canvas-edge
   anchoring, reading-order rows and size order.
"""

import re
from collections import Counter
from dataclasses import dataclass, field

from eval.check import rotated_bbox, text_layout
from eval.score import ATTACH_MIN, emphasis
from renderer.converter.colorutil import parse_rgba

ACTION_WORDS = {
    "shop", "buy", "get", "order", "learn", "discover", "explore", "try", "start", "join", "sign", "subscribe",
    "download", "book", "register", "call", "visit", "save", "claim", "apply", "donate", "watch", "read", "see",
    "find", "contact", "reserve", "grab", "upgrade", "install", "play", "listen", "enroll", "rsvp",
}
ROLE_BASE = {"headline": 1.0, "hero": 0.9, "cta": 0.85, "logo": 0.75, "subhead": 0.6, "body": 0.45,
             "badge": 0.35, "fineprint": 0.2, "decoration": 0.1}
PRIMARY_ROLES = ("headline", "cta", "logo", "hero")
FILL_TOLERANCE = 0.01
EDGE_ZONE = 0.12        # a box edge within 12% of a canvas side counts as anchored to it
CONTAINER_MAX_AREA = 0.25
DECORATION_ALPHA = 0.5  # same threshold as eval.score
EMPHASIS_BOOST = 0.15


@dataclass
class Unit:
    id: str
    members: list            # element ids, bottom-to-top
    kind: str                # "text" | "image" | "rigid"
    box: tuple               # source union of (rotated) boxes, x0 y0 x1 y1
    drawn: tuple = ()        # source union of what is drawn (text = its lines)
    role: str = "body"
    confidence: float = 0.5
    importance: float = 0.5
    edges: tuple = ()        # subset of ("left", "right", "top", "bottom")
    floating: bool = False   # placed into leftover space after the main layout
    rotated: bool = False
    emphasis: float = 0.0    # 0..1, colour stands out from the design's palette
    host: str | None = None  # unit this floating unit is attached to
    rel: tuple = ()          # its drawn centre as a fraction of the host's drawn box
    side: tuple = (1, 1)     # side of its anchor it sits on (x, y), each +-1

    @property
    def w(self):
        return self.box[2] - self.box[0]

    @property
    def h(self):
        return self.box[3] - self.box[1]

    @property
    def corner(self):
        horiz = "left" if "left" in self.edges else "right" if "right" in self.edges else None
        vert = "top" if "top" in self.edges else "bottom" if "bottom" in self.edges else None
        return f"{vert}-{horiz}" if horiz and vert else None


@dataclass
class Analysis:
    source: dict
    sw: float
    sh: float
    els: dict                # id -> source element
    background: list         # element ids
    decorations: list        # Units
    units: dict              # uid -> content Unit
    rows: list               # reading-order rows of non-floating unit ids
    relations: dict = field(default_factory=dict)
    text_align: str = "center"

    def by_role(self, role):
        return next((u for u in self.units.values() if u.role == role), None)

    def anchor(self, u):
        """Source centre of a unit as a fraction of the canvas."""
        return ((u.box[0] + u.box[2]) / 2 / self.sw, (u.box[1] + u.box[3]) / 2 / self.sh)


def element_box(el):
    """What the renderer draws: rotated bounds, laid-out lines for text."""
    if el.get("rotation", 0):
        return rotated_bbox(el)
    if el["type"] == "text":
        lay = text_layout(el)
        if lay["lines"]:
            return (el["x"] + lay["left"], el["y"], el["x"] + lay["right"], el["y"] + lay["height"])
    return (el["x"], el["y"], el["x"] + el["width"], el["y"] + el["height"])


def full_box(el):
    """What has to stay on the canvas: the box itself and, when rotated, its
    rotated bounds too (check() tests both, as the official self-check tests the box)."""
    box = (el["x"], el["y"], el["x"] + el["width"], el["y"] + el["height"])
    return _union([box, rotated_bbox(el)]) if el.get("rotation", 0) else box


def analyze(source):
    els = {e["id"]: e for e in source["elements"]}
    sw, sh = source["canvas"]["width"], source["canvas"]["height"]
    z = {i: (e.get("z_index", 0), n) for n, (i, e) in enumerate(els.items())}

    background = _background(els, z, sw, sh)
    rest = [i for i in els if i not in background]

    parent = {i: i for i in rest}

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(a, b):
        parent[find(a)] = find(b)

    by_group = {}
    for i in rest:
        if els[i].get("group_id"):
            by_group.setdefault(els[i]["group_id"], []).append(i)
    for members in by_group.values():
        for m in members[1:]:
            union(members[0], m)

    containment = []
    shapes = [i for i in rest if els[i]["type"] == "shape" and _alpha(els[i]) >= DECORATION_ALPHA
              and _area(full_box(els[i])) < CONTAINER_MAX_AREA * sw * sh and not _bleeds(full_box(els[i]), sw, sh)]
    for i in rest:
        inner = element_box(els[i])
        for s in shapes:
            if s != i and z[s] < z[i] and _inside(inner, full_box(els[s])) >= 0.9:
                containment.append((s, i))
                union(s, i)
                break

    clusters = {}
    for i in rest:
        clusters.setdefault(find(i), []).append(i)

    decorations, units = [], {}
    for members in clusters.values():
        members.sort(key=lambda m: z[m])
        if len(members) == 1 and _is_decoration(els[members[0]], containment, sw, sh):
            decorations.append(_make_unit(members[0], members, els))
        else:
            uid = next((els[m]["group_id"] for m in members if els[m].get("group_id")), members[0]) if len(members) > 1 else members[0]
            units[uid] = _make_unit(uid, members, els)

    # tightly layered decorations travel with the unit they sit on
    for d in list(decorations):
        host = max(units.values(), key=lambda u: _inside(d.box, u.box), default=None)
        if host and _inside(d.box, host.box) >= 0.8 and _area(d.box) < _area(host.box):
            host.members = sorted(host.members + d.members, key=lambda m: z[m])
            host.box, host.drawn = _union([host.box, d.box]), _union([host.drawn, d.drawn])
            host.kind = "rigid"
            decorations.remove(d)

    for u in [*units.values(), *decorations]:
        u.edges = tuple(e for e, near in (("left", u.box[0] <= EDGE_ZONE * sw), ("right", u.box[2] >= (1 - EDGE_ZONE) * sw),
                                         ("top", u.box[1] <= EDGE_ZONE * sh), ("bottom", u.box[3] >= (1 - EDGE_ZONE) * sh)) if near)
    for d in decorations:
        d.role, d.confidence, d.importance = "decoration", 0.8, ROLE_BASE["decoration"]

    _assign_roles(units, els, sw, sh)
    sal = emphasis(source)
    for u in units.values():
        area_bonus = 0.1 * min(1.0, 4 * _area(u.box) / (sw * sh))
        u.emphasis = max(sal.get(m, 0.0) for m in u.members)
        u.importance = round(ROLE_BASE[u.role] * (0.8 + 0.2 * u.confidence) + area_bonus + EMPHASIS_BOOST * u.emphasis, 4)
        # small badges pinned to a corner, rotated stickers and loose graphics are placed after the main layout
        u.floating = u.role in ("badge", "decoration") and (u.corner is not None or u.rotated) or u.role == "decoration"
    _attach(units)
    for u in [*units.values(), *decorations]:
        h = units[u.host].drawn if u.host else (0, 0, sw, sh)
        u.side = side_of(u.drawn, h)

    rows = reading_rows({uid: u.drawn for uid, u in units.items() if not u.floating})
    aligns = Counter()  # dominant text alignment, weighted by characters
    for e in els.values():
        if e["type"] == "text" and e["id"] not in background:
            aligns[e.get("text_align", "left")] += len(e["content"])

    return Analysis(
        source=source, sw=sw, sh=sh, els=els, background=background, decorations=decorations, units=units,
        rows=rows, text_align=aligns.most_common(1)[0][0] if aligns else "center",
        relations={
            "containment": containment,
            "alignment": _alignments(units),
            "anchors": {uid: u.edges for uid, u in units.items()},
            "reading_order": [uid for row in rows for uid in row],
            "size_order": sorted(units, key=lambda uid: -_area(units[uid].box)),
        },
    )


def side_of(b, ref):
    """Which side of box ref's centre the centre of box b is on: (+-1, +-1)."""
    return (1 if b[0] + b[2] >= ref[0] + ref[2] else -1, 1 if b[1] + b[3] >= ref[1] + ref[3] else -1)


def _attach(units):
    """A badge or decoration that partly covers a bigger non-floating unit (ATTACH_MIN
    to 90% of its area, or any share when rotated) travels with that unit."""
    for u in units.values():
        if u.role not in ("badge", "decoration"):
            continue
        best, share = None, 0.0
        for v in units.values():
            if v is u or v.floating or _area(v.drawn) <= _area(u.drawn):
                continue
            r = _inside(u.drawn, v.drawn)
            if r > share:
                best, share = v, r
        if best is not None and share >= ATTACH_MIN and (share < 0.9 or u.rotated):
            hb, b = best.drawn, u.drawn
            u.floating, u.host = True, best.id
            u.rel = (((b[0] + b[2]) / 2 - hb[0]) / max(hb[2] - hb[0], 1e-6),
                     ((b[1] + b[3]) / 2 - hb[1]) / max(hb[3] - hb[1], 1e-6))


def reading_rows(boxes):
    """Group boxes into rows (vertical overlap >= half the smaller height), top to
    bottom, left to right within a row. Returns lists of keys."""
    rows = []
    for key, b in sorted(boxes.items(), key=lambda kv: kv[1][1]):
        h = b[3] - b[1]
        if rows:
            top, bottom = rows[-1]["span"]
            overlap = min(bottom, b[3]) - max(top, b[1])
            if overlap >= 0.5 * max(1e-6, min(h, bottom - top)):
                rows[-1]["items"].append((key, b))
                rows[-1]["span"] = (min(top, b[1]), max(bottom, b[3]))
                continue
        rows.append({"span": (b[1], b[3]), "items": [(key, b)]})
    return [[k for k, _b in sorted(r["items"], key=lambda kb: kb[1][0])] for r in rows]


def _background(els, z, sw, sh):
    tol_x, tol_y = FILL_TOLERANCE * sw, FILL_TOLERANCE * sh
    fills = {i for i, e in els.items()
             if e["type"] in ("image", "shape") and not e.get("rotation", 0)
             and e["x"] <= tol_x and e["y"] <= tol_y and e["x"] + e["width"] >= sw - tol_x and e["y"] + e["height"] >= sh - tol_y}
    bg = []
    for i in sorted(els, key=lambda i: z[i]):  # consecutive fills from the bottom of the stack
        if i not in fills:
            break
        bg.append(i)
    return bg


def _is_decoration(el, containment, sw, sh):
    if el["type"] != "shape" or el.get("group_id") or any(c == el["id"] for c, _ in containment):
        return False
    return _alpha(el) < DECORATION_ALPHA or el.get("shape_type") == "line" or _bleeds(full_box(el), sw, sh)


def _alpha(el):
    return el.get("opacity", 1) * parse_rgba(el.get("fill_color"), default=(0, 0, 0, 1.0))[3]


def _bleeds(b, sw, sh):
    return b[0] < -0.5 or b[1] < -0.5 or b[2] > sw + 0.5 or b[3] > sh + 0.5


def _make_unit(uid, members, els):
    boxes = [full_box(els[m]) for m in members]
    rotated = any(els[m].get("rotation", 0) for m in members)
    if len(members) == 1 and not rotated and els[members[0]]["type"] in ("text", "image"):
        kind = els[members[0]]["type"]
    else:
        kind = "rigid"
    return Unit(id=uid, members=members, kind=kind, box=_union(boxes), drawn=_union([element_box(els[m]) for m in members]),
                rotated=rotated)


def _union(boxes):
    return (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))


def _assign_roles(units, els, sw, sh):
    """Role rules, in priority order:
    headline  unit holding the largest-font text (ties: larger box); confidence grows
              with how much larger it is than the runner-up
    cta       shape+text unit whose text has an action verb (0.9); otherwise the lowest,
              widest shape+text unit if it's in the bottom 40% (0.6); or a short (<= 5 words)
              standalone text starting with an action verb (0.7)
    badge     other shape+text units (rotated ones 0.8), and small images that aren't the logo
    hero      largest image covering >= 5% of the canvas (confidence by size)
    logo      topmost remaining image under 8% of the canvas that is wide (aspect >= 1.3)
              or touches the top/bottom zone
    fineprint text with font <= 0.6 x median, or smallest font + >= 60 chars + bottom zone
    subhead   largest remaining text with >= 15 chars
    body      any other text
    decoration shapes or graphics with no text (they float into leftover space)
    """
    texts = [(u, els[i]) for u in units.values() for i in u.members if els[i]["type"] == "text"]
    if texts:
        ranked = sorted(texts, key=lambda t: (t[1]["font_size"], t[1]["width"] * t[1]["height"]), reverse=True)
        head = ranked[0]
        runner = next((t[1]["font_size"] for t in ranked[1:] if t[0] is not head[0]), None)
        head[0].role = "headline"
        head[0].confidence = 1.0 if runner is None else min(1.0, 0.5 + (head[1]["font_size"] / runner - 1))

    def unit_text(u):
        return " ".join(els[i]["content"] for i in u.members if els[i]["type"] == "text")

    def has_action(text):
        words = re.findall(r"[a-z]+", text.lower())
        return any(w in ACTION_WORDS for w in words[:3])

    containers = [u for u in units.values() if u.role != "headline" and u.kind == "rigid"
                  and any(els[i]["type"] == "shape" for i in u.members) and any(els[i]["type"] == "text" for i in u.members)]
    cta = next((u for u in containers if not u.rotated and has_action(unit_text(u))), None)
    if cta:
        cta.role, cta.confidence = "cta", 0.9
    else:
        plain = [u for u in containers if not u.rotated and u.box[1] >= 0.6 * sh]
        if plain:
            cta = max(plain, key=lambda u: (u.box[3], u.w))
            cta.role, cta.confidence = "cta", 0.6
    for u in containers:
        if u is not cta:
            u.role, u.confidence = "badge", 0.8 if u.rotated else 0.6

    images = sorted((u for u in units.values() if u.kind == "image"), key=lambda u: -_area(u.box))
    hero = images[0] if images and _area(images[0].box) >= 0.05 * sw * sh else None
    if hero:
        hero.role, hero.confidence = "hero", min(1.0, 0.5 + _area(hero.box) / (sw * sh))
    small = sorted((u for u in images if u is not hero and _area(u.box) < 0.08 * sw * sh), key=lambda u: u.box[1])
    logo = next((u for u in small if u.w / max(u.h, 1e-6) >= 1.3 or "top" in u.edges or "bottom" in u.edges), None)
    if logo:
        logo.role, logo.confidence = "logo", 0.8 if logo.w / max(logo.h, 1e-6) >= 2 else 0.6
    for u in images:
        if u.role == "body":  # untouched default
            u.role, u.confidence = "badge", 0.5

    rest = [(u, els[u.members[0]]) for u in units.values() if u.role == "body" and u.kind == "text"]
    sizes = sorted(e["font_size"] for _u, e in texts) if texts else [0]
    median = sizes[len(sizes) // 2]
    for u, e in rest:
        words = e["content"].split()
        if len(words) <= 5 and has_action(e["content"]) and not cta:
            u.role, u.confidence, cta = "cta", 0.7, u
        elif e["font_size"] <= 0.6 * median or (e["font_size"] == sizes[0] and len(e["content"]) >= 60 and u.box[3] >= 0.85 * sh):
            u.role, u.confidence = "fineprint", 0.7
    rest = sorted((t for t in rest if t[0].role == "body"), key=lambda t: -t[1]["font_size"])
    if rest and len(rest[0][1]["content"]) >= 15:
        rest[0][0].role, rest[0][0].confidence = "subhead", 0.6

    for u in units.values():
        if u.role == "body" and not any(els[i]["type"] == "text" for i in u.members):
            u.role, u.confidence = "decoration", 0.5


def _alignments(units, tol=2.0):
    out = []
    items = [(uid, u.drawn) for uid, u in units.items() if not u.floating]
    for n, (a, ba) in enumerate(items):
        for b, bb in items[n + 1:]:
            for name, va, vb in (("left", ba[0], bb[0]), ("right", ba[2], bb[2]), ("center_x", ba[0] + ba[2], bb[0] + bb[2]),
                                 ("top", ba[1], bb[1]), ("bottom", ba[3], bb[3]), ("center_y", ba[1] + ba[3], bb[1] + bb[3])):
                if abs(va - vb) <= (2 * tol if name.startswith("center") else tol):
                    out.append((a, b, name))
    return out


def _area(b):
    return max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])


def _inside(inner, outer):
    """Fraction of `inner`'s area that lies inside `outer`."""
    a = _area(inner)
    if a <= 0:
        return 0.0
    return _area((max(inner[0], outer[0]), max(inner[1], outer[1]), min(inner[2], outer[2]), min(inner[3], outer[3]))) / a
