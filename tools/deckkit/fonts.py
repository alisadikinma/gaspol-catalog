"""Font lookup shared by every deckkit module."""
import os

from PIL import ImageFont

CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]


def load_font(px, path=None):
    """First font that opens. ``path`` (a .ttf) wins; falls back to PIL's default bitmap font."""
    for p in ([path] if path else []) + CANDIDATES:
        if p and os.path.exists(p):
            try:
                return ImageFont.truetype(p, int(px))
            except OSError:
                continue
    return ImageFont.load_default()
