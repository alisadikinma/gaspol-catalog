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


def missing_glyphs(font_path, text, font_index=0):
    """Characters of ``text`` (spaces excluded) that the font has no glyph for. Pillow draws
    those as a hollow box without any warning, so a patch would ship a box instead of an arrow."""
    from fontTools.ttLib import TTCollection, TTFont
    if str(font_path).lower().endswith((".ttc", ".otc")):
        tt = TTCollection(font_path).fonts[font_index]
    else:
        tt = TTFont(font_path, fontNumber=font_index)
    cmap = tt.getBestCmap() or {}
    seen = []
    for ch in text:
        if not ch.isspace() and ord(ch) not in cmap and ch not in seen:
            seen.append(ch)
    return seen


def _check_glyphs(font_path, texts, font_index=0):
    miss = missing_glyphs(font_path, "".join(texts), font_index)
    if miss:
        names = ", ".join(f"U+{ord(c):04X}" for c in miss)
        raise ValueError(f"font has no glyph for {names}: pick a font that has it ({font_path})")


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


def flat_fill(img, box, bg_x=None):
    """Erase ``box`` with the background colour of one sample column, row by row, no blending.
    ``bg_x`` is the column to sample (default: the first column right of the box, or the one left
    of it at the right image edge). Pick a column that holds background only. Unlike
    :func:`lerp_fill`, letters touching the box cannot bleed their colour in. Mutates and returns
    ``img``; ValueError when ``bg_x`` is outside the image."""
    x0, y0, x1, y1 = box
    a = np.asarray(img.convert("RGB")).copy()
    w = a.shape[1]
    if bg_x is None:
        bg_x = x1 if x1 < w else x0 - 1
    if not 0 <= bg_x < w:
        raise ValueError(f"bg_x {bg_x} is outside the image (width {w})")
    a[y0:y1, x0:x1] = a[y0:y1, bg_x:bg_x + 1]
    img.paste(Image.fromarray(a), (0, 0))
    return img


def erase_between(img, box, bg=None, bg_from=None):
    """Erase ``box``: ``bg`` None blends the ground on either side (:func:`lerp_fill`); an RGB
    tuple paints it flat; ``bg_from`` (a sample column x) paints each row with that column's
    colour (:func:`flat_fill`), for a box that touches letters. Mutates and returns ``img``."""
    if bg_from is not None:
        return flat_fill(img, box, bg_x=bg_from)
    if bg is None:
        return lerp_fill(img, box)
    ImageDraw.Draw(img).rectangle((box[0], box[1], box[2] - 1, box[3] - 1), fill=tuple(bg))
    return img


def line_words(img, y0, y1, x0, x1, thr=110, gap=12, dark=True):
    """x ranges ``(xa, xb)`` (inclusive) of the words in the text band ``y0:y1`` between ``x0`` and
    ``x1``. A column belongs to ink when some pixel is darker than ``thr`` (``dark=False``:
    brighter); ink columns split into words where the blank run is longer than ``gap``. Keep the
    band on the x-height so descenders of the line above or below do not join words."""
    a = np.asarray(img.convert("RGB")).astype(int)[y0:y1, x0:x1].mean(axis=2)
    cols = np.nonzero((a < thr if dark else a > thr).any(axis=0))[0]
    words = []
    for c in cols:
        c = int(c) + x0
        if words and c - words[-1][1] - 1 <= gap:
            words[-1][1] = c
        else:
            words.append([c, c])
    return [(s, e) for s, e in words]


