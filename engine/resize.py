"""Chameleon engine v1: analyse -> generate layout candidates -> realise -> select.

See engine/analyze.py, recipes.py, fit.py and select.py. resize() never raises:
when the pipeline fails it falls back to a repaired uniform scale, and failing
that, to a repaired stretch. When the aspect ratio barely changes, the uniform
scale is also the preferred candidate: the designer's layout already fits.

Two limits: a wall-clock budget (BUDGET_S) after which no new candidates are made and
the best so far is chosen, and a guard that drops a retrieved layout which gives the
headline or main image much less of the canvas than the best recipe layout does.
"""

import copy
import logging
import time
from typing import Any

from engine.analyze import analyze
from engine.fit import realize
from engine.recipes import generate
from engine.select import _passes, fallback, repair, select
from eval.score import _area, _drawn_box, key_elements, score

SAME_ASPECT = 0.02  # relative aspect-ratio change below which the source layout is kept as is
BUDGET_S = 14.5     # seconds per case, everything included (the brief's reference: 15 s)
GEN_SHARE = 0.5     # plans are generated in the first half of it...
SELECT_COST = 5     # ...and realising stops while the rest still covers judging every candidate made: the guard
                    # and select check, score and test legibility of each, about this many times (measured as we go)
GUARD = 0.7         # a retrieved layout must give the headline and main image at least this share of the best recipe's
log = logging.getLogger(__name__)


def resize(source: dict[str, Any], target_canvas: dict[str, Any]) -> dict[str, Any]:
    target = {"width": int(target_canvas["width"]), "height": int(target_canvas["height"])}
    start = time.monotonic()
    deadline = start + BUDGET_S
    try:
        a = analyze(source)
        outputs, recipes, per = [], [], 0.0
        for plan in generate(a, target["width"], target["height"], start + GEN_SHARE * BUDGET_S):
            if outputs and time.monotonic() + SELECT_COST * per * len(outputs) > deadline:
                log.info("time budget reached after %d candidates", len(outputs))
                break
            # stand-out floating units: centred in their free space, or near their source side; the scorer picks
            focal = (True, False) if any(a.units[u].emphasis for u in plan.floating) else (True,)
            # text kept on a panel that can't grow by shrinking it, or left overhanging: an extra candidate, not a replacement
            for f, k in [(f, k) for f in focal for k in ((True, False) if a.panels else (True,))]:
                try:
                    outputs.append(realize(a, plan, target["width"], target["height"], focal=f, keep_on_panel=k))
                    recipes.append(plan.recipe)
                    if len(outputs) <= 2:  # what judging one candidate costs on this machine (the second: the first warms the source's caches)
                        t = time.monotonic()
                        _passes(source, target, outputs[-1]) and score(source, target, outputs[-1])
                        per = time.monotonic() - t
                except Exception:
                    log.exception("recipe %s %s failed", plan.recipe, plan.knobs)
        preferred = None
        sa = source["canvas"]["width"] / source["canvas"]["height"]
        if abs(target["width"] / target["height"] / sa - 1) <= SAME_ASPECT:
            preferred = fallback(source, target)
        outputs, recipes = _guard(source, target, outputs, recipes)
        if outputs or preferred is not None:
            best = select(source, target, outputs, preferred, deadline)
            log.info("winner: %s", next((r for o, r in zip(outputs, recipes) if o is best),
                                        "uniform" if best is preferred else "repaired"))
            return best
        log.warning("no candidates; using fallback")
    except Exception:
        log.exception("engine failed; using fallback")
    try:
        return fallback(source, target)
    except Exception:
        log.exception("fallback failed; using repaired stretch")
        return _stretch(source, target)


def _guard(source, target, outputs, recipes):
    """Drop retrieved layouts that shrink the headline's or main image's share of the canvas
    below GUARD x what the best-scoring passing recipe layout gives it."""
    if "retrieved" not in recipes:
        return outputs, recipes
    ranked = [(score(source, target, o)["total"], o) for o, r in zip(outputs, recipes) if r != "retrieved" and _passes(source, target, o)]
    if not ranked:
        return outputs, recipes
    keys = key_elements(source)
    ref = _shares(max(ranked, key=lambda t: t[0])[1], keys)
    keep = [(o, r) for o, r in zip(outputs, recipes)
            if r != "retrieved" or all(s >= GUARD * b for s, b in zip(_shares(o, keys), ref) if b)]
    if len(keep) < len(outputs):
        log.info("guard dropped %d retrieved layouts", len(outputs) - len(keep))
    return [o for o, _r in keep], [r for _o, r in keep]


def _shares(output, keys):
    """Each key element's drawn area as a share of the canvas (None when there is no such element)."""
    els = {e["id"]: e for e in output["elements"]}
    area = output["canvas"]["width"] * output["canvas"]["height"]
    return [_area(_drawn_box(els[k])) / area if k in els else None for k in keys]


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
