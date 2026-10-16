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
