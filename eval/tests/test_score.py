import copy
import json
from pathlib import Path

import pytest

from engine.resize import resize
from eval.score import PENALTIES, score

REPO = Path(__file__).resolve().parents[2]
SAMPLES = ["level1_warmup", "level2_core", "level3_advanced"]
GEOMETRIC = [k for k, (_f, _w, render) in PENALTIES.items() if not render]


def load(name):
    return json.loads((REPO / "input" / f"chameleon_sample_{name}.json").read_text())


def el(design, eid):
    return next(e for e in design["elements"] if e["id"] == eid)


@pytest.mark.parametrize("name", SAMPLES)
def test_identity_is_perfect(name):
    src = load(name)["source"]
    r = score(src, src["canvas"], copy.deepcopy(src))
    assert r["total"] == 100 and set(r["breakdown"]) == set(GEOMETRIC)


def test_baseline_problems_are_penalised():
    b = {}
    for name in SAMPLES:
        t = load(name)
        b[name] = score(t["source"], t["target_canvas"], resize(t["source"], t["target_canvas"]))
    # L2: everything stays in the middle column of a 4:1 banner, text shrinks to 6-8px
    assert b["level2_core"]["breakdown"]["space"]["penalty"] > 0.5
    assert b["level2_core"]["breakdown"]["small_text"]["penalty"] > 0.2
    # L3: every font collapses to 1-2px
    assert b["level3_advanced"]["breakdown"]["small_text"]["penalty"] > 0.8
    assert b["level3_advanced"]["breakdown"]["space"]["penalty"] > 0.5
    assert b["level3_advanced"]["total"] < b["level2_core"]["total"] < b["level1_warmup"]["total"] <= 100


def _mutated(mutate):
    src = load("level2_core")["source"]
    out = copy.deepcopy(src)
    mutate(out)
    return score(src, src["canvas"], out)["breakdown"]


def test_new_overlap_penalised_but_designed_layering_is_not():
    assert _mutated(lambda o: el(o, "headline").update(y=500))["overlap"]["penalty"] > 0.3
    # the source already layers the bottle over deco_circle_1 and text over the CTA pill
    assert _mutated(lambda o: None)["overlap"]["penalty"] == 0


def test_headline_must_stay_largest():
    assert _mutated(lambda o: el(o, "subhead").update(font_size=70))["headline"]["penalty"] > 0


def test_near_miss_alignment():
    assert _mutated(lambda o: el(o, "subhead").update(x=148))["alignment"]["penalty"] > 0


def test_reading_order():
    def swap(o):
        el(o, "logo").update(y=950)
        for i in ("cta_bg", "cta_label"):
            el(o, i)["y"] -= 890
    assert _mutated(swap)["reading_order"]["penalty"] > 0


def test_contrast_only_when_asked_and_detects_dark_text():
    src = load("level1_warmup")["source"]
    assert "contrast" not in score(src, src["canvas"], src)["breakdown"]
    ok = score(src, src["canvas"], src, contrast=True)["breakdown"]["contrast"]["penalty"]
    dark = copy.deepcopy(src)
    el(dark, "headline")["color"] = "rgba(50,30,45,1)"
    bad = score(src, src["canvas"], dark, contrast=True)["breakdown"]["contrast"]
    assert ok == 0 and bad["penalty"] > 0.4 and bad["detail"].startswith("headline")  # mean over 2 texts
