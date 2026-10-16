"""Wrap page images into a 16:9 PPTX, one full-bleed picture per slide.

Needs ``python-pptx`` (imported lazily). Feed it the CLEAN pages, not the watermarked PDF set.
"""
from pathlib import Path


def build_pptx(images, out, width_in=13.333, height_in=7.5):
    try:
        from pptx import Presentation
        from pptx.util import Inches
    except ImportError as exc:
        raise RuntimeError("build_pptx needs python-pptx: pip install python-pptx") from exc
    for p in images:
        if not Path(p).exists():
            raise FileNotFoundError(p)
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(width_in), Inches(height_in)
    blank = prs.slide_layouts[6]
    for p in images:
        s = prs.slides.add_slide(blank)
        s.shapes.add_picture(str(p), 0, 0, width=prs.slide_width, height=prs.slide_height)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    prs.save(out)
    return len(images)
