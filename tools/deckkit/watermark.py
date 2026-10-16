"""Diagonal tiled watermark and a corner mark, applied and REVERSIBLE.

Both marks are alpha composites, ``out = src*(1-a) + ink*a`` with a known constant alpha on the
glyph mask. Rebuilding the identical mask therefore lets :func:`unmark` invert them per pixel:
``src = (out - ink*a) / (1-a)``. Keep the same arguments for mark and unmark.

Ink is picked from the page itself (white on dark, charcoal on light) by sampling a corner.
"""
import numpy as np
from PIL import Image, ImageDraw

from .fonts import load_font

DEFAULTS = dict(
    text="WATERMARK", corner_text="CONFIDENTIAL",
    size=0.020,        # tile cap height, fraction of page height
    opacity=26,        # 0-255 alpha of each tile (26 = 10%)
    angle=30,
    step_x=4.5,        # gap between tiles, multiples of text width
    step_y=10.0,       # gap between rows, multiples of text height
    corner_size=0.019, corner_right=0.972, corner_top=0.030, corner_opacity=150,
    dark_ink=(26, 26, 26), light_ink=(255, 255, 255),
)


def is_dark(im, probe=(0.90, 0.04), threshold=110):
    w, h = im.size
    r, g, b = im.convert("RGB").getpixel((int(w * probe[0]), int(h * probe[1])))[:3]
    return (r + g + b) / 3 < threshold


def _tile_mask(size, o, font_path=None):
    """Greyscale (0-255) mask of the rotated, tiled watermark for a page of ``size``."""
    w, h = size
    font = load_font(int(h * o["size"]), font_path)
    pad = int(max(w, h) * 0.5)
    layer = Image.new("L", (w + pad * 2, h + pad * 2), 0)
    d = ImageDraw.Draw(layer)
    box = d.textbbox((0, 0), o["text"], font=font)
    tw, th = box[2] - box[0], box[3] - box[1]
    sx, sy = max(1, int(tw * o["step_x"])), max(1, int(th * o["step_y"]))
    row, y = 0, 0
    while y < layer.height:
        x = -sx // 2 if row % 2 else 0   # offset every other row so the grid reads as a weave
        while x < layer.width:
            d.text((x - box[0], y - box[1]), o["text"], font=font, fill=o["opacity"])
            x += sx
        y += sy
        row += 1
    layer = layer.rotate(o["angle"], resample=Image.BICUBIC, center=(layer.width / 2, layer.height / 2))
    return layer.crop((pad, pad, pad + w, pad + h))


def _corner_mask(size, o, font_path=None):
    w, h = size
    font = load_font(int(h * o["corner_size"]), font_path)
    m = Image.new("L", size, 0)
    d = ImageDraw.Draw(m)
    box = d.textbbox((0, 0), o["corner_text"], font=font)
    d.text((w * o["corner_right"] - (box[2] - box[0]) - box[0], h * o["corner_top"] - box[1]),
           o["corner_text"], font=font, fill=o["corner_opacity"])
    return m


def _masks(size, o, font_path):
    ms = []
    if o["text"]:
        ms.append(_tile_mask(size, o, font_path))
    if o["corner_text"]:
        ms.append(_corner_mask(size, o, font_path))
    return ms


def _ink(im, o, ink=None):
    return ink or (o["light_ink"] if is_dark(im) else o["dark_ink"])


def mark(im, font_path=None, ink=None, **opts):
    """Return a new RGB image with the watermark and corner mark applied."""
    o = {**DEFAULTS, **opts}
    im = im.convert("RGB")
    rgb = np.asarray(im).astype(np.float64)
    colour = np.array(_ink(im, o, ink), dtype=np.float64)
    for m in _masks(im.size, o, font_path):
        a = (np.asarray(m).astype(np.float64) / 255.0)[..., None]
        rgb = rgb * (1 - a) + colour * a
    return Image.fromarray(np.clip(np.rint(rgb), 0, 255).astype(np.uint8))


def unmark(im, font_path=None, ink=None, dark=None, **opts):
    """Invert :func:`mark`. Pass ``dark`` (True/False) when the ink choice can't be re-sampled
    from the marked page. Integer rounding in the original leaves ±1-2 levels of error."""
    o = {**DEFAULTS, **opts}
    im = im.convert("RGB")
    if ink is None and dark is not None:
        ink = o["light_ink"] if dark else o["dark_ink"]
    colour = np.array(_ink(im, o, ink), dtype=np.float64)
    rgb = np.asarray(im).astype(np.float64)
    for m in reversed(_masks(im.size, o, font_path)):
        a = (np.asarray(m).astype(np.float64) / 255.0)[..., None]
        rgb = (rgb - colour * a) / np.clip(1 - a, 1e-6, None)
    return Image.fromarray(np.clip(np.rint(rgb), 0, 255).astype(np.uint8))
