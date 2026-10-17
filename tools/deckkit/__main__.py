"""``python3 -m tools.deckkit <command>`` from the plugin root."""
import argparse
import re
import sys

from PIL import Image


def _grid(spec):
    try:
        c, r = (int(v) for v in spec.lower().split("x"))
    except ValueError:
        raise ValueError(f"--grid needs CxR like 3x4, got {spec!r}") from None
    return c, r


def main(argv=None):
    ap = argparse.ArgumentParser(prog="deckkit", description="Post-render deck tooling.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("pdf", help="pages dir -> PDF, optional watermark")
    s.add_argument("src")
    s.add_argument("out")
    s.add_argument("--watermark", help="tile text (enables the watermark)")
    s.add_argument("--corner", default="", help="corner text, e.g. CONFIDENTIAL")
    s.add_argument("--watermark-logo", help="logo image tiled diagonally as the watermark (enables it; not reversible)")
    s.add_argument("--grid", help="CxR: put the watermark text at the centre of each grid cell, e.g. 3x4")
    s.add_argument("--page-size", help="WxH every page is scaled to, e.g. 2752x1536")
    s.add_argument("--skip", nargs="*", default=[], help="page filenames to leave out")
    s.add_argument("--pattern", default=r"\d{2}\.png|slide-\d+\.png")

    s = sub.add_parser("pptx", help="images -> 16:9 pptx")
    s.add_argument("out")
    s.add_argument("images", nargs="+")
    s.add_argument("--transition", choices=["fade"], help="slide transition (default none)")
    s.add_argument("--jpeg-quality", type=int, help="store pictures as JPEG at this quality, e.g. 92")

    s = sub.add_parser("stamp", help="stamp page numbers from filenames")
    s.add_argument("src")
    s.add_argument("dst")
    s.add_argument("--wordmark", help="dark-on-transparent logo png, drawn white")

    s = sub.add_parser("band", help="add a footer band to each page")
    s.add_argument("src_dir")
    s.add_argument("dst_dir")
    s.add_argument("--text", required=True)
    s.add_argument("--logos", nargs="*", default=[], help="left-to-right logo files")
    s.add_argument("--url", help="small line under the logos, e.g. a web address")
    s.add_argument("--numbers", action="store_true",
                   help="draw page numbers from filename digits (only after the renders are approved)")
    s.add_argument("--number-fmt", default="{n} / {total}", help="number text, uses {n} and {total}")
    s.add_argument("--fit-canvas", help="WxH: letterbox each page to this size before banding")

    s = sub.add_parser("review", help="deck.md -> HTML review page")
    s.add_argument("deck")
    s.add_argument("out")
    s.add_argument("--title", default="Deck review")

    s = sub.add_parser("deckmd", help="prompts dir -> deck.md text")
    s.add_argument("prompts_dir")
    s.add_argument("out")

    s = sub.add_parser("unmark", help="invert a previous watermark (same text/options)")
    s.add_argument("src")
    s.add_argument("dst")
    s.add_argument("--watermark", required=True)
    s.add_argument("--corner", default="")
    s.add_argument("--grid", help="CxR, if the mark was applied with --grid")
    s.add_argument("--dark", choices=["yes", "no"], help="ink was light (dark page) or dark")

    s = sub.add_parser("erase-footer", help="OCR + inpaint away a footer tag, e.g. 'ACME'")
    s.add_argument("image")
    s.add_argument("needle")

    s = sub.add_parser("logo-slots", help="paste logos into blank white boxes, left to right")
    s.add_argument("image")
    s.add_argument("logos", nargs="+")
    s.add_argument("--key", choices=["white", "magenta"], default="white", help="slot colour (default white)")
    s.add_argument("--mode", choices=["flat", "quad"], default="flat", help="flat paste, or quad = perspective warp onto a tilted slot")

    s = sub.add_parser("photo", help="cover-crop a real photo into a box or circle")
    s.add_argument("image")
    s.add_argument("photo")
    s.add_argument("--box", required=True, help="x,y,w,h (with --circle: its centre and min(w,h)/2 are used)")
    s.add_argument("--radius", type=int, default=0, help="corner radius in px (clamped to half the short side)")
    s.add_argument("--circle", action="store_true", help="circular mask instead of a rounded box")
    s.add_argument("--out", help="output path (default: overwrite IMAGE)")

    s = sub.add_parser("recolour", help="recolour the accent bars beside text points, top to bottom")
    s.add_argument("image")
    s.add_argument("--colours", nargs="+", required=True, help="hex colours, top bar first")
    s.add_argument("--x-from", type=float, default=0.55, help="only look right of this page fraction")
    s.add_argument("--source", default="#23857f", help="current bar colour")
    s.add_argument("--out", help="output path (default: overwrite IMAGE)")

    s = sub.add_parser("table", help="spec JSON -> drawn comparison table page (exact numbers)")
    s.add_argument("spec")
    s.add_argument("out")
    s.add_argument("--size", default="2752x1536", help="WxH of the page (default 2752x1536)")
    s.add_argument("--font", help="font file (.ttf/.ttc); default: first system font found")

    s = sub.add_parser("shot", help="HTML page -> PNG at an exact size (headless Chrome)")
    s.add_argument("html")
    s.add_argument("out")
    s.add_argument("--size", default="2752x1536", help="WxH of the PNG (default 2752x1536)")

    s = sub.add_parser("prompts", help="slide spec -> prompt files + manifest")
    s.add_argument("spec")
    s.add_argument("--house", help="house standard file (else $GASPOL_CATALOG_HOUSE or .gaspol/context-sources.md)")
    s.add_argument("--preset", help="style preset name (default: the house standard's preset)")
    s.add_argument("--out", help="output dir (default: <spec dir>/prompts)")
    s.add_argument("--only", nargs="*", type=int, default=[], help="write only these slide numbers")

    s = sub.add_parser("gen", help="prompt manifest -> slide images (image MCP)")
    s.add_argument("manifest")
    s.add_argument("--house", help="house standard file (image_client, image_model, image_mode)")
    s.add_argument("--ver", help="version tag: output NN-<ver>.png (default slide-NN.png)")
    s.add_argument("--only", nargs="*", type=int, default=[], help="render only these slide numbers")
    s.add_argument("--model", help="image model (default: house image_model)")
    s.add_argument("--mode", help="generator mode (default: house image_mode)")
    s.add_argument("--workers", type=int, default=4)
    s.add_argument("--tries", type=int, default=3)
    s.add_argument("--out", help="output dir (default: <project>/renders)")
    s.add_argument("--raw", help="raw generator dir (default: <project>/.tmp/mentah)")
    s.add_argument("--resolution", default="2K")

    a = ap.parse_args(argv)
    try:
        if a.cmd == "pdf":
            from . import pdf
            size = tuple(int(v) for v in a.page_size.split("x")) if a.page_size else None
            pages = pdf.list_pages(a.src, a.pattern, a.skip)
            opts = None
            if a.watermark or a.corner or a.watermark_logo:
                opts = {"text": a.watermark or "", "corner_text": a.corner}
                if a.watermark_logo:
                    opts["logo"] = a.watermark_logo
                if a.grid:
                    opts["grid"] = _grid(a.grid)
            print(f"{pdf.build_pdf(pages, a.out, size, mark_opts=opts)} pages -> {a.out}")
        elif a.cmd == "pptx":
            from . import pptx
            print(f"{pptx.build_pptx(a.images, a.out, transition=a.transition, jpeg_quality=a.jpeg_quality)} slides -> {a.out}")
        elif a.cmd == "stamp":
            from . import stamp
            print(f"stamped {len(stamp.stamp_dir(a.src, a.dst, a.wordmark))} pages")
        elif a.cmd == "band":
            import os
            from . import band
            logos = [Image.open(p) for p in a.logos]
            os.makedirs(a.dst_dir, exist_ok=True)
            names = sorted(f for f in os.listdir(a.src_dir) if f.lower().endswith(".png"))
            fit = None
            if a.fit_canvas:
                try:
                    fit = tuple(int(v) for v in a.fit_canvas.lower().split("x"))
                    assert len(fit) == 2
                except (ValueError, AssertionError):
                    raise ValueError(f"--fit-canvas needs WxH like 2752x1536, got {a.fit_canvas!r}") from None
            for n in names:
                digits = re.search(r"\d+", n) if a.numbers else None
                if a.numbers and not digits:
                    raise ValueError(f"--numbers needs digits in the filename, got {n!r}")
                band.add_band(Image.open(os.path.join(a.src_dir, n)), a.text, logos, url=a.url,
                              number=int(digits.group(0)) if digits else None,
                              total=len(names) if a.numbers else None,
                              number_fmt=a.number_fmt, fit_canvas=fit).save(os.path.join(a.dst_dir, n))
            print(f"{len(names)} pages banded")
        elif a.cmd == "unmark":
            from . import watermark
            dark = None if a.dark is None else a.dark == "yes"
            watermark.unmark(Image.open(a.src), dark=dark, text=a.watermark, corner_text=a.corner,
                             grid=_grid(a.grid) if a.grid else None).save(a.dst)
            print(a.dst)
        elif a.cmd == "review":
            from pathlib import Path
            from . import deckmd
            md = Path(a.deck).read_text(encoding="utf-8")
            Path(a.out).write_text(deckmd.review_html(md, a.title), encoding="utf-8")
            print(a.out)
        elif a.cmd == "deckmd":
            from pathlib import Path
            from . import deckmd
            Path(a.out).write_text(deckmd.from_prompts(a.prompts_dir), encoding="utf-8")
            print(a.out)
        elif a.cmd == "erase-footer":
            from . import erase
            r = erase.erase_footer(a.image, a.needle)
            print("not found" if r is None else f"erased x {r[0]}..{r[1]}")
            return 1 if r is None else 0
        elif a.cmd == "logo-slots":
            from . import slots
            img, used = slots.fill_slots(Image.open(a.image), a.logos, key=a.key, mode=a.mode)
            img.save(a.image)
            print(f"{len(used)} logos placed")
        elif a.cmd == "photo":
            from . import photo
            try:
                x, y, w, h = (int(v) for v in a.box.split(","))
            except ValueError:
                raise ValueError(f"--box needs four integers x,y,w,h, got {a.box!r}") from None
            with Image.open(a.image) as page, Image.open(a.photo) as pic:
                if a.circle:
                    res = photo.circle(page, pic, (x + w // 2, y + h // 2), min(w, h) // 2)
                else:
                    res = photo.place(page, pic, (x, y, w, h), radius=a.radius)
            out = a.out or a.image
            res.save(out)
            print(out)
        elif a.cmd == "recolour":
            from . import recolour
            with Image.open(a.image) as page:
                res = recolour.bars(page, a.colours, x_from=a.x_from, source=a.source)
            out = a.out or a.image
            res.save(out)
            print(out)
        elif a.cmd == "table":
            import json
            from . import table
            try:
                size = tuple(int(v) for v in a.size.lower().split("x"))
                assert len(size) == 2
            except (ValueError, AssertionError):
                raise ValueError(f"--size needs WxH like 2752x1536, got {a.size!r}") from None
            with open(a.spec, encoding="utf-8") as fh:
                spec = json.load(fh)
            table.render(spec, size=size, font_path=a.font).save(a.out)
            print(a.out)
        elif a.cmd == "shot":
            from . import chrome
            try:
                size = tuple(int(v) for v in a.size.lower().split("x"))
                assert len(size) == 2
            except (ValueError, AssertionError):
                raise ValueError(f"--size needs WxH like 2752x1536, got {a.size!r}") from None
            print(chrome.shot(a.html, a.out, size=size))
        elif a.cmd == "prompts":
            from pathlib import Path
            from . import house, prompts
            hp = house.resolve(explicit=a.house, start=Path(a.spec).resolve().parent)
            h = house.load(hp) if hp else None
            out = Path(a.out) if a.out else Path(a.spec).resolve().parent / "prompts"
            n = prompts.build(a.spec, house=h, preset=a.preset, out_dir=out, only=a.only or None)
            print(f"{n} prompt -> {out}")
        elif a.cmd == "gen":
            from pathlib import Path
            from . import gen, house
            mp = Path(a.manifest).resolve()
            hp = house.resolve(explicit=a.house, start=mp.parent)
            h = house.load(hp) if hp else {}
            model = a.model or h.get("image_model")
            if not model:
                raise ValueError(gen.NO_MODEL)
            generator = gen.load_generator(h.get("image_client"))
            res = gen.run(mp, generator, out_dir=a.out, raw_dir=a.raw, ver=a.ver, only=a.only or None,
                          workers=a.workers, tries=a.tries, model=model,
                          mode=a.mode or h.get("image_mode"), resolution=a.resolution)
            for n, status in res:
                print(f"{n:02d} {status}")
            return 1 if any(st.startswith("FAIL") for _, st in res) else 0
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
