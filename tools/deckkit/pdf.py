"""Pages -> one PDF, optionally watermarked, scaled to one page size, with pages skippable.

Uses Pillow's own PDF writer (no img2pdf). Pages of different pixel sizes (a 4K render next to
a reused 2752x1536 page) are all scaled to ``page_size`` first, otherwise the PDF pages differ
and the file bloats.
"""
import os
import re
from pathlib import Path

from PIL import Image

from . import watermark


def list_pages(src, pattern=r"\d{2}\.png|slide-\d+\.png", skip=()):
    names = sorted(f for f in os.listdir(src) if re.fullmatch(pattern, f) and f not in set(skip))
    if not names:
        raise FileNotFoundError(f"no pages matching {pattern!r} in {src}")
    return [os.path.join(src, n) for n in names]


def build_pdf(pages, out, page_size=None, dpi=150, mark_opts=None, marked_dir=None, font_path=None):
    """``pages`` = image paths in order. ``mark_opts`` (dict for :func:`watermark.mark`) turns the
    watermark on; ``marked_dir`` keeps the marked PNGs for inspection. Returns the page count."""
    images = []
    for p in pages:
        im = Image.open(p).convert("RGB")
        if page_size and im.size != tuple(page_size):
            im = im.resize(tuple(page_size), Image.LANCZOS)
        if mark_opts is not None:
            im = watermark.mark(im, font_path=font_path, **mark_opts)
            if marked_dir:
                Path(marked_dir).mkdir(parents=True, exist_ok=True)
                im.save(os.path.join(marked_dir, os.path.basename(str(p))))
        images.append(im)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    images[0].save(out, "PDF", resolution=dpi, save_all=True, append_images=images[1:])
    return len(images)
