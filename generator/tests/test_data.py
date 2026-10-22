from __future__ import annotations

import io
import json
from pathlib import Path

from PIL import Image

from engine.analyze import analyze
from generator.campaigns import cluster, fingerprint, hashed, similarity, text_prefix
from generator.extract import group_features, memory_assets


def test_campaign_threshold_structure_and_transitive_exclusion() -> None:
    def record(key: str, texts: list[str], kind: str = "text") -> dict:
        return {"design_hash": hashed(key), "fingerprints": [{"types": [kind], "texts": texts}]}

    records = [record("excluded", ["a", "b"]), record("bridge", ["a", "b", "c"]),
               record("indirect", ["b", "c"]), record("different_structure", ["a", "b"], "image"),
               record("empty1", []), record("empty2", [])]
    components, edges = cluster(records)
    assert similarity(records[0]["fingerprints"][0], records[2]["fingerprints"][0]) < 0.5
    assert components[hashed("excluded")] == components[hashed("indirect")]
    assert components[hashed("excluded")] != components[hashed("different_structure")]
    assert components[hashed("empty1")] != components[hashed("empty2")]
    assert cluster(list(reversed(records))) == (components, edges)


def test_prefix_hash_normalization_and_sanitization() -> None:
    assert text_prefix("  HELLO\nWORLD ") == text_prefix("hello world")
    assert text_prefix("ＡＢＣ") == text_prefix("abc")
    assert text_prefix("a" * 30 + "first") == text_prefix("a" * 30 + "second")
    assert text_prefix(" \n") == ""
    fp = fingerprint([{"type": "text", "content": "private synthetic phrase"}, {"type": "image"}])
    assert "private synthetic phrase" not in json.dumps(fp)
    assert all(len(value) == 64 for value in fp["texts"])


def test_memory_image_adapter_restores_open_and_never_writes(tmp_path: Path) -> None:
    original = Image.open
    image = Image.new("RGBA", (16, 12), (100, 20, 30, 255))
    with memory_assets({"crello_synthetic.png": image}):
        with Image.open(tmp_path / "crello_synthetic.png") as loaded:
            assert loaded.size == (16, 12)
            assert loaded.getpixel((0, 0)) == (100, 20, 30, 255)
    assert Image.open is original
    assert list(tmp_path.iterdir()) == []
    assert image.size == (16, 12)


def test_analyzer_retains_rigid_groups_and_covers_all_elements() -> None:
    source = {"canvas": {"width": 400, "height": 400}, "elements": [
        {"id": "bg", "type": "shape", "shape_type": "rectangle", "fill_color": "rgba(255,255,255,1)",
         "x": 0, "y": 0, "width": 400, "height": 400, "z_index": 0},
        {"id": "card", "type": "shape", "shape_type": "rectangle", "fill_color": "rgba(10,10,10,1)",
         "x": 80, "y": 100, "width": 200, "height": 100, "z_index": 1, "group_id": "button"},
        {"id": "text", "type": "text", "content": "Join now", "font_family": "Solstice Sans", "font_size": 20,
         "color": "rgba(255,255,255,1)", "x": 100, "y": 120, "width": 140, "height": 50,
         "z_index": 2, "group_id": "button"},
    ]}
    features = group_features(analyze(source))
    assert sorted(m for group in features for m in group["members"]) == [0, 1, 2]
    rigid = next(g for g in features if g["members"] == [1, 2])
    assert rigid["kind"] == "rigid"
    assert rigid["char_count"] == 8
    assert "Join now" not in json.dumps(features)
    assert "button" not in json.dumps(features)