def move_ink(img, src_box, dst_xy, clear=True, ink_sum=None, dark=True, bg_x=None):
    """Move the ink of ``src_box`` so its top-left corner lands on ``dst_xy``: only ink pixels are
    copied (r+g+b below ``ink_sum``, default 600; ``dark=False`` copies pixels above ``765 -
    ink_sum`` for light ink on a dark ground), so neighbouring tails and the new ground stay.
    With ``clear`` the source box is first painted with the per-row background of column ``bg_x``
    (default: first column right of the box; :func:`flat_fill`), never a box that overwrites
    the tails of the lines above or below. ``clear=False`` copies. Reuses the real render ink, so
    no stand-in font is needed. Mutates and returns ``img``; ValueError when the box has no ink
    or the target leaves the image."""
    x0, y0, x1, y1 = src_box
    ink_sum = 600 if ink_sum is None else ink_sum
    a = np.asarray(img.convert("RGB")).copy()
    h, w = a.shape[:2]
    tx, ty = int(dst_xy[0]), int(dst_xy[1])
    if tx < 0 or ty < 0 or tx + (x1 - x0) > w or ty + (y1 - y0) > h:
        raise ValueError(f"target {dst_xy} puts the box outside the image")
    sub = a[y0:y1, x0:x1].copy()
    s = sub.astype(int).sum(axis=2)
    mask = s < ink_sum if dark else s > 765 - ink_sum
    if not mask.any():
        raise ValueError("no ink in source box")
    if clear:
        out = Image.fromarray(a)
        flat_fill(out, src_box, bg_x=bg_x)
        a = np.asarray(out).copy()
    region = a[ty:ty + (y1 - y0), tx:tx + (x1 - x0)]
    region[mask] = sub[mask]
    img.paste(Image.fromarray(a), (0, 0))
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
    _check_glyphs(path, [text])
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


