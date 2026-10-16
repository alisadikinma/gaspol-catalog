"""Add a footer band under a page: a confidentiality line on the left, logos on the right."""
from PIL import Image, ImageDraw

from .fonts import load_font

GREY = (90, 106, 114)
RULE = (211, 222, 223)


def trim(img):
    """Crop transparent margins."""
    img = img.convert("RGBA")
    return img.crop(img.getbbox())


def add_band(page, text, logos=(), band_frac=0.055, bg=(255, 255, 255), ink=GREY, rule=RULE, sep="×",
             font_path=None):
    """Return a new image ``band_frac`` taller than ``page``.

    ``logos`` is a left-to-right list of PIL images shown at the right edge, separated by ``sep``.
    The first logo is drawn tallest (primary brand), later ones smaller (the seller's lockup).
    """
    page = page.convert("RGB")
    w, h = page.size
    b = int(w * band_frac)
    out = Image.new("RGB", (w, h + b), bg)
    out.paste(page, (0, 0))
    d = ImageDraw.Draw(out)
    d.line([(0, h), (w, h)], fill=rule, width=3)
    pad = int(w * 0.03)
    d.text((pad, h + b // 2), text, font=load_font(int(b * 0.26), font_path), fill=ink, anchor="lm")
    fsep = load_font(int(b * 0.34), font_path)
    gap = int(b * 0.3)
    x = w - pad
    for i, logo in enumerate(reversed(list(logos))):
        target = int(b * (0.78 if i == len(logos) - 1 else 0.34))
        lg = trim(logo)
        lg = lg.resize((max(1, int(lg.width * target / lg.height)), target), Image.LANCZOS)
        x -= lg.width
        out.paste(lg, (x, h + (b - target) // 2), lg)
        if i < len(logos) - 1:
            x -= gap + int(d.textlength(sep, font=fsep))
            d.text((x, h + b // 2), sep, font=fsep, fill=ink, anchor="lm")
            x -= gap
    return out
