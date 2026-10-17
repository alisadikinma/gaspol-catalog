"""Diagonal tiled watermark and a corner mark, applied and REVERSIBLE.

Both marks are alpha composites, ``out = src*(1-a) + ink*a`` with a known constant alpha on the
glyph mask. Rebuilding the identical mask therefore lets :func:`unmark` invert them per pixel:
``src = (out - ink*a) / (1-a)``. Keep the same arguments for mark and unmark.

Ink is picked from the page itself (white on dark, charcoal on light) by sampling a corner.
"""
import numpy as np
from PIL import Image, ImageChops, ImageDraw

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
    logo_opacity=31,   # 0-255 alpha of each logo tile (31 = 12%)
    logo_width=0.20,   # logo tile width, fraction of page width
    logo_step=1.6,     # logo tile spacing, multiples of the logo size
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


def _grid_mask(size, o, font_path, grid):
    """Text at the centre of each of ``cols x rows`` cells, each copy rotated about its own centre."""
    w, h = size
    cols, rows = grid
    if cols < 1 or rows < 1:
        raise ValueError(f"grid needs at least 1x1, got {cols}x{rows}")
    font = load_font(int(h * o["size"]), font_path)
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    box = d.textbbox((0, 0), o["text"], font=font)
    tw, th = box[2] - box[0], box[3] - box[1]
    side = int((tw ** 2 + th ** 2) ** 0.5) + 4
    cell = Image.new("L", (side, side), 0)
    ImageDraw.Draw(cell).text(((side - tw) / 2 - box[0], (side - th) / 2 - box[1]),
                              o["text"], font=font, fill=o["opacity"])
    cell = cell.rotate(o["angle"], resample=Image.BICUBIC)
    layer = Image.new("L", size, 0)
    for r in range(rows):
        for c in range(cols):
            cx, cy = int((c + 0.5) * w / cols), int((r + 0.5) * h / rows)
            part = Image.new("L", size, 0)
            part.paste(cell, (cx - side // 2, cy - side // 2))
            layer = ImageChops.lighter(layer, part)
    return layer


def _logo_mask(size, o, logo):
    """Logo tiled diagonally. The logo's alpha (or, if opaque, its luminance against the
    background corner) is the stencil; ``logo_opacity`` scales it."""
    w, h = size
    with Image.open(logo) as src:
        lg = src.convert("RGBA")
    has_alpha = np.asarray(lg.getchannel("A")).min() < 255
    box = lg.getbbox()
    lg = lg.crop(box) if box and has_alpha else lg   # trim transparent margin only
    if not has_alpha:   # opaque file: stencil from luminance, background = corner pixel
        lum = np.asarray(lg.convert("L")).astype(np.float64)
        stencil = np.abs(lum - lum[0, 0])
        if not stencil.max():
            raise ValueError(f"logo has no visible pixels: {logo}")
        m = Image.fromarray((stencil / stencil.max() * 255).astype(np.uint8))
    else:
        m = lg.getchannel("A")
        if not np.asarray(m).max():
            raise ValueError(f"logo has no visible pixels: {logo}")
    lw = max(1, int(w * o["logo_width"]))
    m = m.resize((lw, max(1, int(lw * m.height / m.width))), Image.LANCZOS)
    m = m.point(lambda v: int(v * o["logo_opacity"] / 255))
    pad = int(max(w, h) * 0.5)
    layer = Image.new("L", (w + pad * 2, h + pad * 2), 0)
    sx, sy = max(1, int(m.width * (1 + o["logo_step"]))), max(1, int(m.height * (1 + o["logo_step"] * 2)))
    row, y = 0, 0
    while y < layer.height:
        x = -sx // 2 if row % 2 else 0
        while x < layer.width:
            layer.paste(m, (x, y))
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


def _options(opts):
    bad = set(opts) - set(DEFAULTS)
    if bad:
        raise TypeError(f"unknown watermark option(s): {sorted(bad)}")
    return {**DEFAULTS, **opts}


def _masks(size, o, font_path, logo=None, grid=None):
    ms = []
    if logo and (o["text"] or grid):
        raise ValueError("logo watermark cannot be combined with text/grid")
    if grid and not o["text"]:
        raise ValueError("grid needs watermark text (grid places the text at cell centres)")
    if logo:
        ms.append(_logo_mask(size, o, logo))
    elif o["text"] and grid:
        ms.append(_grid_mask(size, o, font_path, tuple(grid)))
    elif o["text"]:
        ms.append(_tile_mask(size, o, font_path))
    if o["corner_text"]:
        ms.append(_corner_mask(size, o, font_path))
    return ms


def _ink(im, o, ink=None):
    return ink or (o["light_ink"] if is_dark(im) else o["dark_ink"])


def mark(im, font_path=None, ink=None, logo=None, grid=None, **opts):
    """Return a new RGB image with the watermark and corner mark applied.

    ``logo`` = path of a logo image tiled diagonally in place of the text (tinted with the page
    ink). ``grid=(cols, rows)`` puts the text at cell centres instead of free tiling."""
    if logo and "text" not in opts:
        opts = {**opts, "text": ""}   # a logo replaces the text tile; only an explicit text conflicts
    o = _options(opts)
    im = im.convert("RGB")
    rgb = np.asarray(im).astype(np.float64)
    colour = np.array(_ink(im, o, ink), dtype=np.float64)
    for m in _masks(im.size, o, font_path, logo, grid):
        a = (np.asarray(m).astype(np.float64) / 255.0)[..., None]
        rgb = rgb * (1 - a) + colour * a
    return Image.fromarray(np.clip(np.rint(rgb), 0, 255).astype(np.uint8))


def unmark(im, font_path=None, ink=None, dark=None, logo=None, grid=None, **opts):
    """Invert :func:`mark`. Pass ``dark`` (True/False) when the ink choice can't be re-sampled
    from the marked page. Integer rounding in the original leaves ±1-2 levels of error."""
    if logo:
        raise ValueError("logo watermark is not reversible")
    o = _options(opts)
    im = im.convert("RGB")
    if ink is None and dark is not None:
        ink = o["light_ink"] if dark else o["dark_ink"]
    colour = np.array(_ink(im, o, ink), dtype=np.float64)
    rgb = np.asarray(im).astype(np.float64)
    for m in reversed(_masks(im.size, o, font_path, None, grid)):
        a = (np.asarray(m).astype(np.float64) / 255.0)[..., None]
        rgb = (rgb - colour * a) / np.clip(1 - a, 1e-6, None)
    return Image.fromarray(np.clip(np.rint(rgb), 0, 255).astype(np.uint8))
