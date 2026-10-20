"""Critic plumbing: features, damages, the hand-scorer fallback, and the search keeping the hard rules."""

import random

import numpy as np

from critic.damage import DAMAGES, naive_stretch
from critic.features import CONT, MAX_TOKENS, N_CONT, ROLES, encode
from engine.analyze import analyze
from engine.clock import now
from engine.critic_score import available, scores
from engine.search import search
from eval.check import check
from eval.score import score
from eval.tests.test_structure import design, image, text


def _src():
    return design(1000, 1000, [image("photo", 100, 100, 500, 500), text("h", 650, 150, 300, 100, "Big news", fs=60),
                               text("b", 650, 300, 300, 120, "Some body text here", fs=24), image("logo", 800, 850, 120, 60)])


def test_features_shape_and_padding():
    src = _src()
    cont, cat, mask = encode(analyze(src), src)
    assert cont.shape == (MAX_TOKENS, N_CONT) == (MAX_TOKENS, len(CONT)) and cat.shape == (MAX_TOKENS, 3)
    assert mask.sum() == 1 + len(src["elements"]) and not cont[int(mask.sum()):].any()
    assert {ROLES[r] for r in cat[1:5, 1]} >= {"headline", "hero"}
    assert np.allclose(cont[1:5, 0:4], cont[1:5, 4:8])  # the source at its own size: output box = source box


def test_damages_change_the_layout_and_score_lower():
    src = _src()
    a = analyze(src)
    for name, f in DAMAGES.items():
        out = f(a, src, random.Random(0))
        if out is not None:
            assert out != src, name
    assert score(src, {"width": 1000, "height": 1000}, DAMAGES["corner_crowding"](a, src, random.Random(0)))["total"] < 90
    assert naive_stretch(src, {"width": 2000, "height": 500})["canvas"] == {"width": 2000, "height": 500}


def test_missing_model_falls_back_to_the_hand_scorer(tmp_path):
    src = _src()
    missing = tmp_path / "none.onnx"
    assert not available(missing)
    t = {"width": 1000, "height": 1000}
    assert scores(src, t, [src], analyze(src), missing) == [score(src, t, src)["total"]]


def test_search_keeps_the_hard_rules():
    src = _src()
    target = {"width": 1600, "height": 900}
    from engine.select import fallback
    start = fallback(src, target)
    found = search(src, target, analyze(src), [start], now() + 1.0, path="/nonexistent.onnx")
    assert found and all(check(src, target, o) == [] for _s, o in found)
    assert found[0][0] >= score(src, target, start)["total"]  # only improvements are kept