def replace_block(img, box, lines, font_path=None, fill=None, dark=True, width=None, leading=1.3,
                  max_size=40, min_size=10, font_index=0, bg=None, thr=150,
                  cap_from_ink=False, align="left", stretch_to_ink=False, bg_from=None):
    """Swap a paragraph of several lines inside ``box`` and return a new image (``img`` is not
    changed). Use it when the new text has a different number of lines than the old one, which
    :func:`replace_line` cannot do.

    The old ink is measured (``dark=False`` for light ink on a dark ground), the box is erased
    (:func:`erase_between`; ``bg`` RGB paints it flat, None blends the ground), and ``lines`` are set
    left-aligned from the old ink's top-left corner in the largest size from ``max_size`` down that
    keeps every line within ``width`` (default: box width minus the old ink's left offset).
    ``leading`` is line pitch as a multiple of the size. ``fill`` None samples the old ink colour
    (darkest pixel, or lightest with ``dark=False``). ``font_index`` picks a face in a .ttc.
    ``thr`` is the ink threshold of :func:`ink_bbox`; lower it for mid-tone light ink (gold on navy).
    ``cap_from_ink=True`` sets the size from the old ink height (for a box holding only capitals or
    digits, e.g. one number inside a headline) instead of the largest size that fits ``width``.
    Lines are placed so the top of the capitals sits on the old ink top. ``align`` ("left",
    "center", "right") places each line against the old ink's left edge, centre or right edge;
    "center" keeps even gaps when a narrower font replaces a word inside a sentence.
    ``bg_from`` (a sample column x) erases flat per row from that column instead of blending
    (:func:`flat_fill`); use it when the box touches letters.
    ``stretch_to_ink=True`` (one line only) scales the new line horizontally to the old ink width,
    so a number swapped inside a sentence in a narrower stand-in font leaves no gap (or a slightly
    longer word fits); ``width`` is then not checked.
    Raises ValueError when the box has no ink, when even ``min_size`` is too wide, or when the
    lines run past the bottom of ``box``."""
    if align not in ("left", "center", "right"):
        raise ValueError("align must be left, center or right")
    if stretch_to_ink and len(lines) != 1:
        raise ValueError("stretch_to_ink needs exactly one line")
    bbox = ink_bbox(img, box, dark=dark, thr=thr)
    if bbox is None:
        raise ValueError("no ink in box")
    if not lines:
        raise ValueError("no lines")
    path = fonts.find_font(font_path)
    _check_glyphs(path, lines, font_index)
    out = img.convert("RGB").copy()
    a = np.asarray(out)[bbox[1]:bbox[3] + 1, bbox[0]:bbox[2] + 1].reshape(-1, 3).astype(int)
    ink = tuple(fill[:3]) if fill is not None else tuple(
        int(v) for v in (a[a.sum(1).argmin()] if dark else a[a.sum(1).argmax()]))
    avail = width if width is not None else box[2] - bbox[0]
    d = ImageDraw.Draw(out)
    font = None
    if cap_from_ink:
        size = size_for_cap(path, bbox[3] - bbox[1] + 1)
        f = ImageFont.truetype(path, size, index=font_index)
        if not stretch_to_ink and max(d.textlength(t, font=f) for t in lines) > avail:
            raise ValueError(f"text wider than {avail}px at the old ink height (size {size})")
        font = f
    else:
        for size in range(max_size, min_size - 1, -1):
            f = ImageFont.truetype(path, size, index=font_index)
            if max(d.textlength(t, font=f) for t in lines) <= avail:
                font = f
                break
    if font is None:
        raise ValueError(f"text wider than {avail}px even at size {min_size}")
    pitch = int(round(size * leading))
    base = baseline_for_top(path, size, bbox[1])
    if max(d.textbbox((bbox[0], base + i * pitch), t, font=font, anchor="ls")[3]
           for i, t in enumerate(lines)) > box[3]:
        raise ValueError("lines run past the bottom of box")
    erase_between(out, box, bg=bg, bg_from=bg_from)
    if stretch_to_ink:
        x0, y0, x1, y1 = d.textbbox((0, base), lines[0], font=font, anchor="ls")
        layer = Image.new("RGBA", (x1 - x0 + 2, y1 - y0 + 2), (0, 0, 0, 0))
        ImageDraw.Draw(layer).text((1 - x0, base - y0 + 1), lines[0], font=font, fill=ink + (255,), anchor="ls")
        layer = layer.crop(layer.getbbox())
        layer = layer.resize((bbox[2] - bbox[0] + 1, layer.height), Image.LANCZOS)
        out.paste(layer, (bbox[0], y0 + (layer.getbbox()[1] if layer.getbbox() else 0)), layer)
        return out
    for i, t in enumerate(lines):
        w = d.textlength(t, font=font)
        x = {"left": bbox[0], "center": (bbox[0] + bbox[2] + 1 - w) / 2, "right": bbox[2] + 1 - w}[align]
        d.text((x, base + i * pitch), t, font=font, fill=ink, anchor="ls")
    return out


ADD_KEYS = {"size", "fill", "leading", "align"}


def add_block(img, box, lines, font_path, size, fill, leading=1.3, align="left"):
    """Write ``lines`` into an empty ``box`` (no old ink to measure): cap top of the first line at
    the box top, ``size`` px, ``fill`` RGB, line pitch ``leading`` x size. Raises ValueError when a
    line is wider than the box or the block runs past its bottom. Returns a new image.
    (2026-11-01: a missing sentence had to go into blank space on a rendered slide.)"""
    if align not in ("left", "center", "right"):
        raise ValueError("align must be left, center or right")
    out = img.convert("RGB").copy()
    d = ImageDraw.Draw(out)
    font = _font(font_path, size)
    x0, y0, x1, y1 = box
    cap = font.getbbox("H")
    top_off = cap[1]
    pitch = size * leading
    for i, t in enumerate(lines):
        w = d.textlength(t, font=font)
        if w > x1 - x0:
            raise ValueError(f"line {t!r} is {w:.0f} px wide, box is {x1 - x0}")
        y = y0 - top_off + i * pitch
        if y + font.getbbox(t)[3] > y1:
            raise ValueError(f"lines run past the bottom of box at line {i + 1}")
        x = {"left": x0, "center": (x0 + x1 - w) / 2, "right": x1 - w}[align]
        d.text((x, y), t, font=font, fill=tuple(fill))
    return out


