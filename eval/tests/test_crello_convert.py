"""The Crello converter on a hand-made row (no Crello data needed)."""

import io

import jsonschema
from PIL import Image

from eval.crello_convert import SCHEMA, TYPES, convert, family, missing_glyphs

FONTS = ["", "Bebas Neue", "Playfair Display"]
FORMATS = ["Instagram"]


def png(w, h, colour=(255, 0, 0, 255)):
    buf = io.BytesIO()
    Image.new("RGBA", (w, h), colour).save(buf, "PNG")
    return {"bytes": buf.getvalue(), "path": None}


def row(elements):
    cols = {k: [] for k in ("type", "left", "top", "width", "height", "angle", "opacity", "color", "image", "text", "font",
                            "font_size", "font_bold", "font_italic", "text_color", "text_align", "capitalize",
                            "line_height", "letter_spacing", "text_line")}
    for e in elements:
        n = len(e.get("text", ""))
        base = {"angle": 0.0, "opacity": 1.0, "color": [], "image": None, "text": "", "font": 0, "font_size": 0.0,
                "font_bold": [False] * n, "font_italic": [False] * n, "text_color": ["rgba(0, 0, 0, 1)"] * n,
                "text_align": 0, "capitalize": False, "line_height": 1.0, "letter_spacing": 0.0, "text_line": [0] * n}
        for k, v in {**base, **e}.items():
            cols[k].append(TYPES.index(v) if k == "type" else v)
    return {"id": "x", "length": len(elements), "format": 0, "canvas_width": 1000, "canvas_height": 1000, **cols}


def test_converts_types_styles_and_bleed():
    r = row([
        {"type": "ImageElement", "left": -500.0, "top": -10.0, "width": 2000.0, "height": 1020.0, "image": png(200, 102)},
        {"type": "ColoredBackground", "left": 100.0, "top": 100.0, "width": 200.0, "height": 50.0, "color": ["rgba(1, 2, 3, 1)"]},
        {"type": "SvgElement", "left": 600.0, "top": 600.0, "width": 100.0, "height": 50.0, "angle": 0.01, "image": png(100, 50)},
        {"type": "TextElement", "left": 100.0, "top": 300.0, "width": 800.0, "height": 120.0, "text": "Big Sale",
         "font": 1, "font_size": 100.0, "capitalize": True, "text_align": 2,
         "text_color": ["rgba(0, 0, 0, 1)"] * 4 + ["rgba(255, 0, 0, 1)"] * 4, "font_bold": [True] * 8},
    ])
    design, meta, images = convert(r, FONTS, FORMATS)
    jsonschema.validate(design, SCHEMA)
    bg, rect, svg, text = design["elements"]
    assert (bg["x"], bg["y"], bg["width"], bg["height"], bg["fit"]) == (0, 0, 1000, 1000, "cover")  # cut to the canvas
    assert images[bg["asset_id"]].size == (100, 100)  # and its pixels too
    assert rect["type"] == "shape" and rect["fill_color"] == "rgba(1,2,3,1)"
    assert svg["fit"] == "contain" and "rotation" not in svg  # 0.01 deg is noise
    assert text["content"] == "BIG SALE" and text["font_family"] == "Solstice Sans" and text["text_align"] == "center"
    assert text["font_weight"] == "bold" and text["color"] == "rgba(0,0,0,1)"
    assert text["style_runs"] == [{"start": 4, "end": 8, "color": "rgba(255,0,0,1)"}]
    assert meta["elements"] == 4 and meta["fonts"] == {"Bebas Neue": 1}


def test_wider_substitute_font_is_shrunk_to_crellos_line_count():
    r = row([{"type": "TextElement", "left": 0.0, "top": 0.0, "width": 300.0, "height": 100.0,
              "text": "CONDENSED HEADLINE", "font": 1, "font_size": 60.0}])
    text = convert(r, FONTS, FORMATS)[0]["elements"][0]
    assert text["font_size"] < 60  # one line in Crello's condensed face; our sans needs a smaller size for that
    assert convert(r, FONTS, FORMATS)[1]["font_refit"]


def test_font_mapping_and_coverage():
    assert family("Playfair Display") == "Solstice Serif" and family("Bebas Neue") == "Solstice Sans"
    assert missing_glyphs("Hello, world!", "Solstice Sans") == []
    assert missing_glyphs("Привет", "Solstice Sans")  # would render as boxes
