"""Comparison table page drawn with PIL, not rendered by an image model.

Rows of exact numbers (prices, counts, dates) must be character-perfect, and image models are
not reliable at that density. ``render`` lays the table out, searches for the largest font size
at which every cell fits, and leaves the bottom band area empty (no page number, no footer):
those are composited later by ``band`` / ``stamp``.

Spec::

    {"title": str, "columns": [str, ...], "rows": [[cell, ...], ...],
     "marks": {"r,c": "good" | "bad"},       # r = body row index from 0 (header excluded), c = column
     "preset": "isometrik-terang",           # optional: palette defaults come from this style preset
     "palette": {"background": "#hex", ...}, # optional overrides
     # optional page furniture (all omitted = the plain table above):
     "kicker": str, "sub": str,              # eyebrow above the title, grey line under it
     "widths": [0.27, 0.365, 0.365],         # column shares of the table width
     "highlight": 1,                         # column drawn as "ours": glow, teal header, tint, thick frame
     "mark_rule": {"col": 2, "equals": "Tidak ada", "bad": [2], "good": [1]},  # marks from a cell value
     "notes": [str, ...],                    # small grey lines under the table
     "ribbon": str,                          # full-width teal band with one white line at the bottom
     "title_font": "/path/Condensed.ttf"}    # headline face (e.g. the deck's condensed headline font)

:func:`spec_from_md` builds this spec from one ``## NN — ...`` section of a deck.md (Kicker,
Headline, Sub, the first table, ``- `` lines as notes, Pita as ribbon).

Palette keys: background, navy (title, header fill, cell text), teal (title rule), body (grey
text). Cell marks use fixed soft tints, optionally overridden with good_bg / good_fg / bad_bg /
bad_fg: GOOD is a pale green cell with dark green text, BAD a pale red cell with dark red text.
"""
from PIL import Image, ImageDraw, ImageFilter

from . import fonts, house

DEFAULT_PRESET = "isometrik-terang"
GOOD_BG, GOOD_FG = (223, 243, 228), (20, 96, 43)
BAD_BG, BAD_FG = (253, 226, 224), (161, 33, 26)
WHITE, ROW_ALT, LINE = (255, 255, 255), (246, 249, 248), (211, 222, 223)
HL_TINT = (232, 247, 244)  # cells of the highlighted ("ours") column
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
    w = spec.get("widths")
    if w is not None and (len(w) != len(cols) or abs(sum(w) - 1) > 0.01 or min(w) <= 0):
        raise ValueError(f"widths needs {len(cols)} positive shares summing to 1, got {w}")
    hl = spec.get("highlight")
    if hl is not None and not (isinstance(hl, int) and 0 <= hl < len(cols)):
        raise ValueError(f"highlight must be a column index 0..{len(cols) - 1}, got {hl!r}")
    marks = {}
    rule = spec.get("mark_rule")
    if rule:
        for r, row in enumerate(rows):
            if row[rule["col"]] == rule["equals"]:
                for c in rule.get("bad", []):
                    marks[(r, c)] = "bad"
                for c in rule.get("good", []):
                    marks[(r, c)] = "good"
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
    if spec.get("widths"):
        xs = [x0]
        for share in spec["widths"]:
            xs.append(xs[-1] + int((x1 - x0) * share))
        xs[-1] = x1
    else:
        xs = [x0 + (x1 - x0) * i // ncol for i in range(ncol + 1)]
    cws = [xs[i + 1] - xs[i] - 2 * pad for i in range(ncol)]  # each column wraps at its own width

    ft = fonts.load_font(max(8, int(H * 0.05)), spec.get("title_font") or path)
    title_lines = _wrap(spec.get("title", ""), ft, x1 - x0)
    if title_lines is None:
        raise ValueError("title does not fit: a word is wider than the page")
    fk = fonts.load_font(max(8, int(H * 0.021)), path)
    fsub = fonts.load_font(max(8, int(H * 0.021)), path)
    ty0 = int(H * 0.045)
    ky = ty0
    if spec.get("kicker"):
        ty0 += int(fk.size * 1.6)
    tlh = int(ft.size * 1.2)
    sub_y = ty0 + tlh * len(title_lines) + int(H * 0.006)
    top = sub_y + (int(fsub.size * 1.7) if spec.get("sub") else 0) + int(H * 0.03)
    ribbon_h = int(62 * s) if spec.get("ribbon") else 0
    fnote = fonts.load_font(max(8, int(27 * s)), path)
    note_lines = []
    for n in spec.get("notes") or []:
        wrapped = _wrap(n, fnote, x1 - x0)
        if wrapped is None:
            raise ValueError(f"note does not fit: a word is wider than the page: {n!r}")
        note_lines += wrapped
    notes_h = (int(16 * s) + len(note_lines) * int(35 * s)) if note_lines else 0
    limit = (H - ribbon_h - int(12 * s) if ribbon_h else H - int(H * BAND_FRACTION)) - notes_h
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
        cells, ok = {}, all(font.getlength(str(n)) <= cws[c] for c, n in enumerate(spec["columns"]))
        for r, row in enumerate(spec["rows"]):
            for c, text in enumerate(row):
                lines = _wrap(text, font, cws[c])
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
        _raise_unfit(spec, path, smin, cws, avail, vpad)
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
                ty0=ty0, x0=x0, x1=x1, size=size, s=s, fk=fk, ky=ky, fsub=fsub, sub_y=sub_y,
                note_lines=note_lines, fnote=fnote, ribbon_h=ribbon_h, table_bottom=y)