RETYPE_KEYS = {"dark", "width", "leading", "max_size", "min_size", "font_index", "fill", "bg", "thr",
               "cap_from_ink", "align", "stretch_to_ink", "bg_from"}


def retype(spec, base_dir="."):
    """Apply a list of paragraph fixes from a spec dict (the ``deckkit retype`` file) and return
    the written paths. Spec: ``{"font": path, "fixes": [{"src", "dst", "box": [x0, y0, x1, y1],
    "lines": [...], "note": "why", ...replace_block options}]}``; ``font`` may also be set per fix.
    Paths are relative to ``base_dir``. Every fix is checked before anything is written, so a
    bad fix (unknown key, missing file, box without ink, text that does not fit) writes nothing.
    A fix whose ``src`` is an earlier fix's ``dst`` works on that earlier result, so several fixes
    on one page chain in order. A fix with ``"erase": true`` and no ``lines`` only wipes ``box``
    (a stray wordmark or mark the model drew), blending the ground or painting ``bg``. A fix
    with ``"add": {"size", "fill", "leading"?, "align"?}`` writes ``lines`` into a box that has
    no old ink (:func:`add_block`)."""
    import os
    fixes = spec.get("fixes")
    if not fixes:
        raise ValueError("spec has no fixes")
    done = {}
    for i, f in enumerate(fixes):
        need = {"src", "dst", "box"} if f.get("erase") else {"src", "dst", "box", "lines"}
        missing = need - f.keys()
        if missing:
            raise ValueError(f"fix {i}: missing {sorted(missing)}")
        extra = f.keys() - RETYPE_KEYS - {"src", "dst", "box", "lines", "font", "note", "erase", "add"}
        if extra:
            raise ValueError(f"fix {i}: unknown keys {sorted(extra)}")
        font = f.get("font", spec.get("font"))
        src = os.path.abspath(os.path.join(base_dir, f["src"]))
        if src not in done and not os.path.exists(src):
            raise FileNotFoundError(f"fix {i}: {src}")
        opts = {k: (tuple(v) if k in ("fill", "bg") else v) for k, v in f.items() if k in RETYPE_KEYS}
        base = done.get(src) or Image.open(src)
        if f.get("erase") not in (None, False, True, "flat"):
            raise ValueError(f"fix {i}: erase must be true or \"flat\", got {f['erase']!r}")
        if f.get("erase"):
            if f.get("lines"):
                raise ValueError(f"fix {i}: erase takes no lines")
            img = base.convert("RGB").copy()
            if f["erase"] == "flat" and opts.get("bg") is None and opts.get("bg_from") is None:
                flat_fill(img, tuple(f["box"]))
            else:
                erase_between(img, tuple(f["box"]), bg=opts.get("bg"), bg_from=opts.get("bg_from"))
            done[os.path.abspath(os.path.join(base_dir, f["dst"]))] = img
            continue
        if "add" in f:
            add = f["add"]
            if not isinstance(add, dict) or "size" not in add or "fill" not in add:
                raise ValueError(f"fix {i}: add needs size and fill")
            bad = add.keys() - ADD_KEYS
            if bad:
                raise ValueError(f"fix {i}: add has unknown keys {sorted(bad)}")
            try:
                img = add_block(base, tuple(f["box"]), f["lines"], font, **add)
            except ValueError as e:
                raise ValueError(f"fix {i} ({f['dst']}): {e}") from None
            done[os.path.abspath(os.path.join(base_dir, f["dst"]))] = img
            continue
        try:
            img = replace_block(base, tuple(f["box"]), f["lines"], font, **opts)
        except ValueError as e:
            raise ValueError(f"fix {i} ({f['dst']}): {e}") from None
        done[os.path.abspath(os.path.join(base_dir, f["dst"]))] = img
    for path, img in done.items():
        img.save(path)
    return list(done)


