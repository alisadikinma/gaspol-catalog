"""Small labels drawn in code: a pill and a striped flag. No image model."""
from PIL import Image, ImageDraw

from .fonts import load_font

_SS = 4  # supersampling for smooth rounded ends


def pill(text, font_path=None, size=28, fg=(255, 255, 255), bg=(35, 133, 127), pad=(18, 8)):
    """RGBA pill: ``text`` centred on a fully rounded bar. Corners are transparent."""
    font = load_font(size, font_path)
    text = str(text)
    l, t, r, b = font.getbbox(text, anchor="ls") if text else (0, 0, 0, 0)
    cap = -font.getbbox("H", anchor="ls")[1]
    px, py = pad
    w = max(int(round(r - l)) + 2 * px, 1)
    h = max(cap + 2 * py, 2)
    layer = Image.new("RGBA", (w * _SS, h * _SS), (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle(
        (0, 0, w * _SS - 1, h * _SS - 1), radius=h * _SS // 2, fill=tuple(bg) + (255,))
    out = layer.resize((w, h), Image.LANCZOS)
    if text:
        ImageDraw.Draw(out).text((px - l, py + cap), text, font=font, fill=tuple(fg) + (255,), anchor="ls")
    return out


def flag(colours, size, stripes="h"):
    """RGB flag of equal stripes. ``stripes`` "h" = bands stacked top to bottom, "v" = left to right."""
    if not colours:
        raise ValueError("flag needs at least one colour")
    if stripes not in ("h", "v"):
        raise ValueError(f"stripes must be 'h' or 'v', got {stripes!r}")
    w, h = size
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    n = len(colours)
    for i, c in enumerate(colours):
        if stripes == "h":
            d.rectangle((0, h * i // n, w - 1, h * (i + 1) // n - 1), fill=tuple(c))
        else:
            d.rectangle((w * i // n, 0, w * (i + 1) // n - 1, h - 1), fill=tuple(c))
    return img
