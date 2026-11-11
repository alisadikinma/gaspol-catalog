"""Re-pack a PDF letter onto fewer pages, line by line, with page numbers in the footer.

A Word export that spills three lines onto an extra page cannot be reflowed without the
source document. This cuts each page into rows (text lines, plus any image such as a scanned
signature together with the lines it overlaps), never splitting a row, and stacks the rows onto
``pages`` output pages at one common scale — the largest that fits, never above 1. Text stays
selectable: every row is copied from a redacted copy of its source page, so no hidden text from
the rest of that page travels along (which would also fool ``deckkit sign`` anchors).

Plan file::

    {"src": "letter.pdf", "dst": "letter-3.pdf", "pages": 3,
     "first_top": 100,            # page 1 starts lower, leaving room for `deckkit letterhead`
     "top": 60, "bottom": 60,     # margins of the packed body
     "keep": [["Hormat kami", "Founder & CEO"]],   # rows from first to last match stay together
     "footer": "Halaman {n} dari {total}", "footer_size": 8}

Gaps between rows are kept as they were (scaled), except a gap that falls on a page break. A
short row ending in ':' ("Catatan :") is never left alone at the bottom of a page, and a
paragraph or list item of up to ``max_lines`` rows (default 4) is never split, so no page starts
with the stray last word of a bullet.
"""
import json
from pathlib import Path


def _rows(page):
    """Rows of one page as [y0, y1, text] in reading order; images merge into overlapping rows."""
    import pymupdf

    spans = []
    for b in page.get_text("dict")["blocks"]:
        for ln in b.get("lines", []):
            r = pymupdf.Rect(ln["bbox"])
            text = "".join(s["text"] for s in ln["spans"]).strip()
            if text:
                spans.append([r.y0, r.y1, text])
    for info in page.get_image_info():
        r = pymupdf.Rect(info["bbox"])
        if r.height > 2 and r.width > 2 and r.height < page.rect.height * 0.9:
            spans.append([r.y0, r.y1, ""])
    spans.sort()
    rows = []
    for y0, y1, t in spans:
        if rows and y0 < rows[-1][1] - 1:  # overlaps the previous row: same row
            rows[-1][1] = max(rows[-1][1], y1)
            rows[-1][2] = (rows[-1][2] + " " + t).strip()
        else:
            rows.append([y0, y1, t])
    return rows


def _units(doc, keep, max_lines=4):
    """Flat list of units {page, y0, y1, text, gap_before}; ``keep`` groups merge rows."""
    units = []
    for i, page in enumerate(doc):
        prev = None
        for y0, y1, t in _rows(page):
            units.append({"page": i, "y0": y0, "y1": y1, "text": t,
                          "gap": 0 if prev is None else y0 - prev})
            prev = y1
    units = _paragraphs(units, max_lines)
    for first, last in keep:
        a = next((k for k, u in enumerate(units) if first in u["text"]), None)
        b = next((k for k, u in enumerate(units) if last in u["text"] and (a is None or k >= a)), None)
        if a is None or b is None or b == a:
            continue
        group = units[a:b + 1]
        if len({u["page"] for u in group}) > 1:
            continue  # a group across a source page break is pasted as its separate pieces
        merged = dict(group[0], y1=max(u["y1"] for u in group), text=" ".join(u["text"] for u in group))
        units[a:b + 1] = [merged]
    return units


BULLETS = set("✓✔•·-–—*▪■●○◦➢➤►")


def starts_item(text):
    """True for a row that opens a list item: a bullet glyph (also Word's Wingdings bullets, which
    extract as private-use characters) or a number like "7." / "2)"."""
    t = text.lstrip()
    if not t:
        return False
    c = t[0]
    if c in BULLETS or 0xE000 <= ord(c) <= 0xF8FF:
        return True
    head = t.split(" ", 1)[0]
    return head[:-1].isdigit() and head[-1:] in ".)"


def _paragraphs(units, max_lines):
    """Merge the rows of one paragraph or list item into one unit when it has at most
    ``max_lines`` rows, so no page starts or ends with a single stray line of it. A row continues
    the paragraph above when it sits on the same source page, follows at line spacing, and opens
    neither a list item nor a heading."""
    out, run = [], []

    def flush():
        if not run:
            return
        if 1 < len(run) <= max_lines:
            out.append(dict(run[0], y1=run[-1]["y1"], text=" ".join(u["text"] for u in run)))
        else:
            out.extend(run)
        run.clear()

    for u in units:
        h = u["y1"] - u["y0"]
        cont = (run and u["page"] == run[-1]["page"] and u["text"] and 0 <= u["gap"] < 0.6 * h
                and not starts_item(u["text"]) and not is_heading(u["text"]) and not is_heading(run[-1]["text"]))
        if not cont:
            flush()
        run.append(u)
    flush()
    return out


