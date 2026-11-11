"""Company letterhead (kop surat) onto an existing PDF letter, keeping its text selectable.

Letters arrive as a Word export without a letterhead. This draws one at the top of the chosen
pages (default: page 1) and moves the page's own content down just enough to clear it; it only
scales the content when moving alone would push the last line past ``min_bottom``. Plan file::

    {"src": "letter.pdf", "dst": "letter-kop.pdf", "pages": [1],
     "logo": "logo.png", "logo_height": 34,
     "lines": [{"text": "PT CONTOH MAJU", "size": 11, "bold": true},
               {"text": "Jalan ..., Kota ... 12345", "size": 8}],
     "rules": [[35, 133, 127], [100, 103, 240]]}

Logo sits at the left margin, the text lines are right-aligned to the right margin, and each
``rules`` colour is one horizontal line under the header (the first thicker). Margins default to
the content's own left/right edges so the header lines up with the letter body. ``font`` and
``font_bold`` (TTF paths) replace the built-in Helvetica, whose bold does not always show; text
widths are measured with the same font, so right-aligned lines end exactly at the rule. The logo
is cropped to its ink first, so its left edge sits on the margin.
"""
import json
from pathlib import Path


def _content_box(page):
    import pymupdf

    box = pymupdf.Rect()
    for b in page.get_text("blocks"):
        box |= pymupdf.Rect(b[:4])
    for info in page.get_image_info():
        box |= pymupdf.Rect(info["bbox"])
    return box if not box.is_empty else page.rect


def _trimmed(path):
    """Logo cropped to its ink (white or transparent margins removed), as PNG bytes + size."""
    import io

    from PIL import Image, ImageChops

    im = Image.open(path).convert("RGBA")
    ink = ImageChops.multiply(im.getchannel("A"), ImageChops.invert(im.convert("L")).point(lambda v: 255 if v > 20 else 0))
    box = ink.getbbox()
    if box:
        im = im.crop(box)
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return buf.getvalue(), im.size


def plan_shift(content, header_bottom, page_h, gap=14, min_bottom=36):
    """Return (dy, scale) that puts ``content`` (a Rect) below ``header_bottom``.
    Moves first; scales only if the moved content would end below ``page_h - min_bottom``."""
    dy = max(0.0, header_bottom + gap - content.y0)
    limit = page_h - min_bottom
    if content.y1 + dy <= limit:
        return dy, 1.0
    scale = (limit - (header_bottom + gap)) / (content.y1 - content.y0)
    return None, scale


def letterhead(plan, base=None):
    import pymupdf

    if not isinstance(plan, dict):
        base = Path(plan).parent
        plan = json.loads(Path(plan).read_text())
    base = Path(base or ".")
    res = lambda p: str(p if Path(p).is_absolute() else base / p)
    src = pymupdf.open(res(plan["src"]))
    targets = {p - 1 for p in plan.get("pages", [1])}
    out = pymupdf.open()
    report = []
    fonts = {}
    for i, sp in enumerate(src):
        W, H = sp.rect.width, sp.rect.height
        if i not in targets:
            out.insert_pdf(src, from_page=i, to_page=i)
            continue
        content = _content_box(sp)
        left = plan.get("left", content.x0)
        right = plan.get("right", W - content.x0 if content.x1 < W - content.x0 else content.x1)
        top = plan.get("top", 28)
        page = out.new_page(width=W, height=H)

        # lay the header out first (positions only): the source page is drawn before the header,
        # because Word exports paint a full white page background that would cover it
        ops = []
        y = top
        for ln in plan.get("lines", []):
            size = ln.get("size", 9)
            key = "font_bold" if ln.get("bold") else "font"
            ffile = plan.get(key)
            alias = ("F1b" if ln.get("bold") else "F1") if ffile else ("hebo" if ln.get("bold") else "helv")
            font = fonts[alias] = fonts.get(alias) or (pymupdf.Font(fontfile=res(ffile)) if ffile else pymupdf.Font(alias))
            colour = tuple(c / 255 for c in ln.get("colour", (40, 40, 40)))
            width = font.text_length(ln["text"], fontsize=size)
            y += size * 1.25
            ops.append(("text", (right - width, y), ln["text"], alias, res(ffile) if ffile else None, size, colour))
        text_bottom = y + 4

        logo_bottom = top
        if plan.get("logo"):
            lh = plan.get("logo_height", 34)
            logo_png, (pw, ph) = _trimmed(res(plan["logo"]))
            lw = lh * pw / ph
            ly = top + max(0, (text_bottom - top - lh) / 2)
            ops.append(("logo", pymupdf.Rect(left, ly, left + lw, ly + lh)))
            logo_bottom = ly + lh

        rule_y = max(text_bottom, logo_bottom) + 6
        for k, rgb in enumerate(plan.get("rules", [[0, 0, 0]])):
            ops.append(("rule", rule_y, tuple(c / 255 for c in rgb), 1.6 if k == 0 else 0.6))
            rule_y += 3
        header_bottom = rule_y

        dy, scale = plan_shift(content, header_bottom, H, plan.get("gap", 14), plan.get("min_bottom", 36))
        if scale == 1.0:
            target = pymupdf.Rect(0, dy, W, H + dy)
            page.show_pdf_page(target, src, i, clip=pymupdf.Rect(0, 0, W, H))
        else:
            # scale about the content's left edge so the body keeps its left margin
            ty = header_bottom + plan.get("gap", 14)
            tx = content.x0 * (1 - scale)
            target = pymupdf.Rect(tx, ty - content.y0 * scale, tx + W * scale, ty - content.y0 * scale + H * scale)
            page.show_pdf_page(target, src, i)
            dy = None
        # the moved page's own background may reach into the header band: paint it white first
        page.draw_rect(pymupdf.Rect(0, 0, W, header_bottom + 2), color=None, fill=(1, 1, 1))
        for op in ops:
            if op[0] == "text":
                _, pos, text, alias, ffile, size, colour = op
                page.insert_text(pos, text, fontname=alias, fontfile=ffile, fontsize=size, color=colour)
            elif op[0] == "logo":
                page.insert_image(op[1], stream=logo_png)
            else:
                _, ry, colour, width = op
                page.draw_line((left, ry), (right, ry), color=colour, width=width)
        report.append((i + 1, round(header_bottom, 1), dy if dy is None else round(dy, 1), round(scale, 3)))
    dst = res(plan["dst"])
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    out.save(dst, garbage=3, deflate=True)
    return report
