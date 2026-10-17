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
