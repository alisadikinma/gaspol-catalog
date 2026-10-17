"""Page numbers (and an optional wordmark) stamped AFTER rendering.

Keep numerals out of image prompts: inserting or dropping a page used to mean re-rendering every
page after it. The render stays anonymous, the number comes from the FILENAME (``07.png`` -> 7),
so renumbering is a rename plus a re-run.
"""
import os
import re

from PIL import Image, ImageDraw

from .fonts import load_font

LAYOUT = dict(probe_y=0.972, probe_x=0.05, num_x=0.963, num_y=0.9615, num_size=0.030,
              clear_right=0.925, clear_left=0.16, band_top=0.945, wm_left=0.035, wm_height=0.032)


def band_colour(im, layout=LAYOUT):
    """Sample the footer band instead of hard-coding its colour, so a palette change still works."""
    w, h = im.size
    return im.getpixel((int(w * layout["probe_x"]), int(h * layout["probe_y"])))


def white_wordmark(path, target_h):
    """Recolour a dark-on-transparent wordmark white and size it to ``target_h``."""
    wm = Image.open(path).convert("RGBA")
    wm = wm.resize((max(1, int(wm.width * target_h / wm.height)), max(1, int(target_h))), Image.LANCZOS)
    r, g, b, a = wm.split()
    white = Image.new("L", wm.size, 255)
    return Image.merge("RGBA", (white, white, white, a))


def stamp(src, dst, number, wordmark=None, layout=LAYOUT, font_path=None):
    im = Image.open(src).convert("RGB")
    w, h = im.size
    fill = band_colour(im, layout)
    d = ImageDraw.Draw(im)
    # wipe both ends of the band so a previously baked-in numeral cannot show through
    d.rectangle((int(w * layout["clear_right"]), int(h * layout["band_top"]), w, h), fill=fill)
    d.rectangle((0, int(h * layout["band_top"]), int(w * layout["clear_left"]), h), fill=fill)
    d.text((int(w * layout["num_x"]), int(h * layout["num_y"])), str(number),
           font=load_font(max(14, int(h * layout["num_size"])), font_path), fill=(255, 255, 255), anchor="mm")
    if wordmark is not None:
        im.paste(wordmark, (int(w * layout["wm_left"]), int(h * layout["num_y"] - wordmark.height / 2)), wordmark)
    im.save(dst)


def stamp_dir(src, dst, wordmark_path=None, pattern=r"\d{2}\.png", layout=LAYOUT, font_path=None):
    names = sorted(f for f in os.listdir(src) if re.fullmatch(pattern, f))
    if not names:
        raise FileNotFoundError(f"no pages matching {pattern!r} in {src}")
    os.makedirs(dst, exist_ok=True)
    wm = None
    if wordmark_path:
        probe = Image.open(os.path.join(src, names[0]))
        wm = white_wordmark(wordmark_path, int(probe.height * layout["wm_height"]))
    for n in names:
        stamp(os.path.join(src, n), os.path.join(dst, n), int(re.match(r"\d+", n).group(0)), wm, layout, font_path)
    return names
