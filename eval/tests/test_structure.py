"""Structure the engine must recognise on unseen designs: turned backgrounds, rule lines,
text on image cards, grids of repeated cells, and a big hero photo."""

import pytest

import engine.select
from engine.analyze import analyze
from engine.resize import resize
from eval.check import check

IMG = "solstice_bottle.png"  # any existing asset; contain keeps its box aspect


@pytest.fixture(autouse=True)
def fewer_renders(monkeypatch):
    monkeypatch.setattr(engine.select, "RENDER_TOP", 1)


def text(id, x, y, w, h, content="Caption text", fs=24, **kw):
    return {"id": id, "type": "text", "x": x, "y": y, "width": w, "height": h, "content": content,
            "font_family": "Solstice Sans", "font_size": fs, "color": "rgba(0,0,0,1)", **kw}


def image(id, x, y, w, h, **kw):
    return {"id": id, "type": "image", "x": x, "y": y, "width": w, "height": h, "asset_id": IMG, "fit": "contain", **kw}


def design(w, h, els):
    for z, e in enumerate(els):
        e["z_index"] = z
    return {"canvas": {"width": w, "height": h}, "elements": els}


@pytest.mark.parametrize("turn", [180, 90])
def test_turned_background_is_recognised_and_placed(turn):
    bg = image("bg", 0, 0, 1080, 1080, rotation=turn, fit="cover")
    src = design(1080, 1080, [bg, text("t", 100, 400, 880, 120, "A headline over a turned photo", fs=60)])
    assert analyze(src).background == ["bg"]
    for target in ({"width": 1080, "height": 1080}, {"width": 1920, "height": 1080}):
        out = resize(src, target)
        assert check(src, target, out) == []
        b = next(e for e in out["elements"] if e["id"] == "bg")
        if turn == 180 or target["width"] == target["height"]:
            assert (b["x"], b["y"], b["width"], b["height"]) == (0, 0, target["width"], target["height"])
        else:  # a quarter turn fills only the centred square the box may occupy
            assert b["width"] == b["height"] == min(target.values())


def test_rule_lines_stay_visible_and_on_their_own():
    src = design(1080, 1080, [
        image("card", 200, 200, 680, 400),
        text("t", 240, 250, 600, 80, "Title on the card", fs=48),
        image("line", 240, 340, 600, 2),  # a divider on the card
        text("u", 240, 700, 600, 60, "Below the card", fs=36),
    ])
    a = analyze(src)
    assert "line" in [m for d in a.decorations for m in d.members]
    out = resize(src, {"width": 300, "height": 250})
    line = next(e for e in out["elements"] if e["id"] == "line")
    assert min(line["width"], line["height"]) >= 1  # 600x2 scaled to fit 300px would be 1px; never less
    assert check(src, {"width": 300, "height": 250}, out) == []


def test_text_on_an_image_card_is_one_rigid_unit():
    src = design(1080, 1080, [
        image("bubble", 300, 300, 400, 200),
        text("say", 340, 340, 320, 100, "Hello there", fs=40),
        text("other", 100, 800, 880, 100, "Elsewhere", fs=40),
    ])
    u = analyze(src).units
    assert any({"bubble", "say"} <= set(x.members) for x in u.values())
    assert not any("other" in x.members and len(x.members) > 1 for x in u.values())


def _grid(rows=2, cols=3):
    els = []
    for r in range(rows):
        for c in range(cols):
            x, y = 60 + c * 340, 300 + r * 380
            els += [image(f"p{r}{c}", x, y, 300, 220), text(f"c{r}{c}", x, y + 230, 300, 40, f"Item {r}{c}", fs=24)]
    return design(1080, 1080, [text("title", 60, 60, 960, 120, "Our menu", fs=80), *els])


def test_grid_of_cells_is_one_unit_and_reflows():
    src = _grid()
    grids = [u for u in analyze(src).units.values() if u.cols]
    assert len(grids) == 1 and grids[0].cols == 3 and len(grids[0].parts) == 6
    assert all(len(m) == 2 for m, _b in grids[0].parts)  # each cell: its photo and its caption
    out = {e["id"]: e for e in resize(src, {"width": 1080, "height": 1920})["elements"]}
    cols = {round(out[f"p{r}{c}"]["x"]) for r in range(2) for c in range(3)}
    assert len(cols) < 3  # a tall canvas: fewer columns
    for r in range(2):
        for c in range(3):  # captions stay under their own photo
            p, t = out[f"p{r}{c}"], out[f"c{r}{c}"]
            assert abs((p["x"] + p["width"] / 2) - (t["x"] + t["width"] / 2)) < 2 and t["y"] > p["y"]


def test_big_hero_keeps_its_share_on_a_wide_canvas():
    src = design(1080, 1350, [
        image("photo", 0, 0, 1080, 700),
        text("h", 80, 760, 920, 200, "A big headline under the photo", fs=72),
        text("b", 80, 1000, 920, 160, "Some body text that explains the offer in a sentence or two.", fs=32),
    ])
    target = {"width": 1584, "height": 396}
    out = resize(src, target)
    p = next(e for e in out["elements"] if e["id"] == "photo")
    assert check(src, target, out) == []
    assert p["height"] >= 0.9 * 396  # it keeps the full height of the banner instead of shrinking with the text


