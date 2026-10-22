"""Hill-climbing search over finished layouts, judged by the critic (engine.critic_score). Off by default:
engine.resize runs it only when CHAMELEON_CRITIC=1.

Starting from a few layouts (the chosen one, the best other candidates, the best preserve layout), each
round takes the next start state in turn, proposes MOVES_PER_ROUND random moves of one layout unit
(engine.analyze units, moved with all their members):
  move     shift by up to MOVE_STEP of the canvas
  resize   scale about its centre by 1 +- up to SCALE_STEP (text font sizes scale too)
  swap     mirror its position to the other side of the canvas (horizontal on landscape canvases,
           vertical on portrait ones)
  ratio    shift the split between the two halves of the canvas: the units in one half grow by up to
           RATIO_STEP from the outer edge, the other half's shrink towards theirs
  reorder  two units in different reading rows trade places (top-left corners)
drops every proposal that breaks a hard rule (eval.check), scores the rest in one batch, and keeps the best
only if it beats that state's score. Fixed seed; stops at the deadline (engine.clock.now).
This is a skeleton: the moves are deliberately simple and the critic decides what is better.
"""

import copy
import random

from critic.damage import box, move, scale
from engine.clock import now
from engine.critic_score import scores
from engine.select import _passes

MOVES_PER_ROUND = 8
MOVE_STEP, SCALE_STEP, RATIO_STEP = 0.04, 0.12, 0.08
SEED = 0


def search(source, target, a, starts, deadline, seed=SEED, path=None):
    """[(score, output)] for each start state after climbing, best first. Starts must pass check()."""
    rng = random.Random(seed)
    units = [u for u in a.units.values()] + list(a.decorations)
    states = [[s, o] for s, o in zip(scores(source, target, starts, a, path), starts)]
    if not units or not states:
        return sorted(((s, o) for s, o in states), key=lambda t: -t[0])
    k = 0
    while (k < 8 if deadline is None else now() < deadline):
        st = states[k % len(states)]
        k += 1
        props = [p for p in (_propose(a, st[1], units, rng) for _ in range(MOVES_PER_ROUND)) if p is not None]
        props = [p for p in props if _passes(source, target, p)]
        if not props or (deadline is not None and now() >= deadline):
            continue
        sc = scores(source, target, props, a, path)
        j = max(range(len(props)), key=sc.__getitem__)
        if sc[j] > st[0]:
            st[0], st[1] = sc[j], props[j]
    return sorted(((s, o) for s, o in states), key=lambda t: -t[0])


def _propose(a, out, units, rng):
    out = copy.deepcopy(out)
    els = {e["id"]: e for e in out["elements"]}
    tw, th = float(out["canvas"]["width"]), float(out["canvas"]["height"])
    kind = rng.choice(("move", "resize", "swap", "ratio", "reorder"))
    u = rng.choice(units)
    b = box(els, u.members)
    if b is None:
        return None
    if kind == "move":
        move(els, u.members, rng.uniform(-MOVE_STEP, MOVE_STEP) * tw, rng.uniform(-MOVE_STEP, MOVE_STEP) * th)
    elif kind == "resize":
        scale(els, u.members, 1 + rng.uniform(-SCALE_STEP, SCALE_STEP), (b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
    elif kind == "swap":
        if tw >= th:
            move(els, u.members, tw - b[2] - b[0], 0.0)
        else:
            move(els, u.members, 0.0, th - b[3] - b[1])
    elif kind == "ratio":
        d = rng.uniform(-RATIO_STEP, RATIO_STEP)
        wide = tw >= th
        mid = tw / 2 if wide else th / 2
        for v in units:
            c = box(els, v.members)
            if c is None:
                continue
            first = ((c[0] + c[2]) / 2 if wide else (c[1] + c[3]) / 2) < mid
            f = 1 + d if first else 1 - d
            edge = (0.0 if first else tw) if wide else (0.0 if first else th)
            scale(els, v.members, f, edge if wide else (c[0] + c[2]) / 2, (c[1] + c[3]) / 2 if wide else edge)
    else:
        rows = [r for r in a.rows if r]
        if len(rows) < 2:
            return None
        r1, r2 = rng.sample(range(len(rows)), 2)
        u, v = a.units[rng.choice(rows[r1])], a.units[rng.choice(rows[r2])]
        bu, bv = box(els, u.members), box(els, v.members)
        if bu is None or bv is None:
            return None
        move(els, u.members, bv[0] - bu[0], bv[1] - bu[1])
        move(els, v.members, bu[0] - bv[0], bu[1] - bv[1])
    return out
