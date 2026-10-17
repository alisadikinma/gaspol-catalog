"""Fix text in an already-rendered page without re-rendering it.

Re-rendering re-rolls every approved string on the page; patching changes only the words you
name. Workflow: find the old ink with :func:`ink_bbox`, erase it (:func:`blend_fill` for a smooth
gradient, a plain fill for flat colour), measure the old text's cap height and width, then
:func:`fit` the replacement to those and :func:`paste_text` it.

The typeface must be the one the page was set in (supply ``font_path`` per weight); match is
only as good as the font.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from . import fonts


def _font(font_path, size):
    return ImageFont.truetype(font_path, size)


def ink_bbox(img, box, dark=True, thr=150):
    """Bounding box (x0, y0, x1, y1) of dark (or light) ink inside ``box``, or None."""
    a = np.asarray(img.convert("RGB")).astype(int)
    sub = a[box[1]:box[3], box[0]:box[2]].mean(axis=2)
    ys, xs = np.nonzero(sub < thr if dark else sub > thr)
    if not len(xs):
        return None
    return (int(xs.min()) + box[0], int(ys.min()) + box[1], int(xs.max()) + box[0], int(ys.max()) + box[1])


def render_text(text, font_path, size, fill, tracking=0.0):
    """``text`` on a transparent canvas with per-character tracking, cropped to its ink."""
    f = _font(font_path, size)
    pad = int(size * 1.5)
    canvas = Image.new("RGBA", (int(size * len(text) * 1.6) + pad * 2, size * 3 + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(canvas)
    x = float(pad)
    for ch in text:
        d.text((x, pad), ch, font=f, fill=fill)
        x += d.textlength(ch, font=f) + tracking
    return canvas.crop(canvas.getbbox())


def fit(text, font_path, target_w, cap_h, fill, tol=1):
    """Pick the font size whose capital H is ``cap_h`` px tall, then the tracking that makes the
    string ``target_w`` wide. Returns ``(size, tracking)``."""
    size = None
    for s in range(6, 400):
        c = Image.new("L", (s * 3, s * 3), 255)
        ImageDraw.Draw(c).text((s // 2, s // 2), "H", font=_font(font_path, s), fill=0)
        ys, _ = np.nonzero(np.asarray(c) < 128)
        if len(ys) and ys.max() - ys.min() + 1 >= cap_h:
            size = s
            break
    if size is None:
        raise ValueError("no font size reaches that cap height")
    lo, hi = -size * 0.2, size * 0.4
    mid = 0.0
    for _ in range(40):
        mid = (lo + hi) / 2
        w = render_text(text, font_path, size, fill, mid).width
        if abs(w - target_w) <= tol:
            break
        lo, hi = (mid, hi) if w < target_w else (lo, mid)
    return size, mid


def blend_fill(img, box, iterations=600):
    """Erase ``box`` by diffusing the surrounding pixels inwards (Laplace inpaint). Use inside a
    smooth gradient, where a flat rectangle leaves a visible patch. Mutates and returns ``img``."""
    x0, y0, x1, y1 = box
    a = np.asarray(img.convert("RGB")).astype(float)
    region = a[y0 - 1:y1 + 1, x0 - 1:x1 + 1].copy()
    border = np.concatenate([region[0], region[-1], region[:, 0], region[:, -1]])
    region[1:-1, 1:-1] = border.mean(axis=0)
    for _ in range(iterations):
        region[1:-1, 1:-1] = 0.25 * (region[:-2, 1:-1] + region[2:, 1:-1] + region[1:-1, :-2] + region[1:-1, 2:])
    a[y0:y1, x0:x1] = region[1:-1, 1:-1]
    img.paste(Image.fromarray(a.clip(0, 255).astype(np.uint8)), (0, 0))
    return img


def paste_text(img, patch, xy, anchor="lb"):
    """Paste ``patch`` with its bottom edge at y. ``anchor`` 'lb' = x is the left edge,
    'cb' = x is the centre."""
    x, y = xy
    if anchor == "cb":
        x -= patch.width // 2
    img.paste(patch, (int(x), int(y - patch.height)), patch)
    return img


def glow_text(text, font_path, size, tracking, core, glow, radius=7, strength=2.2):
    """HUD-style lettering: bright ``core`` over a soft ``glow`` bloom (RGB tuples)."""
    core_layer = render_text(text, font_path, size, core, tracking)
    pad = int(radius * 6)
    xy = (core_layer.width + pad * 2, core_layer.height + pad * 2)
    mask = Image.new("L", xy, 0)
    mask.paste(core_layer.getchannel("A"), (pad, pad))
    arr = np.zeros(xy[::-1], dtype=float)
    for r, wgt in ((radius * 3, 1.0), (radius, 0.9), (radius / 2.5, 0.7)):
        arr += wgt * np.asarray(mask.filter(ImageFilter.GaussianBlur(r))).astype(float)
    out = Image.new("RGBA", xy, tuple(glow[:3]) + (0,))
    out.putalpha(Image.fromarray(np.clip(arr * strength, 0, 255).astype(np.uint8)))
    top = Image.new("RGBA", xy, (0, 0, 0, 0))
    top.paste(core_layer, (pad, pad), core_layer)
    return Image.alpha_composite(out, top)


def emblem_text(text, font_path, size, core, glow, ring=None, tracking=0.0, radius=7, ring_width=None):
    """A round emblem: ``text`` as glowing lettering (:func:`glow_text`) centred in a transparent
    disc-shaped RGBA square, with an optional ``ring`` colour outline. The square is sized so the
    lettering and its bloom fit inside the circle. Paste it over an erased emblem with
    :func:`paste_text` (``anchor='cb'``) or ``img.paste(em, xy, em)``."""
    font_path = fonts.find_font(font_path)
    lettering = glow_text(text, font_path, size, tracking, core, glow, radius=radius)
    diameter = int(np.ceil(np.hypot(lettering.width, lettering.height))) + 4
    em = Image.new("RGBA", (diameter, diameter), (0, 0, 0, 0))
    em.paste(lettering, ((diameter - lettering.width) // 2, (diameter - lettering.height) // 2), lettering)
    # outside the circle stays transparent whatever the bloom reached
    disc = Image.new("L", (diameter, diameter), 0)
    ImageDraw.Draw(disc).ellipse((0, 0, diameter - 1, diameter - 1), fill=255)
    em.putalpha(Image.fromarray(np.minimum(np.asarray(em.getchannel("A")), np.asarray(disc))))
    if ring is not None:
        rw = ring_width or max(2, size // 12)
        d = ImageDraw.Draw(em)
        d.ellipse((0, 0, diameter - 1, diameter - 1), outline=tuple(ring[:3]) + (255,), width=rw)
    return em


def fill_from_side(img, box, side="left"):
    """Erase ``box`` by repeating the pixel line just outside it on ``side`` ('left', 'right',
    'top' or 'bottom') across the box: the left or right column repeats horizontally, the top or
    bottom row repeats vertically. Right for a box in a vertical or horizontal gradient that runs
    along the other axis. ValueError for an unknown side or a box flush with that image edge.
    Mutates and returns ``img``."""
    if side not in ("left", "right", "top", "bottom"):
        raise ValueError(f"side must be left, right, top or bottom, got {side!r}")
    x0, y0, x1, y1 = box
    a = np.asarray(img.convert("RGB")).copy()
    h, w = a.shape[:2]
    if (side == "left" and x0 < 1) or (side == "right" and x1 >= w) \
            or (side == "top" and y0 < 1) or (side == "bottom" and y1 >= h):
        raise ValueError(f"no pixels on the {side} of the box to repeat")
    if side == "left":
        a[y0:y1, x0:x1] = a[y0:y1, x0 - 1:x0]
    elif side == "right":
        a[y0:y1, x0:x1] = a[y0:y1, x1:x1 + 1]
    elif side == "top":
        a[y0:y1, x0:x1] = a[y0 - 1:y0, x0:x1]
    else:
        a[y0:y1, x0:x1] = a[y1:y1 + 1, x0:x1]
    img.paste(Image.fromarray(a), (0, 0))
    return img


def lerp_fill(img, box, margin=3):
    """Erase ``box`` row by row: each row blends the mean colour of the ``margin`` columns just
    left of the box into the mean just right of it. Reproduces a horizontal gradient and a flat
    ground alike. At an image edge the one available side is used. Mutates and returns ``img``."""
    x0, y0, x1, y1 = box
    a = np.asarray(img.convert("RGB")).astype(float)
    w = a.shape[1]
    left = a[y0:y1, max(0, x0 - margin):x0] if x0 > 0 else None
    right = a[y0:y1, x1:min(w, x1 + margin)] if x1 < w else None
    if left is None and right is None:
        raise ValueError("no surrounding pixels to sample")
    lm = left.mean(axis=1) if left is not None else right.mean(axis=1)
    rm = right.mean(axis=1) if right is not None else lm
    t = np.linspace(0.0, 1.0, x1 - x0)[None, :, None]
    a[y0:y1, x0:x1] = lm[:, None, :] * (1 - t) + rm[:, None, :] * t
    img.paste(Image.fromarray(a.clip(0, 255).round().astype(np.uint8)), (0, 0))
    return img


def erase_between(img, box, bg=None):
    """Erase ``box``: ``bg`` None blends the ground on either side (:func:`lerp_fill`); an RGB
    tuple paints it flat. Mutates and returns ``img``."""
    if bg is None:
        return lerp_fill(img, box)
    ImageDraw.Draw(img).rectangle((box[0], box[1], box[2] - 1, box[3] - 1), fill=tuple(bg))
    return img


def _cap_height(font_path, size):
    return -_font(font_path, size).getbbox("H", anchor="ls")[1]


def size_for_cap(font_path, cap_h):
    """Font size (px) whose capital H is closest to ``cap_h`` px tall."""
    for s in range(4, 600):
        if _cap_height(font_path, s) >= cap_h:
            if s > 4 and cap_h - _cap_height(font_path, s - 1) < _cap_height(font_path, s) - cap_h:
                return s - 1
            return s
    raise ValueError("no font size reaches that cap height")


def baseline_for_top(font_path, size, top):
    """Baseline y that puts the top of capital letters at ``top``."""
    return top + _cap_height(font_path, size)


def _ink_colour(img, bbox, thr=150, dark=True):
    a = np.asarray(img.convert("RGB")).astype(int)[bbox[1]:bbox[3] + 1, bbox[0]:bbox[2] + 1].reshape(-1, 3)
    lum = a.mean(axis=1)
    if dark:
        ink = a[lum <= np.percentile(lum[lum < thr], 25)]
    else:
        ink = a[lum >= np.percentile(lum[lum > thr], 75)]
    return tuple(int(v) for v in ink.mean(axis=0))


def _line_layer(text, font, tracking, fill, pad):
    """RGBA layer with ``text`` set from x=pad on baseline y=pad+ascent; returns (layer, baseline)."""
    asc = -font.getbbox("H", anchor="ls")[1] + font.size
    layer = Image.new("RGBA", (int(font.size * len(text) * 1.6) + pad * 2, asc * 2 + pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x, base = float(pad), asc
    for ch in text:
        d.text((x, base), ch, font=font, fill=fill, anchor="ls")
        x += d.textlength(ch, font=font) + tracking
    return layer, base


def replace_line(img, box, text, font_path=None, fill=None, align="left", squeeze=False, dark=True):
    """Swap one text line inside ``box`` and return a new image (``img`` is not changed).

    The old ink is measured, the box is lerp-filled, and ``text`` is set at the old ink's cap
    height, top aligned to the old ink. ``fill`` None samples the old ink colour. ``align`` keeps
    the old ink's left edge, right edge or centre. Text wider than the box raises ValueError;
    ``squeeze=True`` first tracks it down to -0.04 em. ``dark=False`` reads light ink on a dark
    ground (the default reads dark ink). The old ink height is read as the cap
    height, so a line carrying descenders in its old text sets slightly small."""
    bbox = ink_bbox(img, box, dark=dark)
    if bbox is None:
        raise ValueError("no ink in box")
    if align not in ("left", "right", "center"):
        raise ValueError("align must be left, right or center")
    path = fonts.find_font(font_path)
    ink = tuple(fill[:3]) if fill is not None else _ink_colour(img, bbox, dark=dark)
    size = size_for_cap(path, bbox[3] - bbox[1] + 1)
    font = _font(path, size)
    avail = box[2] - box[0]
    pad = size
    layer, base = _line_layer(text, font, 0.0, ink + (255,), pad)
    ink_w = layer.getbbox()[2] - layer.getbbox()[0]
    if ink_w > avail and len(text) > 1:
        tracking = (avail - ink_w) / (len(text) - 1)
        if not squeeze or tracking < -0.04 * size:
            raise ValueError(f"text wider than box: {ink_w}px > {avail}px")
        layer, base = _line_layer(text, font, tracking, ink + (255,), pad)
        ink_w = layer.getbbox()[2] - layer.getbbox()[0]
    if ink_w > avail:
        raise ValueError(f"text wider than box: {ink_w}px > {avail}px")
    if align == "left":
        x = bbox[0]
    elif align == "right":
        x = bbox[2] + 1 - ink_w
    else:
        x = (bbox[0] + bbox[2] + 1 - ink_w) // 2
    x = max(box[0], min(x, box[2] - ink_w))
    out = img.convert("RGB").copy()
    lerp_fill(out, box)
    layer = layer.crop((layer.getbbox()[0], 0, layer.getbbox()[2], layer.height))
    top = baseline_for_top(path, size, bbox[1]) - base
    out.paste(layer, (int(x), int(top)), layer)
    return out
