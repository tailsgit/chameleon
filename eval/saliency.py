"""Where a photo's subject is, so a cover crop can keep it.

The renderer crops a `cover` image to its box from the centre, and the engine can't change that:
it can only choose the box's shape. A quick saliency map of the asset (SIZE px on its long side)
finds the subject, and `aspect_range` gives the box shapes whose centre crop keeps it.

Saliency = the sum of three maps, each scaled to 0..1:
  colour   distance of each (blurred) pixel from the image's mean colour (frequency-tuned
           saliency, Achanta et al. 2009): what stands out from the rest of the picture
  detail   gradient magnitude, blurred: edges and texture, not flat sky or walls
  skin     skin-tone pixels (YCbCr box): faces and people
The salient region is the central KEEP of the (sharpened) saliency mass along each axis (marginal
quantiles); when it covers more than SPREAD of the image there is no distinct subject.
"""

from functools import lru_cache

import numpy as np
from PIL import Image, ImageFilter

from eval.render import assets_dir

SIZE = 96     # px on the long side the map is computed at
KEEP = 0.8    # the salient region holds this share of the saliency mass along each axis
BLUR = 2      # px (at SIZE): smooths noise and JPEG blocks
SKIN = 2      # skin counts this much more than colour or detail: faces are what a crop must keep
SHARPEN = 4   # saliency is raised to this power: the subject, not everything slightly above average
SLACK = 1.01  # box aspects this close to the range's ends still keep the subject (rounding)
SPREAD = 0.5  # a salient region covering more than this share of the image is no subject at all


@lru_cache(maxsize=128)
def salient_box(asset_id):
    """(x0, y0, x1, y1) of the subject as fractions of the image, or None if it can't be read."""
    try:
        with Image.open(assets_dir() / asset_id) as im:
            im = im.convert("RGBA")
            k = SIZE / max(im.size)
            im = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))))
    except (OSError, TypeError):
        return None
    rgba = np.asarray(im, dtype=np.float32) / 255
    rgb = np.asarray(im.convert("RGB").filter(ImageFilter.GaussianBlur(BLUR)), dtype=np.float32) / 255
    alpha = rgba[..., 3]
    colour = np.linalg.norm(rgb - (rgb * alpha[..., None]).sum((0, 1)) / max(alpha.sum(), 1e-6), axis=2)
    grey = rgb.mean(2)
    gy, gx = np.gradient(grey)
    detail = _blur(np.hypot(gx, gy))
    ycc = np.asarray(im.convert("RGB").convert("YCbCr"), dtype=np.float32)
    skin = ((ycc[..., 1] >= 77) & (ycc[..., 1] <= 127) & (ycc[..., 2] >= 133) & (ycc[..., 2] <= 173)).astype(np.float32)
    skin = _blur(skin)
    sal = (sum(w * m / m.max() for w, m in ((1, colour), (1, detail), (SKIN, skin)) if m.max() > 1e-6) * alpha) ** SHARPEN
    if sal.sum() <= 1e-6:
        return None
    lo, hi = (1 - KEEP) / 2, (1 + KEEP) / 2
    (x0, x1), (y0, y1) = (_quantiles(sal.sum(axis), lo, hi) for axis in (0, 1))
    if (x1 - x0) * (y1 - y0) > SPREAD:
        return None  # saliency all over (a texture, a pattern, a busy scene): no subject to keep
    return x0, y0, x1, y1


def _blur(m):
    k = np.ones(2 * BLUR + 1) / (2 * BLUR + 1)
    for axis in (0, 1):
        m = np.apply_along_axis(np.convolve, axis, m, k, mode="same")
    return m


def _quantiles(mass, lo, hi):
    c = np.cumsum(mass) / mass.sum()
    n = len(mass)
    return float(np.searchsorted(c, lo)) / n, float(np.searchsorted(c, hi) + 1) / n


def aspect_range(el):
    """(min, max) box aspect (width / height) whose centre cover crop keeps el's subject, or None
    (not a cover image, unreadable, or no distinct subject)."""
    if el.get("type") != "image" or el.get("fit", "contain") != "cover":
        return None
    box = salient_box(el.get("asset_id"))
    size = _asset_aspect(el.get("asset_id"))
    if box is None or size is None:
        return None
    x0, y0, x1, y1 = box
    fx = max(2 * max(0.5 - x0, x1 - 0.5), 1e-3)  # share of the width the crop must keep
    fy = max(2 * max(0.5 - y0, y1 - 0.5), 1e-3)
    return size * min(1.0, fx), size / min(1.0, fy)


@lru_cache(maxsize=128)
def _asset_aspect(asset_id):
    try:
        with Image.open(assets_dir() / asset_id) as im:
            return im.width / im.height
    except (OSError, TypeError):
        return None


def subject_kept(source, output):
    """False when a cover photo whose source crop showed its subject has a box in output whose centre
    crop cuts it off."""
    out = {e["id"]: e for e in output["elements"]}
    for e in source["elements"]:
        r = aspect_range(e)
        o = out.get(e.get("id"))
        if r is None or o is None or not r[0] <= e["width"] / max(e["height"], 1e-9) <= r[1]:
            continue
        if not r[0] / SLACK <= o["width"] / max(o["height"], 1e-9) <= r[1] * SLACK:
            return False
    return True
