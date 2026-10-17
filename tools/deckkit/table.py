"""Comparison table page drawn with PIL, not rendered by an image model.

Rows of exact numbers (prices, counts, dates) must be character-perfect, and image models are
not reliable at that density. ``render`` lays the table out, searches for the largest font size
at which every cell fits, and leaves the bottom band area empty (no page number, no footer):
those are composited later by ``band`` / ``stamp``.

Spec::

    {"title": str, "columns": [str, ...], "rows": [[cell, ...], ...],
     "marks": {"r,c": "good" | "bad"},       # r = body row index from 0 (header excluded), c = column
     "preset": "isometrik-terang",           # optional: palette defaults come from this style preset
     "palette": {"background": "#hex", ...}} # optional overrides

Palette keys: background, navy (title, header fill, cell text), teal (title rule), body (grey
text). Cell marks use fixed soft tints, optionally overridden with good_bg / good_fg / bad_bg /
bad_fg: GOOD is a pale green cell with dark green text, BAD a pale red cell with dark red text.
"""
from PIL import Image, ImageDraw

from . import fonts, house

DEFAULT_PRESET = "isometrik-terang"
GOOD_BG, GOOD_FG = (223, 243, 228), (20, 96, 43)
BAD_BG, BAD_FG = (253, 226, 224), (161, 33, 26)
WHITE, ROW_ALT, LINE = (255, 255, 255), (246, 249, 248), (211, 222, 223)
PALETTE_KEYS = ("background", "navy", "teal", "body", "good_bg", "good_fg", "bad_bg", "bad_fg")
MARKS = ("good", "bad")
BAND_FRACTION = 0.065  # bottom share of the page left empty for the footer band
REF_W = 2752  # design width; every length below scales with size[0] / REF_W


def _hex(value, name):
    s = str(value).lstrip("#")
    if len(s) != 6:
        raise ValueError(f"palette {name!r}: need a #rrggbb colour, got {value!r}")
    try:
        return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        raise ValueError(f"palette {name!r}: need a #rrggbb colour, got {value!r}") from None


def _colours(spec):
    pal = dict(house.load_preset(spec.get("preset") or DEFAULT_PRESET).get("palette", {}))
    over = spec.get("palette") or {}
    bad = sorted(set(over) - set(PALETTE_KEYS))
    if bad:
        raise ValueError(f"unknown palette key(s) {bad}; allowed: {', '.join(PALETTE_KEYS)}")
    pal.update(over)
    out = {}
    for key in ("background", "navy", "teal", "body"):
        if key not in pal:
            raise ValueError(f"palette missing {key!r}")
        out[key] = _hex(pal[key], key)
    for key, default in (("good_bg", GOOD_BG), ("good_fg", GOOD_FG), ("bad_bg", BAD_BG), ("bad_fg", BAD_FG)):
        out[key] = _hex(pal[key], key) if key in pal else default
    return out


def _validate(spec):
    cols, rows = spec.get("columns"), spec.get("rows")
    if not cols or not rows:
        raise ValueError("spec needs non-empty 'columns' and 'rows'")
    for r, row in enumerate(rows):
        if len(row) != len(cols):
            raise ValueError(f"row {r} has {len(row)} cells, expected {len(cols)}")
    marks = {}
    for key, kind in (spec.get("marks") or {}).items():
        try:
            r, c = (int(v) for v in str(key).split(","))
        except ValueError:
            raise ValueError(f"mark key {key!r}: need 'row,col' like '1,2'") from None
        if not (0 <= r < len(rows) and 0 <= c < len(cols)):
            raise ValueError(f"mark {key!r} is outside the table ({len(rows)} rows x {len(cols)} columns)")
        if kind not in MARKS:
            raise ValueError(f"mark {key!r}: value must be one of {MARKS}, got {kind!r}")
        marks[(r, c)] = kind
    return marks


def _wrap(text, font, width):
    """Lines of ``text`` within ``width``; None when a single word is wider than the cell."""
    lines, cur = [], ""
    for w in str(text).split():
        t = f"{cur} {w}".strip()
        if font.getlength(t) <= width or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return None if any(font.getlength(ln) > width for ln in lines) else lines


