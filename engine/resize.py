"""Chameleon engine v1: analyse -> generate layout candidates -> realise -> select.

See engine/analyze.py, recipes.py, fit.py and select.py. resize() never raises:
when the pipeline fails it falls back to a repaired uniform scale, and failing
that, to a repaired stretch. When the aspect ratio barely changes, the uniform
scale is also the preferred candidate: the designer's layout already fits.
"""

import copy
import logging
from typing import Any

from engine.analyze import analyze
from engine.fit import realize
from engine.recipes import generate
from engine.select import fallback, repair, select

SAME_ASPECT = 0.02  # relative aspect-ratio change below which the source layout is kept as is
log = logging.getLogger(__name__)


def resize(source: dict[str, Any], target_canvas: dict[str, Any]) -> dict[str, Any]:
    target = {"width": int(target_canvas["width"]), "height": int(target_canvas["height"])}
    try:
        a = analyze(source)
        outputs = []
        for plan in generate(a, target["width"], target["height"]):
            try:
                outputs.append(realize(a, plan, target["width"], target["height"]))
            except Exception:
                log.exception("recipe %s %s failed", plan.recipe, plan.knobs)
        preferred = None
        sa = source["canvas"]["width"] / source["canvas"]["height"]
        if abs(target["width"] / target["height"] / sa - 1) <= SAME_ASPECT:
            preferred = fallback(source, target)
        if outputs or preferred is not None:
            return select(source, target, outputs, preferred)
        log.warning("no candidates; using fallback")
    except Exception:
        log.exception("engine failed; using fallback")
    try:
        return fallback(source, target)
    except Exception:
        log.exception("fallback failed; using repaired stretch")
        return _stretch(source, target)


def _stretch(source, target):
    sx = target["width"] / source["canvas"]["width"]
    sy = target["height"] / source["canvas"]["height"]
    out = {"canvas": dict(target), "elements": copy.deepcopy(source["elements"])}
    for el in out["elements"]:
        el.update(x=el["x"] * sx, y=el["y"] * sy, width=el["width"] * sx, height=el["height"] * sy)
        if el["type"] == "text":
            el["font_size"] = max(1, int(el["font_size"] * min(sx, sy)))
    try:
        return repair(source, target, out)
    except Exception:
        return out
