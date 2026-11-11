"""Composite what the image model must not draw onto a rendered page, from a JSON plan.

The prompt asks the model for flat magenta (#ff00ff) slots; this module finds them, checks their
count, and runs the plan's operations in order: real logos (flat, perspective, or only over the
pixels that were magenta), round photos, sticker images, flags, cards, text and rating stars.
Whatever magenta is left at the end is painted ``leftover`` and counted, so a slot the plan forgot
is visible in the report instead of on the slide.

Plan (one page)::

    {"src": "renders/03-r29.png", "dst": "renders/03-r29-tempel.png",
     "expect_slots": 3,                      # or {"min": 1}; omitted = not checked
     "leftover": [250, 251, 251],
     "ops": [{"op": "logo", "slot": {"sort": "y", "index": -1}, "file": "logo.png", "mode": "flat"},
             ...]}

Slot selector: ``{"sort": "x"|"y"|"xy"|"area", "index": i, "where": {"cx_min", "cx_max",
"cy_min", "cy_max"}, "from": a, "to": b}`` — filter by centre, sort ascending (``area`` sorts
largest first), then take ``index`` (negative counts from the end) or the slice ``from``..``to``;
``then`` re-sorts the slice before ``index`` (the two lowest slots, then left to right).
``"slot": "all"`` repeats the op for every slot left after ``where``. Each slot's ground colour
(the pixel just left of it) is read before the first op runs, so a logo pasted into one slot
never becomes the "ground" of the slot beside it. Paths in a plan are relative to the plan file. Operations are listed in
:data:`OPS`; each one's keys are documented on its function.
"""
import math
import os
from collections import deque

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

K = 4  # slot search runs on the page shrunk K times
LEFTOVER = (250, 251, 251)


def is_magenta(px):
    r, g, b = px[:3]
    return r > 170 and b > 150 and g < 130 and r - g > 80 and b - g > 60