def is_heading(text, max_len=40):
    """A short row ending in ':' ("Lingkup :", "Catatan :") belongs with the row after it."""
    t = text.strip()
    return bool(t) and t.endswith(":") and len(t) <= max_len


def layout(units, n_pages, page_h, first_top, top, bottom, scale):
    """Assign units to pages at ``scale``. Returns [(page_index, y_out, unit)] or None if it
    needs more than ``n_pages``. A heading row (see :func:`is_heading`) is moved to the next page
    together with the row after it rather than left alone at the bottom."""
    placed, p, y = [], 0, first_top
    for k, u in enumerate(units):
        h = (u["y1"] - u["y0"]) * scale
        gap = u["gap"] * scale if k else 0
        need = h
        if is_heading(u["text"]) and k + 1 < len(units):
            nxt = units[k + 1]
            need = h + nxt["gap"] * scale + (nxt["y1"] - nxt["y0"]) * scale
        if y + gap + need > page_h - bottom and y > (first_top if p == 0 else top):
            p, y, gap = p + 1, top, 0
            if p >= n_pages:
                return None
        y += gap
        placed.append((p, y, u))
        y += h
    return placed


def repage(plan, base=None):
    import pymupdf

    if not isinstance(plan, dict):
        base = Path(plan).parent
        plan = json.loads(Path(plan).read_text())
    base = Path(base or ".")
    res = lambda p: str(p if Path(p).is_absolute() else base / p)
    src = pymupdf.open(res(plan["src"]))
    W, H = src[0].rect.width, src[0].rect.height
    n = plan["pages"]
    first_top, top, bottom = plan.get("first_top", plan.get("top", 60)), plan.get("top", 60), plan.get("bottom", 60)
    units = _units(src, plan.get("keep", []), plan.get("max_lines", 4))

    scale, placed = 1.0, None
    while scale >= plan.get("min_scale", 0.8):
        placed = layout(units, n, H, first_top, top, bottom, scale)
        if placed:
            break
        scale = round(scale - 0.01, 2)
    if not placed:
        raise ValueError(f"does not fit on {n} pages even at scale {plan.get('min_scale', 0.8)}")

    out = pymupdf.open()
    used = max(p for p, _, _ in placed) + 1
    for _ in range(used):
        out.new_page(width=W, height=H)
    # horizontal: scale about the page centre so left and right margins stay equal
    x0 = W * (1 - scale) / 2
    pieces = []  # keep every source piece open until the output is saved
    for p, y, u in placed:
        piece = pymupdf.open()
        pieces.append(piece)
        piece.insert_pdf(src, from_page=u["page"], to_page=u["page"])
        pg = piece[0]
        pad = 1.0
        for r in (pymupdf.Rect(0, 0, W, u["y0"] - pad), pymupdf.Rect(0, u["y1"] + pad, W, H)):
            if r.height > 0:
                pg.add_redact_annot(r)
        pg.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_REMOVE, graphics=pymupdf.PDF_REDACT_LINE_ART_NONE)
        clip = pymupdf.Rect(0, u["y0"] - pad, W, u["y1"] + pad)
        target = pymupdf.Rect(x0, y - pad * scale, x0 + W * scale, y + (u["y1"] - u["y0"] + pad) * scale)
        out[p].show_pdf_page(target, piece, 0, clip=clip)

    fmt = plan.get("footer")
    if fmt:
        size = plan.get("footer_size", 8)
        font = pymupdf.Font(fontfile=res(plan["font"])) if plan.get("font") else pymupdf.Font("helv")
        for k, page in enumerate(out):
            text = fmt.format(n=k + 1, total=used)
            w = font.text_length(text, fontsize=size)
            page.insert_text(((W - w) / 2, H - plan.get("footer_y", 30)), text, fontsize=size,
                             fontname="F0" if plan.get("font") else "helv",
                             fontfile=res(plan["font"]) if plan.get("font") else None,
                             color=tuple(c / 255 for c in plan.get("footer_colour", (110, 110, 110))))
    dst = res(plan["dst"])
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    out.save(dst, garbage=3, deflate=True)
    return {"pages": used, "scale": scale, "rows": len(units)}
