"""The engine must never crash and never return an output with hard-rule
violations, on the samples and on random unseen designs."""

import copy
import json
import random
from pathlib import Path

import pytest

import engine.select
from engine.resize import resize
from eval.check import check
from eval.synthetic import TARGETS, random_design

REPO = Path(__file__).resolve().parents[2]
@pytest.fixture(autouse=True)
def fewer_renders(monkeypatch):
    monkeypatch.setattr(engine.select, "RENDER_TOP", 1)  # keep the suite fast; ranking is exercised by bench


@pytest.mark.parametrize("seed", range(40))
def test_random_designs(seed):
    rng = random.Random(seed)
    src = random_design(rng)
    target = dict(zip(("width", "height"), rng.choice(TARGETS)))
    before = copy.deepcopy(src)
    out = resize(src, target)
    assert src == before, "resize must not mutate its input"
    assert check(src, target, out) == []


@pytest.mark.parametrize("name", ["level1_warmup", "level2_core", "level3_advanced"])
@pytest.mark.parametrize("size", [(728, 90), (160, 600), (1080, 1920)])
def test_samples_pass(name, size):
    task = json.loads((REPO / "input" / f"chameleon_sample_{name}.json").read_text())
    target = {"width": size[0], "height": size[1]}
    assert check(task["source"], target, resize(task["source"], target)) == []


def test_degenerate_inputs_do_not_crash():
    target = {"width": 300, "height": 250}
    only_bg = {"canvas": {"width": 1000, "height": 1000}, "elements": [
        {"id": "bg", "type": "shape", "x": 0, "y": 0, "width": 1000, "height": 1000, "shape_type": "rectangle",
         "fill_color": "rgba(0,0,0,1)"}]}
    assert check(only_bg, target, resize(only_bg, target)) == []
    zero = {"canvas": {"width": 1000, "height": 1000}, "elements": [
        {"id": "t", "type": "text", "x": 10, "y": 10, "width": 0, "height": 0, "content": "", "font_family": "Nope",
         "font_size": 12, "color": "rgba(0,0,0,1)"}]}
    out = resize(zero, target)  # must not raise; an empty, zero-size text can't satisfy every rule
    assert {e["id"] for e in out["elements"]} == {"t"}


def test_same_aspect_keeps_the_source_layout():
    task = json.loads((REPO / "input" / "chameleon_sample_level3_advanced.json").read_text())
    target = {"width": 864, "height": 1080}  # 4:5 like the 1080x1350 source
    out = resize(task["source"], target)
    assert out == engine.select.fallback(task["source"], target) and check(task["source"], target, out) == []


def _ribbon_on_card():
    """A rotated ribbon across the top-right corner of a product card (not a canvas corner)."""
    els = [
        {"id": "bg", "type": "shape", "shape_type": "rectangle", "x": 0, "y": 0, "width": 1080, "height": 1080,
         "fill_color": "rgba(40,30,50,1)", "z_index": 0},
        {"id": "card", "type": "image", "asset_id": "solstice_bottle.png", "fit": "contain",
         "x": 340, "y": 200, "width": 400, "height": 400, "z_index": 1},
        {"id": "title", "type": "text", "content": "Discover the summer collection", "font_family": "Solstice Serif",
         "font_size": 56, "color": "rgba(255,255,255,1)", "text_align": "center",
         "x": 90, "y": 660, "width": 900, "height": 150, "z_index": 2},
        {"id": "rib_bg", "type": "shape", "shape_type": "rectangle", "fill_color": "rgba(220,60,50,1)",
         "x": 560, "y": 220, "width": 240, "height": 50, "rotation": 20, "z_index": 3, "group_id": "rib"},
        {"id": "rib_label", "type": "text", "content": "NEW", "font_family": "Solstice Sans", "font_size": 22,
         "color": "rgba(255,255,255,1)", "text_align": "center", "font_weight": "bold",
         "x": 560, "y": 230, "width": 240, "height": 30, "rotation": 20, "z_index": 4, "group_id": "rib"},
    ]
    return {"canvas": {"width": 1080, "height": 1080}, "elements": els}


