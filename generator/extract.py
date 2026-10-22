"""Reuse the converter/analyzer transiently, returning only sanitized features."""

from __future__ import annotations

import math
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
from unittest.mock import patch

import jsonschema
from PIL import Image

from engine.analyze import Analysis, Unit, analyze
from eval import crello_convert as converter
from eval import score
from generator.campaigns import fingerprint, hashed


@contextmanager
def memory_assets(images: dict[str, Image.Image]) -> Iterator[None]:
    """Serve analyzer/scorer image reads from RAM; never create asset files.

    Single-threaded per worker: PIL.Image.open is patched only for this context.
    Cached source JSON and image-derived data are cleared at its boundaries.
    """
    original = Image.open

    def open_image(fp: object, *args: object, **kwargs: object) -> Image.Image:
        if isinstance(fp, (str, os.PathLike)):
            name = Path(fp).name
            if name in images:
                return images[name].copy()
            if name.startswith("crello_"):
                raise FileNotFoundError(name)
        return original(fp, *args, **kwargs)

    def clear() -> None:
        for value in vars(score).values():
            if callable(value) and hasattr(value, "cache_clear"):
                value.cache_clear()

    clear()
    try:
        with patch.object(Image, "open", open_image):
            yield
    finally:
        clear()


def raw_fingerprint(row: dict) -> dict:
    types = {"TextElement": "text", "ColoredBackground": "shape", "SvgElement": "image",
             "SvgMaskElement": "image", "ImageElement": "image"}
    return fingerprint([{"type": types[converter.TYPES[t]], "content": row["text"][i] or ""}
                        for i, t in enumerate(row["type"])])


def group_features(analysis: Analysis) -> list[dict]:
    sw, sh = analysis.sw, analysis.sh
    els = analysis.els
    order = {eid: index for index, eid in enumerate(els)}

    def feature(members: list[str], box: tuple, role: str, kind: str,
                *, parts: list | None = None, cols: int = 0, host: str | None = None) -> dict:
        w, h = box[2] - box[0], box[3] - box[1]
        types = [els[eid]["type"] for eid in members]
        return {"members": [order[eid] for eid in members], "types": types, "role": role, "kind": kind,
                "box": [box[0] / sw, box[1] / sh, w / sw, h / sh], "aspect": w / max(h, 1e-9),
                "char_count": sum(len(els[eid].get("content", "")) for eid in members),
                "image_aspects": [els[eid]["width"] / max(els[eid]["height"], 1e-9) for eid in members if els[eid]["type"] == "image"],
                "area_share": w * h / (sw * sh), "z_order": min(els[eid].get("z_index", order[eid]) for eid in members),
                "host_members": [order[eid] for eid in analysis.units[host].members] if host else [],
                "parts": [{"members": [order[eid] for eid in mem], "box": [b[0] / sw, b[1] / sh, (b[2] - b[0]) / sw, (b[3] - b[1]) / sh]} for mem, b in (parts or [])],
                "cols": cols}

    out = []
    for u in [*analysis.units.values(), *analysis.decorations]:
        kind = "grid" if u.cols else "row" if u.parts else "flow_text" if u.kind == "text" else u.kind
        item = feature(u.members, u.box, u.role, kind, parts=u.parts, cols=u.cols, host=u.host)
        item["engine_kind"] = u.kind
        item["floating"] = u.floating
        out.append(item)
    # Preserve special groups separately: the engine does not put these in units.
    for eid in analysis.background:
        e = els[eid]
        item = feature([eid], (e["x"], e["y"], e["x"] + e["width"], e["y"] + e["height"]), "background", "background")
        item.update(engine_kind=e["type"], floating=False)
        out.append(item)
    for eid, members in analysis.panels.items():
        e = els[eid]
        item = feature([eid], (e["x"], e["y"], e["x"] + e["width"], e["y"] + e["height"]), "panel", "panel")
        item.update(engine_kind=e["type"], floating=False)
        # Content membership references other groups; it must not double-count elements.
        item["host_members"] = [order[m] for m in members]
        out.append(item)
    out.sort(key=lambda g: (g["z_order"], g["members"]))
    assert sorted(m for g in out for m in g["members"]) == list(range(len(els))), "group membership must partition elements"
    assert all(math.isfinite(v) for g in out for v in [*g["box"], g["aspect"], g["area_share"], *g["image_aspects"]])
    return out


def extract(row: dict, fonts: list[str], formats: list[str]) -> dict:
    record = {"design_hash": hashed(str(row["id"])), "fingerprints": [raw_fingerprint(row)],
              "canvas": [int(row["canvas_width"]), int(row["canvas_height"])], "groups": [], "status": "ok"}
    source, _meta, images = converter.convert(row, fonts, formats)
    try:
        record["fingerprints"].append(fingerprint(source["elements"]))
        texts = [e for e in source["elements"] if e["type"] == "text"]
        n = len(source["elements"])
        reason = ("too_few_elements" if n < converter.MIN_ELEMENTS else "too_many_elements" if n > converter.MAX_ELEMENTS
                  else "no_text" if not texts else "unsupported_characters" if any(converter.missing_glyphs(e["content"], e["font_family"]) for e in texts) else None)
        if reason:
            record["status"] = reason
            return record
        jsonschema.Draft202012Validator(converter.SCHEMA).validate(source)
        with memory_assets(images):
            record["groups"] = group_features(analyze(source))
        return record
    finally:
        for image in images.values():
            image.close()
