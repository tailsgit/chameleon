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


from generator.group_features import group_features


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
