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

REPO = Path(__file__).resolve().parents[2]
WORDS = ("summer sale botanical light golden hour shop now limited edition crafted fresh new flavor "
         "discover the collection exclusive offer today only free shipping on all orders").split()
FONTS = ("Solstice Serif", "Solstice Sans")
ASSETS = ("solstice_bg_gradient.png", "solstice_logo_lockup.png", "solstice_bottle.png", "does_not_exist.png")
TARGETS = [(1080, 1080), (1080, 1920), (1600, 400), (728, 90), (300, 250), (160, 600), (1920, 1080), (600, 200)]


@pytest.fixture(autouse=True)
def fewer_renders(monkeypatch):
    monkeypatch.setattr(engine.select, "RENDER_TOP", 1)  # keep the suite fast; ranking is exercised by bench


def random_design(rng):
    sw, sh = rng.choice([(1080, 1080), (1080, 1350), (1200, 628), (1920, 1080), (800, 2000)])
    els = []
    if rng.random() < 0.8:
        els.append({"id": "bg", "type": "image", "x": 0, "y": 0, "width": sw, "height": sh, "z_index": 0,
                    "asset_id": rng.choice(ASSETS), "fit": "cover"})
    for n in range(rng.randint(1, 12)):
        w, h = rng.uniform(20, sw * 0.8), rng.uniform(10, sh * 0.4)
        el = {"id": f"e{n}", "x": rng.uniform(-0.1 * sw, sw - w * 0.5), "y": rng.uniform(-0.1 * sh, sh - h * 0.5),
              "width": w, "height": h, "z_index": rng.randint(1, 6)}
        kind = rng.choice(["text", "text", "image", "shape"])
        if kind == "text":
            fs = rng.choice([10, 14, 18, 24, 36, 48, 72])
            el.update(type="text", content=" ".join(rng.choice(WORDS) for _ in range(rng.randint(1, 25))).title(),
                      font_family=rng.choice(FONTS), font_size=fs, color="rgba(255,255,255,1)",
                      text_align=rng.choice(["left", "center", "right"]), font_weight=rng.choice(["regular", "bold"]),
                      height=max(h, fs * 1.3), letter_spacing=rng.choice([0, 0, 2]))
        elif kind == "image":
            el.update(type="image", asset_id=rng.choice(ASSETS), fit=rng.choice(["contain", "contain", "cover"]))
        else:
            el.update(type="shape", shape_type=rng.choice(["rectangle", "ellipse", "line"]),
                      fill_color=f"rgba(232,106,58,{rng.choice([1, 0.3])})", corner_radius=rng.choice([0, 20]))
        if rng.random() < 0.15:
            el["rotation"] = rng.choice([-30, -12, 8, 45, 90])
        if rng.random() < 0.25:
            el["group_id"] = f"g{rng.randint(0, 2)}"
        if rng.random() < 0.2:
            el["opacity"] = rng.choice([0.2, 0.6])
        els.append(el)
    return {"canvas": {"width": sw, "height": sh}, "elements": els}


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