REFLOW_OPS = {"words", "move", "clear"}


def _reflow_check(i, j, op):
    where = f"fix {i} op {j}"
    kind = op.get("op")
    if kind not in REFLOW_OPS:
        raise ValueError(f"{where}: op must be one of {sorted(REFLOW_OPS)}, got {kind!r}")
    if kind == "words":
        need = {"line"}
    elif kind == "clear":
        need = {"box"}
    else:
        need = {"to"} | ({"line", "word"} if "box" not in op else {"box"})
    missing = need - op.keys()
    if missing:
        raise ValueError(f"{where}: missing {sorted(missing)}")


def reflow(spec, base_dir="."):
    """Move or remove words of rendered text from a spec dict (the ``deckkit reflow`` file) and
    return ``(written paths, words report)``. Spec: ``{"fixes": [{"src", "dst", "ops": [...]}]}``;
    paths are relative to ``base_dir``. Ops run in order on the current image:

    * ``{"op": "words", "line": [y0, y1, x0, x1], "thr", "gap", "dark"}`` lists the word x ranges
      (:func:`line_words`); the report holds one ``[[xa, xb], ...]`` per ``words`` op.
    * ``{"op": "move", "to": [x, y], "box": [x0, y0, x1, y1]}`` or ``{"line": [...], "word": N}``
      (N counts from 0; the box is then the word's columns over the line's rows, one pixel
      wider) moves the ink there (:func:`move_ink`; options ``clear``, ``ink_sum``, ``dark``,
      ``bg_x``). ``to`` is the top-left corner of the box.
    * ``{"op": "clear", "box": [...], "bg_x": N}`` wipes a box flat (:func:`flat_fill`).

    Every fix is run on a copy before anything is saved, so a bad op (unknown op, missing key,
    word index out of range, no ink) writes nothing. A fix whose ``src`` is an earlier ``dst``
    works on that result."""
    import os
    fixes = spec.get("fixes")
    if not fixes:
        raise ValueError("spec has no fixes")
    done, report = {}, []
    for i, f in enumerate(fixes):
        missing = {"src", "dst", "ops"} - f.keys()
        if missing:
            raise ValueError(f"fix {i}: missing {sorted(missing)}")
        src = os.path.abspath(os.path.join(base_dir, f["src"]))
        if src not in done and not os.path.exists(src):
            raise FileNotFoundError(f"fix {i}: {src}")
        img = (done.get(src) or Image.open(src)).convert("RGB").copy()
        for j, op in enumerate(f["ops"]):
            _reflow_check(i, j, op)
            try:
                if op["op"] == "words":
                    y0, y1, x0, x1 = op["line"]
                    report.append([list(w) for w in line_words(
                        img, y0, y1, x0, x1, **{k: op[k] for k in ("thr", "gap", "dark") if k in op})])
                elif op["op"] == "clear":
                    flat_fill(img, tuple(op["box"]), bg_x=op.get("bg_x"))
                else:
                    if "box" in op:
                        box = tuple(op["box"])
                    else:
                        y0, y1, x0, x1 = op["line"]
                        ws = line_words(img, y0, y1, x0, x1, **{k: op[k] for k in ("thr", "gap", "dark") if k in op})
                        if not 0 <= op["word"] < len(ws):
                            raise ValueError(f"word {op['word']} not in line ({len(ws)} words)")
                        box = (ws[op["word"]][0], y0, ws[op["word"]][1] + 1, y1)
                    move_ink(img, box, tuple(op["to"]),
                             **{k: op[k] for k in ("clear", "ink_sum", "dark", "bg_x") if k in op})
            except ValueError as e:
                raise ValueError(f"fix {i} op {j} ({f['dst']}): {e}") from None
        done[os.path.abspath(os.path.join(base_dir, f["dst"]))] = img
    for path, img in done.items():
        img.save(path)
    return list(done), report
