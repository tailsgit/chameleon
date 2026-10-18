"""engine.retrieve: the assignment it relies on, and retrieved plans that pass the checks."""

from itertools import permutations

import numpy as np
import pytest

import engine.retrieve as retrieve
from engine.analyze import analyze
from engine.fit import realize
from engine.recipes import Sizer
from engine.retrieve import assign
from eval.check import check


@pytest.mark.parametrize("seed", range(20))
def test_assignment_is_optimal(seed):
    rng = np.random.default_rng(seed)
    n, m = int(rng.integers(1, 6)), int(rng.integers(1, 7))
    n = min(n, m)
    cost = rng.random((n, m)) * 10
    pairs = assign(cost)
    assert sorted(i for i, _ in pairs) == list(range(n)) and len({j for _, j in pairs}) == n
    best = min(sum(cost[i, p[i]] for i in range(n)) for p in permutations(range(m), n))
    assert sum(cost[i, j] for i, j in pairs) == pytest.approx(best)


def test_retrieved_plans_map_by_role_and_pass(monkeypatch):
    src = {"canvas": {"width": 1080, "height": 1080}, "elements": [
        {"id": "photo", "type": "image", "x": 0, "y": 0, "width": 1080, "height": 600, "asset_id": "solstice_bottle.png", "fit": "contain", "z_index": 0},
        {"id": "title", "type": "text", "x": 80, "y": 680, "width": 920, "height": 120, "content": "A big title", "font_family": "Solstice Sans",
         "font_size": 80, "color": "rgba(0,0,0,1)", "z_index": 1},
        {"id": "note", "type": "text", "x": 80, "y": 900, "width": 920, "height": 60, "content": "Some smaller words below it", "font_family": "Solstice Sans",
         "font_size": 30, "color": "rgba(0,0,0,1)", "z_index": 1}]}
    a = analyze(src)
    roles = {u.id: u.role for u in a.units.values()}
    # one wide design: photo on the left half, headline top right, body text below it
    lib = [{"aspect": 1.9, "roles": {"hero": 1, "headline": 1, "body": 1}, "units": [
        {"role": "hero", "kind": "image", "box": [0, 0, 0.5, 1]},
        {"role": "headline", "kind": "text", "box": [0.55, 0.1, 0.95, 0.4]},
        {"role": "body", "kind": "text", "box": [0.55, 0.5, 0.95, 0.8]}]}]
    monkeypatch.setattr(retrieve, "library", lambda: lib)
    target = {"width": 1920, "height": 1000}
    plans = retrieve.retrieved(a, Sizer(a, 1920, 1000), 1920, 1000)
    assert len(plans) == 1 and roles["photo"] == "hero" and roles["title"] == "headline"
    out = {e["id"]: e for e in realize(a, plans[0], 1920, 1000)["elements"]}
    assert out["photo"]["x"] + out["photo"]["width"] <= 960 + 1  # the photo went into the left slot
    assert out["title"]["x"] >= 0.55 * 1920 - 1 and out["title"]["y"] < out["note"]["y"]
    assert check(src, target, {"canvas": {"width": 1920, "height": 1000}, "elements": list(out.values())}) == []
    assert retrieve.retrieved(a, Sizer(a, 1000, 1920), 1000, 1920) == []  # a tall target: no design that shape
