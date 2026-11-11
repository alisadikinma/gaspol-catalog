"""Two-logo lockup ("seller x client"): trim, make white transparent, equal height, join with a mark.

Output is a transparent RGBA PNG, ready for a magenta cover slot (``compose`` op ``logo``, flat) or
for the footer band (``band --logos`` with the trimmed single logos from ``--trim-out``)."""
from PIL import Image, ImageDraw

from . import compose, fonts

SEP_INK = (110, 120, 128, 255)
NEAR_WHITE = 238  # pixels whose darkest channel is above this become transparent


def trim(im, thr=18):
    """Crop transparent and white margin (``thr`` = tolerance, see ``compose.trim``), then make the
    remaining near-white pixels transparent so no white box shows on a coloured page."""
    flat = Image.alpha_composite(Image.new("RGBA", im.size, (255, 255, 255, 255)), im.convert("RGBA"))
    if not any(min(p[:3]) <= 255 - max(thr, 1) for p in flat.getdata()):
        raise ValueError("logo is empty: nothing left after trimming the white margin")
    out = compose.trim(flat, thr)
    out.putdata([(r, g, b, 0 if min(r, g, b) > NEAR_WHITE else 255) for r, g, b, _ in out.getdata()])
    return out


def _open(path):
    try:
        with Image.open(path) as im:
            im.load()
            return im.copy()
    except FileNotFoundError:
        raise FileNotFoundError(f"logo not found: {path}") from None
    except OSError as exc:
        raise ValueError(f"cannot read logo {path}: {exc}") from None


def _fit(im, h):
    return im.resize((max(1, round(im.width * h / im.height)), h), Image.LANCZOS)


def lockup(logos, height=300, sep="×", gap=None, second_scale=0.78, font=None, sep_width=None,
           thr=18, parts=None):
    """Two logo files -> one RGBA image ``height`` px tall.

    The first logo gets the full height, the second ``second_scale`` of it (a lockup looks balanced
    when the client mark is a bit smaller). ``sep`` sits centred between them in a cell
    ``sep_width`` wide (default 0.3*height) with ``gap`` on each side (default 0.233*height).
    ``font`` is a .ttf path (default: the shared deckkit font search). If ``parts`` is a list, the
    scaled single logos are appended to it (for ``--trim-out``)."""
    logos = list(logos)
    if len(logos) != 2:
        raise ValueError(f"a lockup needs exactly 2 logos, got {len(logos)}")
    if height < 10:
        raise ValueError(f"--height must be at least 10 px, got {height}")
    gap = round(height * 0.233) if gap is None else int(gap)
    sep_width = round(height * 0.3) if sep_width is None else int(sep_width)
    f = fonts.load_font(height // 2, font)
    first = _fit(trim(_open(logos[0]), thr), height)
    second = _fit(trim(_open(logos[1]), thr), max(1, round(height * second_scale)))
    if parts is not None:
        parts.extend([first, second])
    width = first.width + gap + sep_width + gap + second.width
    out = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    out.paste(first, (0, (height - first.height) // 2), first)
    cx = first.width + gap + sep_width // 2
    ImageDraw.Draw(out).text((cx, height // 2), sep, font=f, fill=SEP_INK, anchor="mm")
    out.paste(second, (first.width + gap + sep_width + gap, (height - second.height) // 2), second)
    return out


def square(path, size=720, safe=0.8, bg=(255, 255, 255)):
    """A logo centred on a square ``size`` x ``size`` canvas (RGB, ``bg`` colour), scaled so its
    whole box fits inside a circle of diameter ``safe * size``. Profiles such as Google Business
    Profile ask for a square logo and then show it in a circle; a wide wordmark that fills the square
    would lose its ends."""
    if not 0 < safe <= 1:
        raise ValueError(f"safe must be in (0, 1], got {safe}")
    lg = trim(_open(path))
    k = safe * size / (lg.width ** 2 + lg.height ** 2) ** 0.5
    lg = lg.resize((max(1, round(lg.width * k)), max(1, round(lg.height * k))), Image.LANCZOS)
    out = Image.new("RGB", (size, size), tuple(bg))
    out.paste(lg, ((size - lg.width) // 2, (size - lg.height) // 2), lg)
    return out
