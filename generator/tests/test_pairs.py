from __future__ import annotations

import copy
import sys

from PIL import Image

from engine.analyze import analyze
from eval.render import render_image
from generator.engine_sample import bounded_process
from generator.extract import group_features
from generator.pair_geometry import (METHODS, aligned_targets, canvases, cheap_source,
                                     outside_canvas, outside_coordinates, pair_record)
from generator.transient import render_assets


def design() -> dict:
    return {"canvas": {"width": 400, "height": 400}, "elements": [
        {"id": "bg", "type": "shape", "shape_type": "rectangle", "fill_color": "rgba(255,255,255,1)",
         "x": 0, "y": 0, "width": 400, "height": 400, "z_index": 0},
        {"id": "photo", "type": "image", "asset_id": "crello_synthetic.png", "fit": "contain",
         "x": 20, "y": 20, "width": 80, "height": 40, "z_index": 1},
        {"id": "text", "type": "text", "content": "Hello", "font_family": "Solstice Sans", "font_size": 20,
         "color": "rgba(0,0,0,1)", "x": 350, "y": 300, "width": 80, "height": 50, "z_index": 2},
    ]}


def test_memory_assets_support_full_renderer_without_placeholders() -> None:
    images = {"crello_synthetic.png": Image.new("RGBA", (80, 40), (231, 12, 3, 255))}
    with render_assets(images):
        rendered = render_image(design())
        assert rendered.getpixel((60, 40)) == (231, 12, 3)


def test_seeded_sources_preserve_content_and_real_target_boxes() -> None:
    target = design(); before = copy.deepcopy(target)
    images = {"crello_synthetic.png": Image.new("RGBA", (80, 40), (231, 12, 3, 255))}
    with render_assets(images):
        groups = group_features(analyze(target))
        cached = {"groups": groups, "canvas": [400, 400], "design_hash": "a" * 64,
                  "campaign_hash": "b" * 64, "split": "train", "raw_shard": 0, "raw_row": 0}
        canvas = {"width": 800, "height": 400}
        for method in METHODS:
            source = cheap_source(target, groups, canvas, method, 2026, cached["design_hash"], 0)
            assert source == cheap_source(target, groups, canvas, method, 2026, cached["design_hash"], 0)
            assert target == before
            assert source["elements"][1]["width"] / source["elements"][1]["height"] == 2
            assert source["elements"][2]["content"] == "Hello"
            pair = pair_record(target, cached, source, method, 0)
            canonical = {tuple(g["members"]): g["box"] for g in groups}
            for group, box, changed in zip(pair["source_groups"], pair["target_boxes"], pair["target_regrouped"]):
                if not changed:
                    assert box == canonical[tuple(group["members"])], "target was transformed or clipped"
    assert outside_canvas([0.875, 0.75, 0.2, 0.125])
    assert not outside_coordinates([0.875, 0.75, 0.2, 0.125])


def test_regrouped_target_is_original_element_union_without_clipping() -> None:
    target = design()
    boxes, changed = aligned_targets(target, [], [{"members": [1, 2]}])
    assert changed == [True]
    assert boxes[0][0] == 20 / 400
    assert boxes[0][0] + boxes[0][2] == 430 / 400
    assert outside_canvas(boxes[0])


def test_canvas_schedule_is_seeded_and_different_from_target() -> None:
    a = canvases("a" * 64, [1080, 1080], 2026)
    assert a == canvases("a" * 64, [1080, 1080], 2026)
    assert len(a) == 4
    assert all([c["width"], c["height"]] != [1080, 1080] for c in a)
    assert 0.25 <= a[-1]["width"] / a[-1]["height"] <= 4


def test_wall_timeout_kills_worker_without_waiting_for_completion() -> None:
    result = bounded_process([sys.executable, "-c", "import time; time.sleep(5)"], b"", timeout=0.1)
    assert result["timed_out"]
    assert result["elapsed"] < 1.0
    assert result["returncode"] != 0
