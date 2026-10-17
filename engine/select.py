"""Choose the winning candidate, and the safety nets behind it.

1. Drop duplicate candidates and any with a hard-rule violation (eval.check).
2. Rank the rest by the geometric score (eval.score, ~1 ms each), render the top
   RENDER_TOP and pick the best full score including contrast. Rendering is
   expensive under amd64 emulation, so only those few get rendered.
3. If nothing passes: repair every candidate (pull into the canvas, fix image
   proportions, shrink text until it fits) plus a uniform-scale fallback, and return
   the one with the fewest violations, then the best score.
"""

import copy
import json
import logging
import math

from engine.analyze import full_box
from eval.check import check, text_layout
from eval.score import score

RENDER_TOP = 10
log = logging.getLogger(__name__)


def select(source, target, outputs):
    seen, unique = set(), []
    for o in outputs:
        key = json.dumps(o, sort_keys=True)
        if key not in seen:
            seen.add(key)
            unique.append(o)

    passing = [(o, score(source, target, o)["total"]) for o in unique if _passes(source, target, o)]
    if passing:
        top = sorted(passing, key=lambda t: -t[1])[:RENDER_TOP]
        try:
            return max(top, key=lambda t: score(source, target, t[0], contrast=True)["total"])[0]
        except Exception:  # the renderer is unavailable: fall back to the geometric ranking
            log.exception("contrast scoring failed; using geometric ranking")
            return top[0][0]

    log.warning("no candidate passed check(); repairing %d candidates", len(unique))
    repaired = [repair(source, target, o) for o in unique] + [fallback(source, target)]
    def badness(o):
        try:
            return len(check(source, target, o)), -score(source, target, o)["total"]
        except Exception:
            return math.inf, 0
    return min(repaired, key=badness)


def _passes(source, target, output):
    try:
        return not check(source, target, output)
    except Exception:
        log.exception("check() failed on a candidate; discarding it")
        return False


def fallback(source, target):
    """Uniform scale of the whole design (nothing distorts, wrapping is unchanged),
    centred, background full canvas, then repaired."""
    sw, sh = source["canvas"]["width"], source["canvas"]["height"]
    tw, th = target["width"], target["height"]
    s = min(tw / sw, th / sh)
    ox, oy = (tw - sw * s) / 2, (th - sh * s) / 2
    out = {"canvas": {"width": tw, "height": th}, "elements": copy.deepcopy(source["elements"])}
    for el in out["elements"]:
        el.update(x=ox + el["x"] * s, y=oy + el["y"] * s, width=el["width"] * s, height=el["height"] * s)
        if el["type"] == "text":
            el["font_size"] = max(1, math.floor(el["font_size"] * s))
    return repair(source, target, out)


def repair(source, target, output):
    """Best-effort fix of every hard rule we can fix locally. Never raises."""
    tw, th = target["width"], target["height"]
    sw, sh = source["canvas"]["width"], source["canvas"]["height"]
    src = {e["id"]: e for e in source["elements"]}
    out = copy.deepcopy(output)
    out["canvas"] = {"width": tw, "height": th}
    for el in out["elements"]:
        s = src.get(el.get("id"))
        if s is None:
            continue
        try:
            _repair_element(el, s, sw, sh, tw, th)
        except Exception:
            log.exception("repair failed for %s", el.get("id"))
    return out


def _repair_element(el, s, sw, sh, tw, th):
    fills_src = s["x"] <= 1 and s["y"] <= 1 and s["x"] + s["width"] >= sw - 1 and s["y"] + s["height"] >= sh - 1
    if fills_src and el["type"] in ("image", "shape") and not el.get("rotation", 0):
        if el["type"] == "shape" or el.get("fit", "contain") == "cover":
            el.update(x=0, y=0, width=tw, height=th)
            return
    el["width"], el["height"] = max(1.0, el["width"]), max(1.0, el["height"])
    if el["type"] == "image" and el.get("fit", "contain") != "cover" and s["width"] > 0 and s["height"] > 0:
        ar = s["width"] / s["height"]
        cx, cy = el["x"] + el["width"] / 2, el["y"] + el["height"] / 2
        w = min(el["width"], el["height"] * ar)
        el.update(width=w, height=w / ar)
        el.update(x=cx - el["width"] / 2, y=cy - el["height"] / 2)

    b = full_box(el)
    bw, bh = b[2] - b[0], b[3] - b[1]
    if bw > tw or bh > th:
        f = 0.999 * min(tw / bw, th / bh)
        cx, cy = el["x"] + el["width"] / 2, el["y"] + el["height"] / 2
        el.update(width=el["width"] * f, height=el["height"] * f)
        el.update(x=cx - el["width"] / 2, y=cy - el["height"] / 2)
        if el["type"] == "text":
            el["font_size"] = max(1, math.floor(el["font_size"] * f))
        b = full_box(el)
    dx = -b[0] if b[0] < 0 else (tw - b[2] if b[2] > tw else 0)
    dy = -b[1] if b[1] < 0 else (th - b[3] if b[3] > th else 0)
    el.update(x=el["x"] + dx, y=el["y"] + dy)

    if el["type"] == "text":
        def fits(fs):
            lay = text_layout(dict(el, font_size=fs))
            return lay["left"] >= -0.5 and lay["right"] <= el["width"] + 0.5 and lay["height"] <= el["height"] + 0.5
        fs = int(el["font_size"])
        while fs > 1 and not fits(fs):
            fs -= 1
        el["font_size"] = max(1, fs)
        if not fits(el["font_size"]):  # still too big at this size: grow the box, keeping it on the canvas
            lay = text_layout(el)
            w = min(tw, max(el["width"], lay["right"] - min(0.0, lay["left"]) + 1))
            el.update(width=w, x=min(max(0.0, el["x"] + min(0.0, lay["left"])), tw - w))
            h = min(th, text_layout(el)["height"] + 1)
            el.update(height=h, y=min(el["y"], th - h))