def _centre(el):
    return el["x"] + el["width"] / 2, el["y"] + el["height"] / 2


def test_attached_ribbon_travels_with_its_card():
    from engine.analyze import analyze
    src = _ribbon_on_card()
    a = analyze(src)
    assert a.units["rib"].host == "card"
    for target in ({"width": 1600, "height": 400}, {"width": 600, "height": 1200}):
        out = resize(src, target)
        assert check(src, target, out) == []
        o = {e["id"]: e for e in out["elements"]}
        card, rib = o["card"], _centre(o["rib_bg"])
        fx, fy = (rib[0] - card["x"]) / card["width"], (rib[1] - card["y"]) / card["height"]
        sx, sy = (680 - 340) / 400, (245 - 200) / 400
        assert abs(fx - sx) < 0.2 and abs(fy - sy) < 0.2, (target, fx, fy)
        assert o["rib_bg"]["rotation"] == 20 and o["rib_label"]["rotation"] == 20  # same side of its card: same tilt


def test_rotation_mirrors_only_with_the_position():
    from engine.analyze import analyze
    from engine.fit import orient
    task = json.loads((REPO / "input" / "chameleon_sample_level3_advanced.json").read_text())
    a = analyze(task["source"])
    u = a.units["ribbon"]
    out = {i: copy.deepcopy(e) for i, e in a.els.items()}
    orient(out, a, u, 1080, 1350)
    assert out["ribbon_bg"]["rotation"] == -12  # still top-right: unchanged
    for m in u.members:
        out[m]["x"] = 1080 - out[m]["x"] - out[m]["width"]  # moved to top-left
    orient(out, a, u, 1080, 1350)
    assert out["ribbon_bg"]["rotation"] == 12 and out["ribbon_label"]["rotation"] == 12  # mirrored, nothing new
    for m in u.members:
        out[m]["y"] = 1350 - out[m]["y"] - out[m]["height"]  # and to the bottom: a half-turn, same angle again
    orient(out, a, u, 1080, 1350)
    assert out["ribbon_bg"]["rotation"] == -12


def test_colour_emphasis_raises_importance():
    from engine.analyze import analyze
    src = json.loads((REPO / "input" / "chameleon_sample_level2_core.json").read_text())["source"]
    grey = copy.deepcopy(src)  # the orange badge repainted in the dark palette colour
    next(e for e in grey["elements"] if e["id"] == "badge_bg")["fill_color"] = "rgba(43,27,46,1)"
    def badge(s):
        return next(u for u in analyze(s).units.values() if "badge_bg" in u.members)
    assert badge(src).emphasis > 0 and badge(grey).emphasis == 0
    assert badge(src).importance > badge(grey).importance


def test_sibling_row_is_one_unit_and_stays_together():
    from engine.analyze import analyze
    from eval.score import score
    t = json.loads((REPO / "input" / "chameleon_sample_level3_advanced.json").read_text())
    assert "badge1+badge2+badge3" in analyze(t["source"]).units
    for tw, th in ((300, 250), (820, 312), (1920, 1080)):
        out = resize(t["source"], {"width": tw, "height": th})
        assert score(t["source"], out["canvas"], out)["breakdown"]["siblings"]["penalty"] == 0, (tw, th)


def test_sibling_row_restacks_rather_than_go_unreadable():
    from eval.score import score
    t = json.loads((REPO / "input" / "chameleon_sample_level3_advanced.json").read_text())
    out = resize(t["source"], {"width": 1080, "height": 1920})
    labels = [e for e in out["elements"] if e["id"] in ("badge1_label", "badge2_label", "badge3_label")]
    assert len({e["font_size"] for e in labels}) == 1 and labels[0]["font_size"] >= 15  # one size, readable
    sib = score(t["source"], out["canvas"], out)["breakdown"]["siblings"]
    assert sib["penalty"] == 0.25 and "no longer a row" in sib["detail"]  # a stack, kept together