def _layout(spec, size, font_path):
    marks = _validate(spec)
    pal = _colours(spec)
    W, H = size
    s = W / REF_W
    path = fonts.find_font(font_path)
    x0, x1 = int(116 * s), W - int(116 * s)
    pad, vpad = max(2, int(18 * s)), max(1, int(14 * s))
    ncol = len(spec["columns"])
    xs = [x0 + (x1 - x0) * i // ncol for i in range(ncol + 1)]
    cw = xs[1] - xs[0] - 2 * pad

    ft = fonts.load_font(max(8, int(H * 0.05)), path)
    title_lines = _wrap(spec.get("title", ""), ft, x1 - x0)
    if title_lines is None:
        raise ValueError("title does not fit: a word is wider than the page")
    ty0 = int(H * 0.045)
    tlh = int(ft.size * 1.2)
    top = ty0 + tlh * len(title_lines) + int(H * 0.04)
    limit = H - int(H * BAND_FRACTION)
    avail = limit - top
    nrows = len(spec["rows"])
    base = avail // (nrows + 1)

    smin = max(8, int(18 * s))
    # Body stays below the 5% title so the title still reads as the headline, and short cells stay on one line.
    smax = max(smin, min(int(base * 0.42), int(H * 0.034)))
    plan = None
    for px in range(smax, smin - 1, -1):
        font = fonts.load_font(px, path)
        lh = int(px * 1.24)
        cells, ok = {}, all(font.getlength(str(n)) <= cw for n in spec["columns"])
        for r, row in enumerate(spec["rows"]):
            for c, text in enumerate(row):
                lines = _wrap(text, font, cw)
                if lines is None:
                    ok = False
                    break
                cells[(r, c)] = lines
            if not ok:
                break
        if not ok:
            continue
        need = [max(len(cells[(r, c)]) for c in range(ncol)) * lh + 2 * vpad for r in range(nrows)]
        head_need = int(px * 2.0)
        if max(need) <= base and head_need <= base:
            heights, head_h = [base] * nrows, base
        elif head_need + sum(need) <= avail:
            extra = (avail - head_need - sum(need)) // (nrows + 1)  # spread leftover so the table still reaches the band
            heights, head_h = [n + extra for n in need], head_need + extra
        else:
            continue
        plan = (px, font, lh, head_h, cells, heights)
        break
    if plan is None:
        _raise_unfit(spec, path, smin, cw, avail, vpad)
    px, font, lh, head_h, cells, heights = plan
    boxes, y = {}, top + head_h
    for c in range(ncol):
        boxes[(-1, c)] = (xs[c], top, xs[c + 1], top + head_h)
    for r, h in enumerate(heights):
        for c in range(ncol):
            boxes[(r, c)] = (xs[c], y, xs[c + 1], y + h)
        y += h
    return dict(pal=pal, marks=marks, path=path, px=px, lh=lh, pad=pad, xs=xs, top=top, head_h=head_h,
                cells=cells, heights=heights, boxes=boxes, title_lines=title_lines, ft=ft, tlh=tlh,
                ty0=ty0, x0=x0, x1=x1, size=size, s=s)


def _raise_unfit(spec, path, smin, cw, avail, vpad):
    """Name the cell that blocks the layout at the minimum font size."""
    font = fonts.load_font(smin, path)
    lh = int(smin * 1.24)
    for c, name in enumerate(spec["columns"]):
        if font.getlength(str(name)) > cw:
            raise ValueError(f"column {c} header {str(name)!r} does not fit: wider than the column at the minimum size ({smin}px)")
    tallest, where = -1, None
    for r, row in enumerate(spec["rows"]):
        for c, text in enumerate(row):
            lines = _wrap(text, font, cw)
            if lines is None:
                raise ValueError(f"cell {r},{c} does not fit: a word is wider than the column at the minimum size ({smin}px)")
            h = len(lines) * lh + 2 * vpad
            if h > avail:
                raise ValueError(f"cell {r},{c} does not fit: {len(lines)} lines is taller than the page at the minimum size ({smin}px)")
            if h > tallest:
                tallest, where = h, (r, c)
    r, c = where
    raise ValueError(f"cell {r},{c} does not fit: the table is too tall at the minimum size ({smin}px); shorten the text or drop rows")


def cell_boxes(spec, size=(2752, 1536), font_path=None):
    """{(row, col): (x0, y0, x1, y1)} for every cell; header cells use row -1."""
    return _layout(spec, size, font_path)["boxes"]


def render(spec, size=(2752, 1536), font_path=None):
    """RGB image of exactly ``size`` with the table drawn; ValueError names a cell that cannot fit."""
    L = _layout(spec, size, font_path)
    pal, marks, boxes = L["pal"], L["marks"], L["boxes"]
    W, H = size
    im = Image.new("RGB", (W, H), pal["background"])
    d = ImageDraw.Draw(im)
    y = L["ty0"]
    for ln in L["title_lines"]:
        d.text((L["x0"], y), ln, font=L["ft"], fill=pal["navy"])
        y += L["tlh"]
    rule_y = L["top"] - int(size[1] * 0.025)
    d.rectangle((L["x0"], rule_y, L["x0"] + int(160 * L["s"]), rule_y + max(2, int(6 * L["s"]))), fill=pal["teal"])
    bold = fonts.load_font(L["px"], L["path"])
    head_font = bold
    for c, name in enumerate(spec["columns"]):
        x0, y0, x1, y1 = boxes[(-1, c)]
        d.rectangle((x0, y0, x1, y1), fill=pal["navy"])
        d.text((x0 + L["pad"], (y0 + y1) // 2), str(name), font=head_font, fill=WHITE, anchor="lm")
    for r in range(len(spec["rows"])):
        for c in range(len(spec["columns"])):
            x0, y0, x1, y1 = boxes[(r, c)]
            kind = marks.get((r, c))
            bg = pal["good_bg"] if kind == "good" else pal["bad_bg"] if kind == "bad" else (WHITE if r % 2 == 0 else ROW_ALT)
            fg = pal["good_fg"] if kind == "good" else pal["bad_fg"] if kind == "bad" else (pal["navy"] if c == 0 else pal["body"])
            d.rectangle((x0, y0, x1, y1), fill=bg)
            lines = L["cells"][(r, c)]
            ty = y0 + ((y1 - y0) - len(lines) * L["lh"]) // 2
            for ln in lines:
                d.text((x0 + L["pad"], ty), ln, font=bold, fill=fg)
                ty += L["lh"]
            d.line((x0, y1, x1, y1), fill=LINE, width=2)
    return im
