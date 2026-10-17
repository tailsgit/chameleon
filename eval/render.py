"""In-memory rendering through the official renderer (same path as engine/main.py)."""

import io
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parents[1]
ASSETS_DIR = REPO / "brand_kit" / "assets"
FONTS_DIR = REPO / "brand_kit" / "fonts"
MAX_SIZE = 2048  # render_design_to_png's default cap on the long side


def render_image(design: dict) -> Image.Image:
    """Render `design` to an RGB PIL image. Canvases longer than 2048px come
    back downscaled, exactly like output/*.png."""
    from renderer.converter.convert import _get_renderer, convert_chameleon_to_crello

    renderer = _get_renderer(str(FONTS_DIR))
    example, _warnings = convert_chameleon_to_crello(design, renderer.font_manager, str(ASSETS_DIR))
    png = renderer.render(example, max_size=MAX_SIZE, format="png")
    return Image.open(io.BytesIO(png)).convert("RGB")


def render_scale(design: dict) -> float:
    """Pixels in the rendered image per design px."""
    c = design["canvas"]
    return min(1.0, MAX_SIZE / max(c["width"], c["height"]))