def test_a_big_flat_card_holds_its_text_and_a_photo_keeps_it_as_a_block(tmp_path, monkeypatch):
    import numpy as np
    from PIL import Image
    Image.new("RGBA", (64, 64), (240, 230, 200, 255)).save(tmp_path / "card.png")
    Image.fromarray(np.random.default_rng(0).integers(0, 255, (64, 64, 3), dtype=np.uint8)).save(tmp_path / "photo.png")
    monkeypatch.setenv("CHAMELEON_ASSETS", str(tmp_path))
    def on(asset):  # a 600x600 image (31% of the canvas) with a title on it: (kept together, as a block)
        src = design(1080, 1080, [{**image("img", 240, 240, 600, 600), "asset_id": asset}, text("t", 300, 400, 480, 100, "On it", fs=60)])
        u = next((u for u in analyze(src).units.values() if {"img", "t"} <= set(u.members)), None)
        return u is not None, bool(u and u.children)
    assert on("card.png") == (True, False)  # a card: one unit holding its text
    assert on("photo.png") == (True, True)  # a photo with text on it: an overlap block, opened only if unreadable


def test_a_tall_stack_of_texts_flows_into_columns_on_a_wide_banner():
    src = design(500, 2000, [text(f"t{i}", 50, 40 + i * 120, 400, 60, f"Line number {i}", fs=40) for i in range(16)])
    target = {"width": 1584, "height": 396}
    out = resize(src, target)
    assert check(src, target, out) == []
    els = {e["id"]: e for e in out["elements"]}
    col = {i: els[f"t{i}"]["x"] // 400 for i in range(16)}  # columns are ~528px apart on this banner
    assert 2 <= len(set(col.values())) <= 3  # side by side in 2 or 3 columns
    assert all(els[f"t{i}"]["font_size"] >= 14 for i in range(16))  # instead of all shrinking to fit one column
    assert sorted(range(16), key=lambda i: (col[i], els[f"t{i}"]["y"])) == list(range(16))  # down each column, then right


def test_an_oversized_panel_fits_around_its_text():
    panel = {"id": "panel", "type": "shape", "x": 60, "y": 60, "width": 960, "height": 960,
             "shape_type": "rectangle", "fill_color": "rgba(255,255,255,1)"}
    src = design(1080, 1080, [panel, text("h", 140, 140, 800, 120, "A short title", fs=80)])
    assert "panel" in analyze(src).panels
    target = {"width": 1920, "height": 1080}
    res = resize(src, target)
    assert check(src, target, res) == []
    out = {e["id"]: e for e in res["elements"]}
    p, h = out["panel"], out["h"]
    assert p["x"] <= h["x"] and p["y"] <= h["y"]  # still behind its text...
    assert p["width"] * p["height"] < 0.5 * 1920 * 1080  # ...but no longer a mostly empty square


def _kept(src, target, out):
    from eval.score import relations_kept
    return relations_kept(src, target, out)[0]


def test_a_collage_moves_as_one_block():
    els = [image("p1", 100, 100, 400, 300), image("p2", 380, 250, 400, 300), image("p3", 200, 450, 400, 300),
           text("t", 100, 900, 880, 100, "Our summer in pictures", fs=60)]
    src = design(1080, 1080, els)
    block = next(u for u in analyze(src).units.values() if {"p1", "p2", "p3"} <= set(u.members))
    assert block.children and "t" not in block.members  # the three photos, not the caption far below
    for target in ({"width": 1920, "height": 1080}, {"width": 1080, "height": 1920}):
        out = resize(src, target)
        assert check(src, target, out) == []
        o = {e["id"]: e for e in out["elements"]}
        s = o["p1"]["width"] / 400  # one scale, same arrangement and stacking
        for i, (x, y) in (("p2", (280, 150)), ("p3", (100, 350))):
            assert abs(o[i]["x"] - o["p1"]["x"] - x * s) < 1 and abs(o[i]["y"] - o["p1"]["y"] - y * s) < 1
        assert [e["id"] for e in out["elements"]][:3] == ["p1", "p2", "p3"]


def test_contact_heading_stays_with_its_details():
    src = design(1080, 1350, [
        image("photo", 0, 0, 1080, 700),
        text("h", 80, 760, 920, 120, "Summer sale", fs=90),
        text("lab", 80, 1060, 400, 50, "Contact us", fs=36, font_weight="bold"),
        text("info", 80, 1120, 600, 120, "hello@example.com\n+1 555 0100", fs=28),
    ])
    assert any(r["kind"] == "label" and {r["a"], r["b"]} == {"lab", "info"} for r in __import__("eval.score", fromlist=["relations"]).relations(src))
    for target in ({"width": 1584, "height": 396}, {"width": 1080, "height": 1920}):
        out = resize(src, target)
        assert check(src, target, out) == []
        o = {e["id"]: e for e in out["elements"]}
        gap = o["info"]["y"] - (o["lab"]["y"] + o["lab"]["height"] * 0.5)
        assert 0 <= gap <= 3 * o["lab"]["font_size"] and abs(o["info"]["x"] - o["lab"]["x"]) < 2  # still right under it


def test_a_block_opens_only_when_it_would_be_unreadable():
    # two paragraphs side by side, close together: one block; on a tall narrow canvas it can only stay readable apart
    body = "A longer paragraph of body text that explains the offer in a few short sentences for the reader."
    src = design(1600, 900, [text("h", 100, 80, 1400, 150, "Two columns of news", fs=100),
                             text("l", 100, 400, 680, 300, body, fs=30), text("r", 820, 400, 680, 300, body, fs=30)])
    assert any({"l", "r"} <= set(u.members) and u.children for u in analyze(src).units.values())
    wide = resize(src, {"width": 1920, "height": 1080})
    o = {e["id"]: e for e in wide["elements"]}
    assert abs(o["l"]["y"] - o["r"]["y"]) < 1  # fits readably: kept side by side
    tall = resize(src, {"width": 160, "height": 600})
    o = {e["id"]: e for e in tall["elements"]}
    assert check(src, {"width": 160, "height": 600}, tall) == [] and min(o["l"]["font_size"], o["r"]["font_size"]) >= 12