def find_slots(im, min_px=60):
    """Magenta components as dicts: area (shrunk px), box, cx, cy, quad (TL, TR, BR, BL)."""
    small = im.convert("RGB").resize((im.width // K, im.height // K), Image.BILINEAR)
    w, h = small.size
    px = small.load()
    m = [[is_magenta(px[x, y]) for x in range(w)] for y in range(h)]
    out = []
    for y in range(h):
        for x in range(w):
            if not m[y][x]:
                continue
            m[y][x] = False
            q, pts = deque([(x, y)]), []
            while q:
                a, b = q.popleft()
                pts.append((a, b))
                for c, d in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
                    if 0 <= c < w and 0 <= d < h and m[d][c]:
                        m[d][c] = False
                        q.append((c, d))
            if len(pts) < min_px:
                continue
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            corners = [min(pts, key=lambda p: p[0] + p[1]), max(pts, key=lambda p: p[0] - p[1]),
                       max(pts, key=lambda p: p[0] + p[1]), min(pts, key=lambda p: p[0] - p[1])]
            out.append(dict(area=len(pts), box=(min(xs) * K, min(ys) * K, (max(xs) + 1) * K, (max(ys) + 1) * K),
                            cx=sum(xs) / len(xs) * K, cy=sum(ys) / len(ys) * K,
                            quad=[(p[0] * K, p[1] * K) for p in corners]))
    return out


def select(slots, sel):
    """Slots chosen by a selector (see module doc). Returns a list."""
    if isinstance(sel, int):
        sel = {"sort": "x", "index": sel}
    if sel == "all":
        sel = {"index": "all"}
    w = sel.get("where", {})
    pool = [s for s in slots
            if w.get("cx_min", -1e9) <= s["cx"] < w.get("cx_max", 1e9)
            and w.get("cy_min", -1e9) <= s["cy"] < w.get("cy_max", 1e9)]
    key = sel.get("sort", "x")
    keys = {"x": lambda s: s["cx"], "y": lambda s: s["cy"], "xy": lambda s: s["cx"] + s["cy"],
            "area": lambda s: -s["area"]}
    if key not in keys:
        raise ValueError(f"slot sort must be one of {sorted(keys)}, got {key!r}")
    pool.sort(key=keys[key])
    if "from" in sel or "to" in sel:
        pool = pool[sel.get("from", 0):sel.get("to", len(pool))]
        if "then" not in sel:
            return pool
    if "then" in sel:  # re-sort the slice, e.g. the two lowest slots, then left to right
        if sel["then"] not in keys:
            raise ValueError(f"slot then must be one of {sorted(keys)}, got {sel['then']!r}")
        pool.sort(key=keys[sel["then"]])
    idx = sel.get("index", 0)
    if idx == "all":
        return pool
    if not pool or not -len(pool) <= idx < len(pool):
        raise ValueError(f"slot selector {sel} matches {len(pool)} slot(s); index {idx} is out of range")
    return [pool[idx]]


def trim(src, thr=0):
    """Logo cropped to its content: transparent margin and white margin removed.

    ``src`` is a path or a PIL image. ``thr`` (0-255) is how far a pixel may differ from white and
    still count as margin; 0 = exactly white only, ~18 also drops JPEG-ish near-white edges."""
    im = (src if isinstance(src, Image.Image) else Image.open(src)).convert("RGBA")
    im = im.crop(im.getbbox())
    diff = ImageChops.difference(im.convert("RGB"), Image.new("RGB", im.size, (255, 255, 255)))
    bb = diff.convert("L").point(lambda v: 255 if v > thr else 0).getbbox() if thr else diff.getbbox()
    return im.crop(bb) if bb else im


def neighbour(im, box):
    """Ground colour just left of ``box``, at its middle height."""
    x0, y0, x1, y1 = box
    return im.getpixel((max(0, x0 - 10), min(im.height - 1, (y0 + y1) // 2)))


def _perspective_coeffs(dst, src):
    a = []
    for (x, y), (u, v) in zip(dst, src):
        a.append([x, y, 1, 0, 0, 0, -u * x, -u * y, u])
        a.append([0, 0, 0, x, y, 1, -v * x, -v * y, v])
    n = 8
    for i in range(n):
        p = max(range(i, n), key=lambda r: abs(a[r][i]))
        a[i], a[p] = a[p], a[i]
        for r in range(n):
            if r != i:
                f = a[r][i] / a[i][i]
                a[r] = [x - f * y for x, y in zip(a[r], a[i])]
    return [a[i][8] / a[i][i] for i in range(n)]


def logo_flat(im, slot, file, fill="neighbour", fit=0.86):
    """Whole logo centred in the slot box; the box is first painted ``fill`` (RGB, or
    "neighbour" = the ground beside the slot)."""
    x0, y0, x1, y1 = slot["box"]
    colour = slot.get("ground") or neighbour(im, slot["box"]) if fill == "neighbour" else tuple(fill)
    ImageDraw.Draw(im).rectangle((x0 - 5, y0 - 5, x1 + 5, y1 + 5), fill=colour)
    lg = trim(file)
    k = min((x1 - x0) * fit / lg.width, (y1 - y0) * fit / lg.height)
    lg = lg.resize((max(1, int(lg.width * k)), max(1, int(lg.height * k))), Image.LANCZOS)
    im.alpha_composite(lg, ((x0 + x1 - lg.width) // 2, (y0 + y1 - lg.height) // 2))


def logo_quad(im, slot, file, plate=(250, 251, 251), grow=(1.06, 1.10), fit=0.80):
    """Logo warped onto the slot's quad (a tilted screen, a truck side), keeping the logo's aspect.
    ``plate`` (RGB or null) is painted over the quad grown by ``grow`` first."""
    q = slot["quad"]
    cx, cy = sum(p[0] for p in q) / 4, sum(p[1] for p in q) / 4
    if plate:
        outer = [(cx + (x - cx) * grow[0], cy + (y - cy) * grow[1]) for x, y in q]
        ImageDraw.Draw(im).polygon(outer, fill=tuple(plate))
    lg = trim(file)
    lg = lg.resize((lg.width * 4, lg.height * 4), Image.LANCZOS)
    wq = math.dist(q[0], q[1])
    hq = math.dist(q[0], q[3])
    fy = min(fit, fit * wq * lg.height / lg.width / max(hq, 1))
    inner = [(cx + (x - cx) * fit, cy + (y - cy) * fy) for x, y in q]
    w, h = lg.size
    layer = lg.transform(im.size, Image.PERSPECTIVE,
                         _perspective_coeffs(inner, [(0, 0), (w, 0), (w, h), (0, h)]), Image.BICUBIC)
    im.alpha_composite(layer)


def whiten(im, colour=LEFTOVER, box=None, pinkish=True, dark_fringe=False):
    """Paint magenta (and, with ``pinkish``, its anti-aliased pink fringe) ``colour``, inside
    ``box`` or on the whole page.

    ``dark_fringe`` also paints the dark purple edge magenta leaves on a dark ground, such as a
    phone bezel (about 60,5,75). It matches purple on any page, so give it a ``box``."""
    px = im.load()
    x0, y0, x1, y1 = box or (0, 0, im.width, im.height)
    for y in range(max(0, y0), min(im.height, y1)):
        for x in range(max(0, x0), min(im.width, x1)):
            r, g, b = px[x, y][:3]
            if is_magenta(px[x, y]) or (pinkish and r > 150 and b > 140 and r - g > 35 and b - g > 30
                                        and abs(r - b) < 70) or (
                    dark_fringe and r - g > 30 and b - g > 30 and abs(r - b) < 70):
                px[x, y] = tuple(colour) + (255,)


def logo_pixel(im, slots, file, colour=LEFTOVER, shift=0.0, fit=(0.72, 0.6)):
    """For slots partly covered by a figure: magenta whitened per pixel (the figure stays in
    front), then the logo flat in the largest of ``slots``, nudged right by ``shift`` x its width."""
    whiten(im, colour)
    s = max(slots, key=lambda s: s["area"])
    x0, y0, x1, y1 = s["box"]
    lg = trim(file)
    k = min((x1 - x0) * fit[0] / lg.width, (y1 - y0) * fit[1] / lg.height)
    lg = lg.resize((int(lg.width * k), int(lg.height * k)), Image.LANCZOS)
    im.alpha_composite(lg, (int((x0 + x1) / 2 - lg.width / 2 + (x1 - x0) * shift), int((y0 + y1) / 2 - lg.height / 2)))


def photo_round(im, slot, file, crop=None, ring=(35, 133, 127), ring_width=5):
    """Real photo, cropped to ``crop`` (x0, y0, x1, y1 in the photo), in a circle over the slot."""
    x0, y0, x1, y1 = slot["box"]
    d = max(x1 - x0, y1 - y0) + 10
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    f = Image.open(file).convert("RGB")
    f = (f.crop(tuple(crop)) if crop else f).resize((d, d), Image.LANCZOS)
    mask = Image.new("L", (d * 4, d * 4), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, d * 4 - 1, d * 4 - 1), fill=255)
    im.paste(f, (cx - d // 2, cy - d // 2), mask.resize((d, d), Image.LANCZOS))
    if ring:
        ImageDraw.Draw(im).ellipse((cx - d // 2, cy - d // 2, cx + d // 2, cy + d // 2), outline=tuple(ring),
                                   width=ring_width)


def image(im, file, xy, height=None, width=None, shadow=False, trim_margin=False):
    """A sticker image (badge, seal, a logo at a fixed spot) pasted with its top-left at ``xy``,
    scaled to ``height`` or ``width``; ``shadow`` adds a soft drop shadow; ``trim_margin`` crops the
    file's transparent and white margin first (as logos are elsewhere)."""
    lg = trim(file) if trim_margin else Image.open(file).convert("RGBA")
    if height:
        lg = lg.resize((max(1, int(lg.width * height / lg.height)), int(height)), Image.LANCZOS)
    elif width:
        lg = lg.resize((int(width), max(1, int(lg.height * width / lg.width))), Image.LANCZOS)
    if shadow:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        sh.paste((20, 30, 50, 90), (xy[0] + 4, xy[1] + 8), lg.getchannel("A"))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
    im.alpha_composite(lg, tuple(xy))


def logo_box(im, box, file, fit=(0.86, 0.86), plate=None, radius=6, outline=(150, 158, 166)):
    """Logo centred in a fixed ``box`` (x0, y0, x1, y1); ``plate`` RGB draws a rounded panel
    (with ``outline``, null for none) behind it first."""
    if plate:
        ImageDraw.Draw(im).rounded_rectangle(tuple(box), radius=radius, fill=tuple(plate),
                                             outline=tuple(outline) if outline else None, width=2)
    x0, y0, x1, y1 = box
    lg = trim(file)
    k = min((x1 - x0) * fit[0] / lg.width, (y1 - y0) * fit[1] / lg.height)
    lg = lg.resize((max(1, int(lg.width * k)), max(1, int(lg.height * k))), Image.LANCZOS)
    im.alpha_composite(lg, ((x0 + x1 - lg.width) // 2, (y0 + y1 - lg.height) // 2))


def _flag_image(country, w, q=8):
    h = w * 2 // 3
    W, H = w * q, h * q
    f = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(f)
    tricolour = {"de": ("h", ((0, 0, 0), (221, 0, 0), (255, 206, 0))),
                 "fr": ("v", ((0, 38, 153), (255, 255, 255), (239, 65, 53))),
                 "it": ("v", ((0, 146, 70), (255, 255, 255), (206, 43, 55))),
                 "nl": ("h", ((174, 28, 40), (255, 255, 255), (33, 70, 139)))}
    if country in tricolour:
        way, cols = tricolour[country]
        for i, c in enumerate(cols):
            d.rectangle((0, H * i // 3, W, H * (i + 1) // 3) if way == "h" else (W * i // 3, 0, W * (i + 1) // 3, H),
                        fill=c)
    elif country == "id":
        d.rectangle((0, 0, W, H // 2), fill=(206, 17, 38))
    elif country == "sg":
        red = (237, 41, 57)
        d.rectangle((0, 0, W, H // 2), fill=red)
        r, bx, by = H * 0.17, W * 0.2, H * 0.25
        d.ellipse((bx - r, by - r, bx + r, by + r), fill=(255, 255, 255))
        d.ellipse((bx - r + r * 0.45, by - r, bx + r + r * 0.45, by + r), fill=red)
        sx, sy, sr = bx + r * 1.15, by, r * 0.55
        for i in range(5):
            a = math.radians(-90 + 72 * i)
            ox, oy, b = sx + sr * math.cos(a), sy + sr * math.sin(a), r * 0.26
            d.polygon([(ox + (b if j % 2 == 0 else b * 0.4) * math.cos(math.radians(-90 + 36 * j)),
                        oy + (b if j % 2 == 0 else b * 0.4) * math.sin(math.radians(-90 + 36 * j))) for j in range(10)],
                      fill=(255, 255, 255))
    else:
        raise ValueError(f"flag: no built-in drawing for {country!r} (built in: de fr it nl id sg); use op image")
    return f.resize((w, h), Image.LANCZOS)


def flag(im, country, center, width=54):
    """Small white-edged flag centred at ``center``, drawn 8x and shrunk (built in: de fr it nl id
    sg; any other flag: op ``image`` with a file)."""
    f = _flag_image(country, int(width))
    w, h = f.size
    x, y = int(center[0] - w / 2), int(center[1] - h / 2)
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((x - 1, y + 2, x + w + 5, y + h + 8), radius=5, fill=(20, 30, 50, 90))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(4)))
    ImageDraw.Draw(im).rounded_rectangle((x - 3, y - 3, x + w + 3, y + h + 3), radius=5, fill=(255, 255, 255))
    im.paste(f, (x, y))


def card(im, box, radius=26, fill=(255, 255, 255), outline=(214, 222, 228), shadow=True):
    """Rounded card with an optional soft shadow."""
    x0, y0, x1, y1 = box
    if shadow:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((x0 + 4, y0 + 8, x1 + 4, y1 + 8), radius=radius, fill=(20, 33, 58, 46))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    ImageDraw.Draw(im).rounded_rectangle(tuple(box), radius=radius, fill=tuple(fill),
                                         outline=tuple(outline) if outline else None, width=2)


def text(im, xy, text, font, size, fill=(24, 38, 66), anchor="la", index=0, rect=None, rect_fill=None):
    """One line of text; ``rect`` wipes a box first with ``rect_fill``: RGB, "neighbour" (left of the
    box), or ``{"at": [x, y]}`` (the colour of that pixel)."""
    d = ImageDraw.Draw(im)
    if rect:
        if isinstance(rect_fill, dict):
            colour = im.getpixel(tuple(rect_fill["at"]))
        else:
            colour = neighbour(im, rect) if rect_fill in (None, "neighbour") else tuple(rect_fill)
        d.rectangle(tuple(rect), fill=colour)
    d.text(tuple(xy), text, font=ImageFont.truetype(font, int(size), index=index), fill=tuple(fill), anchor=anchor)


def stars(im, center, count=5, r=21, gap=52, fill=(251, 188, 4)):
    """A row of filled five-point stars, the first centred at ``center``."""
    d = ImageDraw.Draw(im)
    cx0, cy = center
    for i in range(count):
        cx = cx0 + i * gap
        d.polygon([(cx + (r if j % 2 == 0 else r * 0.42) * math.cos(-math.pi / 2 + j * math.pi / 5),
                    cy + (r if j % 2 == 0 else r * 0.42) * math.sin(-math.pi / 2 + j * math.pi / 5)) for j in range(10)],
                  fill=tuple(fill))


def logo_slanted(im, slot, file, tint=None, flag_after=None, widen=1.12, nudge=-4, clean=None):
    """Logo laid along a slanted panel (a truck side seen at an angle). The slot's top and bottom
    edges are measured per pixel column, the slot is covered with the panel's own colour (sampled
    left of it), and the logo is warped along that slope, drawn 4x then shrunk. ``tint`` (RGB)
    turns the logo into one colour from its darkness (drops a coloured logo ground);
    ``flag_after`` appends a built-in flag; ``clean`` (RGB min/max box) repaints stray fringe
    pixels of that colour range near the slot with the panel colour."""
    px = im.load()
    x0, y0, x1, y1 = slot["box"]
    col = {}
    W, H = im.size
    for x in range(max(0, x0 - 10), min(W, x1 + 10)):
        ys = [y for y in range(max(0, y0 - 30), min(H, y1 + 30)) if is_magenta(px[x, y])]
        if len(ys) > 8:
            col[x] = (min(ys), max(ys))
    xs = sorted(col)
    if len(xs) < 6:
        raise ValueError("logo_slanted: slot too small to measure its slope")
    xa, xb = xs[0], xs[-1]
    ta, tb = xs[len(xs) // 6], xs[-len(xs) // 6]
    m = ((col[tb][0] - col[ta][0]) + (col[tb][1] - col[ta][1])) / 2 / (tb - ta)
    top = lambda x: col[ta][0] + m * (x - ta)
    bot = lambda x: col[ta][1] + m * (x - ta)
    if xa < 12:
        raise ValueError("logo_slanted: no panel left of the slot to sample its colour")
    sample = sorted(px[xa - 12, y][:3] for y in range(max(0, int(top(xa)) + 6), min(H, int(bot(xa)) - 4), 2))
    panel = sample[len(sample) // 2] + (255,)
    ImageDraw.Draw(im).polygon([(xa - 2, top(xa) - 2), (xb + 2, top(xb) - 2), (xb + 2, bot(xb) + 2),
                                (xa - 2, bot(xa) + 2)], fill=panel)
    if clean:
        lo, hi = clean
        px = im.load()
        for y in range(max(0, y0 - 34), min(H, y1 + 34)):
            for x in range(max(0, xa - 8), min(W, xb + 9)):
                p = px[x, y]
                if all(lo[i] <= p[i] <= hi[i] for i in range(3)) or is_magenta(p):
                    px[x, y] = panel
    lg = Image.open(file).convert("RGBA")
    if tint:
        a = lg.getchannel("G").point(lambda g: max(0, min(255, int((190 - g) * 255 / 170))))
        one = Image.new("RGBA", lg.size, tuple(tint) + (255,))
        one.putalpha(a)
        lg = one.crop(a.getbbox())
    else:
        lg = lg.crop(lg.getbbox())
    if flag_after:
        fh = lg.height
        t = max(3, fh // 12)  # white edge, as a printed flag decal has
        fl = Image.new("RGBA", (int(fh * 1.5), fh), (255, 255, 255, 255))
        inner = _flag_image(flag_after, fl.width - 2 * t).resize((fl.width - 2 * t, fh - 2 * t), Image.LANCZOS)
        fl.paste(inner, (t, t))
        both = Image.new("RGBA", (lg.width + fh // 3 + fl.width, fh), (0, 0, 0, 0))
        both.paste(lg, (0, 0))
        both.paste(fl, (lg.width + fh // 3, 0))
        lg = both
    width = (xb - xa) * widen
    height = width * lg.height / lg.width
    cx = (xa + xb) / 2 + nudge
    cy = (top(cx) + bot(cx)) / 2
    left, right = cx - width / 2, cx + width / 2
    dst = [(left, cy + m * (left - cx) - height / 2), (right, cy + m * (right - cx) - height / 2),
           (right, cy + m * (right - cx) + height / 2), (left, cy + m * (left - cx) + height / 2)]
    s, ox, oy = 4, int(left) - 10, int(min(p[1] for p in dst)) - 10
    rw, rh = int(width) + 20, int(max(p[1] for p in dst)) - oy + 10
    w, h = lg.size
    big = lg.transform((rw * s, rh * s), Image.PERSPECTIVE,
                       _perspective_coeffs([((x - ox) * s, (y - oy) * s) for x, y in dst],
                                           [(0, 0), (w, 0), (w, h), (0, h)]), Image.BICUBIC)
    im.alpha_composite(big.resize((rw, rh), Image.LANCZOS), (ox, oy))


OPS = ("logo", "photo", "image", "logo_box", "flag", "card", "text", "stars", "whiten", "logo_slanted")


def _path(base, p):
    return p if os.path.isabs(p) else os.path.join(base, p)


def run(plan, base_dir="."):
    """Apply one page plan; returns ``(dst_path, slot_count, leftover_pixels)``."""
    for k in ("src", "dst", "ops"):
        if k not in plan:
            raise ValueError(f"plan missing {k!r}")
    src = _path(base_dir, plan["src"])
    im = Image.open(src).convert("RGBA")
    slots = find_slots(im)
    for s in slots:
        s["ground"] = neighbour(im, s["box"])
    exp = plan.get("expect_slots")
    if exp is not None:
        lo, hi = (exp.get("min", 0), exp.get("max", 10 ** 6)) if isinstance(exp, dict) else (exp, exp)
        if not lo <= len(slots) <= hi:
            raise ValueError(f"{plan['src']}: found {len(slots)} magenta slot(s), plan expects {exp}: "
                             f"{[s['box'] for s in slots]}")
    leftover = tuple(plan.get("leftover", LEFTOVER))
    for i, op in enumerate(plan["ops"]):
        kind = op.get("op")
        if kind not in OPS:
            raise ValueError(f"op {i}: unknown op {kind!r}; known: {', '.join(OPS)}")
        o = {k: v for k, v in op.items() if k not in ("op", "slot", "note")}
        for k in ("file", "font"):
            if k in o:
                o[k] = _path(base_dir, o[k])
        if kind == "logo":
            mode = o.pop("mode", "flat")
            if mode == "quad" and "quad" in op and "slot" not in op:
                o.pop("quad")
                logo_quad(im, {"quad": [tuple(p) for p in op["quad"]]}, **o)
                continue
            chosen = select(slots, op.get("slot", 0))
            if mode == "pixel":
                logo_pixel(im, chosen, colour=leftover, **o)
                continue
            for s in chosen:
                if mode == "flat":
                    logo_flat(im, s, **o)
                elif mode == "quad":
                    if "quad" in op:
                        s = dict(s, quad=[tuple(p) for p in op["quad"]])
                        o.pop("quad", None)
                    logo_quad(im, s, **o)
                else:
                    raise ValueError(f"op {i}: logo mode must be flat, quad or pixel, got {mode!r}")
        elif kind == "photo":
            for s in select(slots, op.get("slot", 0)):
                photo_round(im, s, **o)
        elif kind == "logo_slanted":
            for s in select(slots, op.get("slot", 0)):
                logo_slanted(im, s, **o)
        elif kind == "whiten":
            if "slot" in op:
                for s in select(slots, op["slot"]):
                    x0, y0, x1, y1 = s["box"]
                    whiten(im, o.get("colour", (252, 252, 252)), (x0 - 6, y0 - 6, x1 + 6, y1 + 6), pinkish=False)
            else:
                whiten(im, o.get("colour", leftover), o.get("box"), o.get("pinkish", True),
                       o.get("dark_fringe", False))
        else:
            {"image": image, "logo_box": logo_box, "flag": flag, "card": card, "text": text,
             "stars": stars}[kind](im, **o)
    px = im.load()
    left = 0
    for y in range(im.height):
        for x in range(im.width):
            if is_magenta(px[x, y]):
                px[x, y] = leftover + (255,)
                left += 1
    dst = _path(base_dir, plan["dst"])
    im.convert("RGB").save(dst)
    return dst, len(slots), left
