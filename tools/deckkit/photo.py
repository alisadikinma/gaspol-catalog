"""Put a real photo into a photo well or an empty circle an image model left blank.

Models draw faces and places badly, so the render asks for an empty well and the real photo is
placed afterwards. The photo is cover-cropped (fills the box, keeps the centre) and masked with an
antialiased shape drawn at 4x, so pixels outside the box or circle never change.
"""
from PIL import Image, ImageChops, ImageDraw

SS = 4  # mask supersampling


def cover(photo, size):
    """Scale ``photo`` to fill ``size`` (w, h) and crop the overflow around the centre."""
    w, h = (int(v) for v in size)
    if w < 1 or h < 1:
        raise ValueError(f"size must be positive, got {size}")
    s = max(w / photo.width, h / photo.height)
    nw, nh = max(w, round(photo.width * s)), max(h, round(photo.height * s))
    p = photo.resize((nw, nh), Image.LANCZOS)
    left, top = (nw - w) // 2, (nh - h) // 2
    return p.crop((left, top, left + w, top + h))


def _check_box(page, box):
    x, y, w, h = (int(v) for v in box)
    if w < 1 or h < 1 or x < 0 or y < 0 or x + w > page.width or y + h > page.height:
        raise ValueError(f"box {tuple(box)} is not inside the {page.width}x{page.height} page")
    return x, y, w, h


def _paste(page, photo, box, shape):
    x, y, w, h = _check_box(page, box)
    fitted = cover(photo.convert("RGBA"), (w, h))
    mask = Image.new("L", (w * SS, h * SS), 0)
    shape(ImageDraw.Draw(mask), w * SS, h * SS)
    mask = mask.resize((w, h), Image.BOX)
    alpha = ImageChops.multiply(mask, fitted.getchannel("A"))
    out = page.convert("RGB").copy()
    out.paste(fitted.convert("RGB"), (x, y), alpha)
    return out


def place(page, photo, box, radius=0):
    """Return a copy of ``page`` with ``photo`` cover-cropped into ``box`` = (x, y, w, h), corners
    rounded by ``radius`` px (clamped to half the shorter side). Box outside page: ValueError."""
    if radius < 0:
        raise ValueError(f"radius must be >= 0, got {radius}")
    _, _, w, h = _check_box(page, box)
    r = min(radius, min(w, h) / 2)

    def shape(d, sw, sh):
        d.rounded_rectangle((0, 0, sw - 1, sh - 1), radius=r * SS, fill=255)
    return _paste(page, photo, box, shape)


def circle(page, photo, centre, r):
    """Return a copy of ``page`` with ``photo`` cover-cropped into the circle at ``centre``
    (cx, cy) with radius ``r``. Circle outside page: ValueError."""
    r = int(r)
    if r < 1:
        raise ValueError(f"r must be >= 1, got {r}")
    cx, cy = (int(v) for v in centre)

    def shape(d, sw, sh):
        d.ellipse((0, 0, sw - 1, sh - 1), fill=255)
    return _paste(page, photo, (cx - r, cy - r, 2 * r, 2 * r), shape)