def _raise_unfit(spec, path, smin, cws, avail, vpad):
    """Name the cell that blocks the layout at the minimum font size."""
    font = fonts.load_font(smin, path)
    lh = int(smin * 1.24)
    for c, name in enumerate(spec["columns"]):
        if font.getlength(str(name)) > cws[c]:
            raise ValueError(f"column {c} header {str(name)!r} does not fit: wider than the column at the minimum size ({smin}px)")
    tallest, where = -1, None
    for r, row in enumerate(spec["rows"]):
        for c, text in enumerate(row):
            lines = _wrap(text, font, cws[c])
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
    hl = spec.get("highlight")
    s = L["s"]
    if hl is not None:  # glow behind "our" column, before anything is drawn over it
        gx0, gy0 = boxes[(-1, hl)][:2]
        gx1 = boxes[(-1, hl)][2]
        glow = Image.new("L", (W, H), 0)
        ImageDraw.Draw(glow).rectangle((gx0 - int(12 * s), gy0 - int(12 * s), gx1 + int(12 * s),
                                        L["table_bottom"] + int(12 * s)), fill=230)
        im.paste((95, 205, 194), mask=glow.filter(ImageFilter.GaussianBlur(max(1, int(20 * s)))))
    d = ImageDraw.Draw(im)
    if spec.get("kicker"):
        d.text((L["x0"], L["ky"]), spec["kicker"], font=L["fk"], fill=pal["teal"])
    y = L["ty0"]
    for ln in L["title_lines"]:
        d.text((L["x0"], y), ln, font=L["ft"], fill=pal["navy"])
        y += L["tlh"]
    if spec.get("sub"):
        d.text((L["x0"], L["sub_y"]), spec["sub"], font=L["fsub"], fill=pal["body"])
    else:
        rule_y = L["top"] - int(size[1] * 0.025)
        d.rectangle((L["x0"], rule_y, L["x0"] + int(160 * s), rule_y + max(2, int(6 * s))), fill=pal["teal"])
    bold = fonts.load_font(L["px"], L["path"])
    head_font = bold
    for c, name in enumerate(spec["columns"]):
        x0, y0, x1, y1 = boxes[(-1, c)]
        d.rectangle((x0, y0, x1, y1), fill=pal["teal"] if c == hl else pal["navy"])
        d.text((x0 + L["pad"], (y0 + y1) // 2), str(name), font=head_font, fill=WHITE, anchor="lm")
    for r in range(len(spec["rows"])):
        for c in range(len(spec["columns"])):
            x0, y0, x1, y1 = boxes[(r, c)]
            kind = marks.get((r, c))
            bg = pal["good_bg"] if kind == "good" else pal["bad_bg"] if kind == "bad" else (
                HL_TINT if c == hl else WHITE if r % 2 == 0 else ROW_ALT)
            fg = pal["good_fg"] if kind == "good" else pal["bad_fg"] if kind == "bad" else (pal["navy"] if c == 0 else pal["body"])
            d.rectangle((x0, y0, x1, y1), fill=bg)
            lines = L["cells"][(r, c)]
            ty = y0 + ((y1 - y0) - len(lines) * L["lh"]) // 2
            for ln in lines:
                d.text((x0 + L["pad"], ty), ln, font=bold, fill=fg)
                ty += L["lh"]
            d.line((x0, y1, x1, y1), fill=LINE, width=2)
    if hl is not None:
        x0, y0 = boxes[(-1, hl)][:2]
        d.rectangle((x0, y0, boxes[(-1, hl)][2], L["table_bottom"]), outline=pal["teal"], width=max(2, int(7 * s)))
    ny = L["table_bottom"] + int(16 * s)
    for ln in L["note_lines"]:
        d.text((L["x0"], ny), ln, font=L["fnote"], fill=pal["body"])
        ny += int(35 * s)
    if spec.get("ribbon"):
        rh = L["ribbon_h"]
        d.rectangle((0, H - rh, W, H), fill=pal["teal"])
        d.text((W // 2, H - rh // 2), spec["ribbon"], font=fonts.load_font(max(8, int(30 * s)), L["path"]),
               fill=WHITE, anchor="mm")
    return im


def spec_from_md(md_text, section):
    """Table spec from the ``## <section> — ...`` block of a deck.md: **Kicker**, **Headline**,
    **Sub**, the first markdown table (first row = columns), ``- `` lines as notes, **Pita** as the
    ribbon. HTML comments are ignored. Add ``highlight`` / ``mark_rule`` / ``widths`` yourself."""
    import re
    m = re.search(rf"^## {re.escape(str(section))} — .*?$(.*?)(?=^## |\Z)", md_text, re.M | re.S)
    if not m:
        raise ValueError(f"no '## {section} — ' section in the deck")
    sec = re.sub(r"<!--.*?-->", "", m.group(1), flags=re.S)

    def field(k):
        f = re.search(rf"\*\*{k}\*\* — (.*)", sec)
        return f.group(1).strip() if f else None

    rows = [[c.strip() for c in ln.strip().strip("|").split("|")] for ln in sec.split("\n")
            if ln.startswith("|") and not re.match(r"^\|[\s\-|]+\|$", ln)]
    if not rows:
        raise ValueError(f"section {section} has no table")
    spec = {"title": field("Headline") or "", "columns": rows[0], "rows": rows[1:]}
    for key, k in (("kicker", "Kicker"), ("sub", "Sub"), ("ribbon", "Pita")):
        if field(k):
            spec[key] = field(k)
    notes = [ln[2:].strip() for ln in sec.split("\n") if ln.startswith("- ")]
    if notes:
        spec["notes"] = notes
    return spec
