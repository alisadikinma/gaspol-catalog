"""Font lookup shared by every deckkit module."""
import os

from PIL import ImageFont

CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]


def _explicit(path, px):
    """An explicitly requested font must open; never silently replaced by another."""
    if not os.path.isfile(path):
        raise FileNotFoundError(f"font file not found: {path}")
    try:
        return ImageFont.truetype(path, int(px))
    except OSError as exc:
        raise FileNotFoundError(f"font file cannot be opened: {path} ({exc})") from None


def load_font(px, path=None):
    """``path`` (a .ttf) must open or FileNotFoundError. With no path: first CANDIDATES font that
    opens, else PIL's default bitmap font."""
    if path:
        return _explicit(path, px)
    for p in CANDIDATES:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, int(px))
            except OSError:
                continue
    return ImageFont.load_default()


def find_font(path=None):
    """Path of the font file to use: ``path`` if given (must open), else the first of CANDIDATES
    that opens. Raises FileNotFoundError when none opens."""
    if path:
        _explicit(path, 12)
        return path
    for p in CANDIDATES:
        if os.path.exists(p):
            try:
                ImageFont.truetype(p, 12)
            except OSError:
                continue
            return p
    raise FileNotFoundError("no usable font file; pass font_path")
