"""Add a footer band under a page: a confidentiality line on the left, logos on the right."""
from PIL import Image, ImageDraw

from .fonts import load_font

GREY = (90, 106, 114)
RULE = (211, 222, 223)


def trim(img):
    """Crop transparent margins."""
    img = img.convert("RGBA")
    return img.crop(img.getbbox())


def letterbox(page, size):
    """Scale ``page`` to fit inside ``size`` and pad with its own edge colour (top-left pixel)."""
    page = page.convert("RGB")
    cw, ch = size
    if page.size == (cw, ch):
        return page
    s = min(cw / page.width, ch / page.height)
    r = page.resize((max(1, int(page.width * s)), max(1, int(page.height * s))), Image.LANCZOS)
    out = Image.new("RGB", (cw, ch), r.getpixel((min(5, r.width - 1), min(5, r.height - 1))))
    out.paste(r, ((cw - r.width) // 2, (ch - r.height) // 2))
    return out


def add_band(page, text, logos=(), band_frac=0.055, bg=(255, 255, 255), ink=GREY, rule=RULE, sep="×",
             font_path=None, url=None, number=None, total=None, number_fmt="{n} / {total}", fit_canvas=None):
    """Return a new image ``band_frac`` taller than ``page``.

    ``logos`` is a left-to-right list of PIL images shown at the right edge, separated by ``sep``.
    The first logo is drawn tallest (primary brand), later ones smaller (the seller's lockup).
    ``url`` is a small line right-aligned under the logos. ``fit_canvas=(W, H)`` letterboxes the page
    to exactly W x H first, so the output is W x (H + band). ``number`` is drawn at the band's right
    end only when given (never before the renders are approved); ``number_fmt`` takes ``{n}``/``{total}``.
    """
    page = letterbox(page, fit_canvas) if fit_canvas else page.convert("RGB")
    w, h = page.size
    b = int(w * band_frac)
    out = Image.new("RGB", (w, h + b), bg)
    out.paste(page, (0, 0))
    d = ImageDraw.Draw(out)
    d.line([(0, h), (w, h)], fill=rule, width=3)
    pad = int(w * 0.03)
    d.text((pad, h + b // 2), text, font=load_font(int(b * 0.26), font_path), fill=ink, anchor="lm")
    x = w - pad
    if number is not None:
        label = number_fmt.format(n=number, total=total)
        fnum = load_font(int(b * 0.3), font_path)
        d.text((x, h + b // 2), label, font=fnum, fill=ink, anchor="rm")
        x -= int(d.textlength(label, font=fnum)) + int(b * 0.5)
    right = x
    furl = load_font(int(b * 0.2), font_path)
    ulen = int(b * 0.2) + int(b * 0.07) if url else 0
    scale = 0.5 if url else 1.0
    fsep = load_font(int(b * 0.34 * scale), font_path)
    gap = int(b * 0.3 * scale)
    for i, logo in enumerate(reversed(list(logos))):
        target = int(b * (0.78 if i == len(logos) - 1 else 0.34) * scale)
        lg = trim(logo)
        lg = lg.resize((max(1, int(lg.width * target / lg.height)), target), Image.LANCZOS)
        x -= lg.width
        out.paste(lg, (x, h + (b - target - ulen) // 2), lg)
        if i < len(logos) - 1:
            x -= gap + int(d.textlength(sep, font=fsep))
            d.text((x, h + (b - ulen) // 2 + target // 2), sep, font=fsep, fill=ink, anchor="lm")
            x -= gap
    if url:
        top = h + (b - int(b * 0.78 * scale) - ulen) // 2 + int(b * 0.78 * scale) + int(b * 0.07)
        d.text((right, top), url, font=furl, fill=ink, anchor="ra")
    return out
