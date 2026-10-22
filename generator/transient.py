"""Serve analyzer and full-renderer asset reads from RAM without asset files."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
from unittest.mock import patch

from PIL import Image

from generator.extract import memory_assets


@contextmanager
def render_assets(images: dict[str, Image.Image]) -> Iterator[None]:
    from renderer.converter import assets, convert

    original = assets.asset_path

    def path(directory: str | None, asset_id: str | None) -> Path | None:
        if asset_id in images:
            return Path("/__chameleon_memory_assets__") / asset_id
        if asset_id and asset_id.startswith("crello_"):
            return None
        return original(directory, asset_id)

    with memory_assets(images), patch.object(assets, "asset_path", path), patch.object(convert, "asset_path", path):
        yield
