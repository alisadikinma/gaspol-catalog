"""Signature and company stamp onto an existing PDF letter, keeping its text selectable.

The letter is usually exported from Word by someone else and changes between drafts, so items
are placed relative to a text anchor on the page (e.g. the signer's printed name) rather than at
fixed coordinates. Plan file::

    {"src": "letter.pdf", "dst": "letter-signed.pdf",
     "items": [
       {"image": "sig.png",   "anchor": "Nama Penanda Tangan", "dx": -10, "dy": -62, "width": 120},
       {"image": "stamp.jpg", "anchor": "Nama Penanda Tangan", "dx": -60, "dy": -80, "width": 95,
        "opacity": 0.85}
     ]}

``dx``/``dy`` are points from the top-left corner of the anchor text; negative ``dy`` is above
it. ``page`` (1-based) limits the anchor search; without it the LAST page holding the anchor is
used, because a signer's name usually also appears earlier in the body. A white background
(JPEG stamps, scanned signatures) is made transparent unless ``"keep_white": true``, and the
image is cropped to its ink (``"trim": false`` to keep the margins) so ``width`` means the width
of the signature itself, not of the scan around it.
"""
import io
import json
from pathlib import Path

from PIL import Image


def _transparent_png(path, opacity=1.0, keep_white=False, white_level=235, trim=True):
    im = Image.open(path).convert("RGBA")
    if not keep_white:
        px = im.getdata()
        im.putdata([(r, g, b, 0) if min(r, g, b) >= white_level else (r, g, b, a) for r, g, b, a in px])
    if trim and not keep_white:
        box = im.getchannel("A").getbbox()
        if box:
            im = im.crop(box)
    if opacity < 1.0:
        alpha = im.getchannel("A").point(lambda v: int(v * opacity))
        im.putalpha(alpha)
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return buf.getvalue(), im.size


def _find_anchor(doc, text, page=None):
    pages = [page - 1] if page else range(len(doc) - 1, -1, -1)
    for i in pages:
        hits = doc[i].search_for(text)
        if hits:
            return i, hits[-1]
    raise ValueError(f"anchor text {text!r} not found" + (f" on page {page}" if page else ""))


def sign(plan, base=None):
    """Apply ``plan`` (dict or path to JSON). Relative paths resolve against the plan's folder.
    Returns a list of (page, rect) actually used, one per item."""
    import pymupdf

    if not isinstance(plan, dict):
        base = Path(plan).parent
        plan = json.loads(Path(plan).read_text())
    base = Path(base or ".")
    res = lambda p: str(p if Path(p).is_absolute() else base / p)
    items = plan.get("items") or []
    if not items:
        raise ValueError("plan has no items")
    doc = pymupdf.open(res(plan["src"]))
    placed = []
    for it in items:
        data, (w_px, h_px) = _transparent_png(res(it["image"]), it.get("opacity", 1.0), it.get("keep_white", False),
                                              trim=it.get("trim", True))
        if "anchor" in it:
            i, r = _find_anchor(doc, it["anchor"], it.get("page"))
            x0, y0 = r.x0 + it.get("dx", 0), r.y0 + it.get("dy", 0)
        else:
            i = it.get("page", len(doc)) - 1
            x0, y0 = it["x"], it["y"]
        w = it["width"]
        rect = pymupdf.Rect(x0, y0, x0 + w, y0 + w * h_px / w_px)
        doc[i].insert_image(rect, stream=data, overlay=True)
        placed.append((i + 1, tuple(round(v, 1) for v in rect)))
    out = res(plan["dst"])
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    doc.save(out, garbage=3, deflate=True)
    return placed
