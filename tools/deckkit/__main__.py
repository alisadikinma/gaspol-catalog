"""``python3 -m tools.deckkit <command>`` from the plugin root."""
import argparse
import sys

from PIL import Image


def main(argv=None):
    ap = argparse.ArgumentParser(prog="deckkit", description="Post-render deck tooling.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("pdf", help="pages dir -> PDF, optional watermark")
    s.add_argument("src")
    s.add_argument("out")
    s.add_argument("--watermark", help="tile text (enables the watermark)")
    s.add_argument("--corner", default="", help="corner text, e.g. CONFIDENTIAL")
    s.add_argument("--page-size", help="WxH every page is scaled to, e.g. 2752x1536")
    s.add_argument("--skip", nargs="*", default=[], help="page filenames to leave out")
    s.add_argument("--pattern", default=r"\d{2}\.png|slide-\d+\.png")

    s = sub.add_parser("pptx", help="images -> 16:9 pptx")
    s.add_argument("out")
    s.add_argument("images", nargs="+")

    s = sub.add_parser("stamp", help="stamp page numbers from filenames")
    s.add_argument("src")
    s.add_argument("dst")
    s.add_argument("--wordmark", help="dark-on-transparent logo png, drawn white")

    s = sub.add_parser("band", help="add a footer band to each page")
    s.add_argument("src_dir")
    s.add_argument("dst_dir")
    s.add_argument("--text", required=True)
    s.add_argument("--logos", nargs="*", default=[], help="left-to-right logo files")

    s = sub.add_parser("unmark", help="invert a previous watermark (same text/options)")
    s.add_argument("src")
    s.add_argument("dst")
    s.add_argument("--watermark", required=True)
    s.add_argument("--corner", default="")
    s.add_argument("--dark", choices=["yes", "no"], help="ink was light (dark page) or dark")

    s = sub.add_parser("erase-footer", help="OCR + inpaint away a footer tag, e.g. 'ACME'")
    s.add_argument("image")
    s.add_argument("needle")

    s = sub.add_parser("logo-slots", help="paste logos into blank white boxes, left to right")
    s.add_argument("image")
    s.add_argument("logos", nargs="+")

    a = ap.parse_args(argv)
    try:
        if a.cmd == "pdf":
            from . import pdf
            size = tuple(int(v) for v in a.page_size.split("x")) if a.page_size else None
            pages = pdf.list_pages(a.src, a.pattern, a.skip)
            opts = {"text": a.watermark or "", "corner_text": a.corner} if (a.watermark or a.corner) else None
            print(f"{pdf.build_pdf(pages, a.out, size, mark_opts=opts)} pages -> {a.out}")
        elif a.cmd == "pptx":
            from . import pptx
            print(f"{pptx.build_pptx(a.images, a.out)} slides -> {a.out}")
        elif a.cmd == "stamp":
            from . import stamp
            print(f"stamped {len(stamp.stamp_dir(a.src, a.dst, a.wordmark))} pages")
        elif a.cmd == "band":
            import os
            from . import band
            logos = [Image.open(p) for p in a.logos]
            os.makedirs(a.dst_dir, exist_ok=True)
            names = sorted(f for f in os.listdir(a.src_dir) if f.lower().endswith(".png"))
            for n in names:
                band.add_band(Image.open(os.path.join(a.src_dir, n)), a.text, logos).save(os.path.join(a.dst_dir, n))
            print(f"{len(names)} pages banded")
        elif a.cmd == "unmark":
            from . import watermark
            dark = None if a.dark is None else a.dark == "yes"
            watermark.unmark(Image.open(a.src), dark=dark, text=a.watermark, corner_text=a.corner).save(a.dst)
            print(a.dst)
        elif a.cmd == "erase-footer":
            from . import erase
            r = erase.erase_footer(a.image, a.needle)
            print("not found" if r is None else f"erased x {r[0]}..{r[1]}")
            return 1 if r is None else 0
        elif a.cmd == "logo-slots":
            from . import slots
            img, used = slots.fill_slots(Image.open(a.image), a.logos)
            img.save(a.image)
            print(f"{len(used)} logos placed")
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
