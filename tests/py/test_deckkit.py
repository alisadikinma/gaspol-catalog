import tempfile
import unittest
from pathlib import Path

try:
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    raise unittest.SkipTest('needs Pillow + numpy: use the gaspol-video venv python')

from tools.deckkit import band, compose, fonts, lockup, patch, pdf, slots, stamp, watermark


def page(size=(600, 340), colour=(240, 240, 240)):
    im = Image.new("RGB", size, colour)
    d = ImageDraw.Draw(im)
    for i in range(0, size[0], 40):
        d.line([(i, 0), (i, size[1])], fill=(200, 210, 230), width=3)
    return im


class WatermarkTest(unittest.TestCase):
    def test_mark_changes_pixels_and_picks_ink_by_page_darkness(self):
        light, dark = page(), page(colour=(20, 24, 40))
        for im in (light, dark):
            out = watermark.mark(im, text="DECK")
            self.assertGreater(np.abs(np.asarray(out).astype(int) - np.asarray(im).astype(int)).max(), 5)
        # watermark on a light page darkens, on a dark page lightens
        self.assertLess(np.asarray(watermark.mark(light, text="DECK")).mean(), np.asarray(light).mean())
        self.assertGreater(np.asarray(watermark.mark(dark, text="DECK")).mean(), np.asarray(dark).mean())

    def test_unmark_restores_original_within_rounding(self):
        for im in (page(), page(colour=(20, 24, 40))):
            marked = watermark.mark(im, text="DECK", corner_text="CONFIDENTIAL")
            back = watermark.unmark(marked, text="DECK", corner_text="CONFIDENTIAL", dark=watermark.is_dark(im))
            err = np.abs(np.asarray(back).astype(int) - np.asarray(im).astype(int))
            self.assertLessEqual(err.max(), 3)


class PdfTest(unittest.TestCase):
    def test_pdf_scales_pages_and_skips(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            page((600, 340)).save(t / "01.png")
            page((300, 170)).save(t / "02.png")
            page((300, 170)).save(t / "03.png")
            pages = pdf.list_pages(t, skip=["03.png"])
            self.assertEqual([Path(p).name for p in pages], ["01.png", "02.png"])
            n = pdf.build_pdf(pages, t / "o.pdf", page_size=(400, 226), mark_opts={"text": "X"})
            self.assertEqual(n, 2)
            self.assertTrue((t / "o.pdf").read_bytes().startswith(b"%PDF"))

    def test_pdf_without_page_size_refuses_other_aspect(self):
        # A banded page (taller) next to a 16:9 page would be stretched; refuse instead.
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            page((600, 340)).save(t / "01.png")
            page((600, 400)).save(t / "02.png")
            with self.assertRaisesRegex(ValueError, r"02.png.*aspect"):
                pdf.build_pdf(pdf.list_pages(t), t / "o.pdf")

    def test_pdf_without_page_size_uses_first_page_size(self):
        # Image models return mixed sizes (2048x1152 and 1672x941); with no page_size the PDF
        # used to keep both and pages 4-8 came out smaller.
        import re as _re
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            page((600, 340)).save(t / "01.png")
            page((300, 170)).save(t / "02.png")
            pdf.build_pdf(pdf.list_pages(t), t / "o.pdf")
            boxes = set(_re.findall(rb"/MediaBox \[\s*0 0 ([\d.]+) ([\d.]+)\s*\]", (t / "o.pdf").read_bytes()))
            self.assertEqual(len(boxes), 1, boxes)

    def test_cli_opacity_percent(self):
        from tools.deckkit import __main__ as cli
        self.assertEqual(cli._alpha("12"), 31)   # 12% of 255
        self.assertEqual(cli._alpha("10"), 26)
        for bad in ("0", "101", "x"):
            with self.assertRaisesRegex(ValueError, "--opacity"):
                cli._alpha(bad)
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            page().save(t / "01.png")
            self.assertEqual(_quiet_cli(["pdf", str(t), str(t / "o.pdf"), "--watermark", "X", "--opacity", "12"]), 0)
            self.assertTrue((t / "o.pdf").read_bytes().startswith(b"%PDF"))
            self.assertNotEqual(_quiet_cli(["pdf", str(t), str(t / "p.pdf"), "--opacity", "12"]), 0)

    def test_list_pages_empty_raises(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(FileNotFoundError):
                pdf.list_pages(t)


class StampBandPatchTest(unittest.TestCase):
    def test_stamp_uses_filename_number_and_wordmark(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            src, dst = t / "s", t / "d"
            src.mkdir()
            im = page()
            ImageDraw.Draw(im).rectangle((0, int(340 * 0.94), 600, 340), fill=(20, 30, 60))
            im.save(src / "07.png")
            Image.new("RGBA", (80, 20), (10, 10, 10, 255)).save(t / "wm.png")
            self.assertEqual(stamp.stamp_dir(src, dst, t / "wm.png"), ["07.png"])
            out = np.asarray(Image.open(dst / "07.png"))
            band_region = out[int(340 * 0.95):, int(600 * 0.93):]
            self.assertGreater((band_region.min(2) > 200).sum(), 0, "numeral drawn white on the band")

    def test_add_band_grows_page(self):
        logo = Image.new("RGBA", (100, 40), (200, 0, 0, 255))
        out = band.add_band(page(), "CONFIDENTIAL", [logo, logo])
        self.assertEqual(out.width, 600)
        self.assertEqual(out.height, 340 + int(600 * 0.055))

    def test_blend_fill_hides_a_mark_on_a_gradient(self):
        g = np.tile(np.linspace(40, 200, 200, dtype=np.uint8), (100, 1))
        img = Image.fromarray(np.dstack([g, g, g]))
        before = np.asarray(img).copy()
        ImageDraw.Draw(img).rectangle((90, 40, 110, 60), fill=(255, 0, 0))
        patch.blend_fill(img, (90, 40, 111, 61))
        err = np.abs(np.asarray(img).astype(int) - before.astype(int))[40:61, 90:111]
        self.assertLess(err.mean(), 6)

    def test_ink_bbox(self):
        im = Image.new("RGB", (100, 100), (255, 255, 255))
        ImageDraw.Draw(im).rectangle((20, 30, 40, 50), fill=(0, 0, 0))
        self.assertEqual(patch.ink_bbox(im, (0, 0, 100, 100)), (20, 30, 40, 50))
        self.assertIsNone(patch.ink_bbox(Image.new("RGB", (50, 50), (255, 255, 255)), (0, 0, 50, 50)))


try:
    import cv2  # noqa: F401
    HAVE_CV = True
except ImportError:
    HAVE_CV = False


@unittest.skipUnless(HAVE_CV, "cv2 not importable (use the gaspol-video venv python)")
class SlotsTest(unittest.TestCase):
    def test_fill_slots_left_to_right_and_count_mismatch(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            im = Image.new("RGB", (900, 300), (20, 40, 80))
            d = ImageDraw.Draw(im)
            for x in (50, 350, 650):
                d.rectangle((x, 50, x + 200, 250), fill=(255, 255, 255))
            for i, c in enumerate([(255, 0, 0), (0, 255, 0), (0, 0, 255)]):
                Image.new("RGBA", (100, 40), c + (255,)).save(t / f"l{i}.png")
            logos = [t / f"l{i}.png" for i in range(3)]
            with self.assertRaises(ValueError):
                slots.fill_slots(im.copy(), logos[:2])
            im, used = slots.fill_slots(im, logos)
            self.assertEqual([u[0] for u in used], sorted(u[0] for u in used))
            self.assertEqual(im.getpixel((150, 150)), (255, 0, 0))
            self.assertEqual(im.getpixel((750, 150)), (0, 0, 255))


def _quiet_cli(argv):
    import contextlib
    import io
    from tools.deckkit import __main__ as cli
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return cli.main(argv)


MAGENTA = (255, 0, 255)


def _magenta_page(polys, size=(900, 400)):
    im = Image.new("RGB", size, (20, 40, 80))
    d = ImageDraw.Draw(im)
    for poly in polys:
        d.polygon(poly, fill=MAGENTA)
    return im


@unittest.skipUnless(HAVE_CV, "cv2 not importable (use the gaspol-video venv python)")
class QuadSlotsTest(unittest.TestCase):
    PARA = [(100, 80), (400, 100), (380, 300), (80, 280)]

    def test_find_slots_magenta_corners(self):
        quads = slots.find_slots(_magenta_page([self.PARA]), key="magenta")
        self.assertEqual(len(quads), 1)
        for got, want in zip(quads[0], self.PARA):
            self.assertLessEqual(abs(got[0] - want[0]), 3)
            self.assertLessEqual(abs(got[1] - want[1]), 3)

    def test_two_slots_sorted_left_to_right(self):
        right = [(600, 80), (800, 80), (800, 300), (600, 300)]
        quads = slots.find_slots(_magenta_page([right, self.PARA]), key="magenta")
        self.assertEqual(len(quads), 2)
        self.assertLess(quads[0][0][0], quads[1][0][0])

    def test_paste_quad_leaves_no_magenta(self):
        im = _magenta_page([self.PARA])
        quad = slots.find_slots(im, key="magenta")[0]
        logo = Image.new("RGBA", (120, 40), (255, 255, 255, 255))
        for plate in (None, (10, 10, 10)):
            out = slots.paste_quad(im, logo, quad, plate=plate)
            xs = [p[0] for p in quad]
            ys = [p[1] for p in quad]
            a = np.asarray(out.convert("RGB"))[min(ys):max(ys) + 1, min(xs):max(xs) + 1].astype(int)
            dist = np.sqrt(((a - np.array(MAGENTA)) ** 2).sum(2))
            self.assertGreaterEqual(dist.min(), 40)
        self.assertEqual(out.getpixel((240, 190)), (255, 255, 255))
        self.assertEqual(im.getpixel((240, 190)), MAGENTA)

    def test_rounded_tilted_phone_screen_gets_its_sharp_corners(self):
        """2026-11-01 forklift slide 6: a phone screen (rounded corners, a notch, seen in
        perspective) fell back to minAreaRect, so the pasted screen ran off the frame."""
        import cv2
        true = np.array([(120, 60), (300, 40), (320, 420), (110, 440)], np.int32)
        m = np.zeros((500, 450), np.uint8)
        cv2.fillConvexPoly(m, true, 1)
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (41, 41)))
        m[45:62, 180:240] = 0                      # the notch
        a = np.full((500, 450, 3), 40, np.uint8)
        a[m > 0] = MAGENTA
        quad = slots.find_slots(Image.fromarray(a), key="magenta", min_area=0.01)[0]
        for got, want in zip(quad, true.tolist()):
            self.assertLessEqual(abs(got[0] - want[0]), 4, (quad, true.tolist()))
            self.assertLessEqual(abs(got[1] - want[1]), 4, (quad, true.tolist()))

    def test_pixel_mode_leaves_no_pink_fringe_on_the_bezel(self):
        """2026-11-01 forklift slide 6: a screen's anti-aliased edge (magenta blended into a dark
        bezel) survived the paste as a purple rim around every phone and monitor."""
        im = Image.new("RGB", (500, 400), (40, 40, 44))
        d = ImageDraw.Draw(im)
        d.rectangle((100, 80, 400, 300), fill=MAGENTA)
        for i in range(1, 9):   # the bezel next to the screen, tinted by the magenta glow
            d.rectangle((100 - i, 80 - i, 400 + i, 300 + i), outline=(60 + 2 * i, 30, 62 + 2 * i))
        for i in range(9, 17):  # the rest of a thick phone bezel, drawn plum (70,55,72)
            d.rectangle((100 - i, 80 - i, 400 + i, 300 + i), outline=(70, 55, 72))
        quad = slots.find_slots(im, key="magenta", min_area=0.01)[0]
        shot = Image.new("RGBA", (300, 220), (230, 240, 235, 255))
        out = np.asarray(slots.paste_quad(im, shot, quad, fit=1.0, mode="pixel")).astype(int)
        r, g, b = out[..., 0], out[..., 1], out[..., 2]
        pink = (r - g > 12) & (b - g > 12)
        self.assertEqual(int(pink.sum()), 0)
        self.assertEqual(tuple(out[20, 20]), (40, 40, 44))   # far from the screen: untouched

    def test_white_key_matches_find_white_slots(self):
        im = Image.new("RGB", (900, 300), (20, 40, 80))
        d = ImageDraw.Draw(im)
        for x in (50, 350, 650):
            d.rectangle((x, 50, x + 200, 250), fill=(255, 255, 255))
        boxes = slots.find_white_slots(im, 0.002)
        quads = slots.find_slots(im, key="white")
        self.assertEqual([(q[0][0], q[0][1], q[2][0] - q[0][0] + 1, q[2][1] - q[0][1] + 1) for q in quads], boxes)

    def test_fill_slots_quad_count_mismatch(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "l.png"
            Image.new("RGBA", (50, 20), (255, 0, 0, 255)).save(p)
            with self.assertRaisesRegex(ValueError, "found 1 slots, got 2 logos"):
                slots.fill_slots(_magenta_page([self.PARA]), [p, p], key="magenta", mode="quad")

    def test_cli_magenta_quad(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            _magenta_page([self.PARA]).save(t / "p.png")
            Image.new("RGBA", (120, 40), (255, 0, 0, 255)).save(t / "l.png")
            rc = _quiet_cli(["logo-slots", str(t / "p.png"), str(t / "l.png"), "--key", "magenta", "--mode", "quad"])
            self.assertEqual(rc, 0)
            self.assertEqual(Image.open(t / "p.png").convert("RGB").getpixel((240, 190)), (255, 0, 0))

    def test_flat_magenta_leaves_no_pink_halo(self):
        # Image models antialias the slot edge: a 1-2 px ring of half-magenta survived the paste
        # as a faint pink frame around the logo.
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "l.png"
            Image.new("RGBA", (80, 30), (255, 0, 0, 255)).save(p)
            im = Image.new("RGB", (1000, 500), (250, 250, 250))
            d = ImageDraw.Draw(im)
            d.rectangle((98, 98, 301, 161), fill=(252, 150, 250))
            d.rectangle((100, 100, 299, 159), fill=(249, 2, 243))
            out, _ = slots.fill_slots(im, [p], min_area=0.002, key="magenta")
            a = np.asarray(out).astype(int)[90:170, 90:310]
            pink = (np.minimum(a[..., 0], a[..., 2]) - a[..., 1]) > 40
            self.assertFalse(pink.any(), f"{int(pink.sum())} pink pixels left")

    def test_flat_magenta_pad_covers_soft_glow(self):
        # gpt-image-2 draws a soft pink glow ~10 px wide around the slot; pad plates it with the
        # ground colour sampled just outside.
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "l.png"
            Image.new("RGBA", (80, 30), (255, 0, 0, 255)).save(p)
            im = Image.new("RGB", (1000, 500), (250, 250, 250))
            d = ImageDraw.Draw(im)
            d.rectangle((90, 90, 309, 169), fill=(254, 238, 254))
            d.rectangle((100, 100, 299, 159), fill=(249, 2, 243))
            out, _ = slots.fill_slots(im, [p], min_area=0.002, key="magenta", pad=12)
            a = np.asarray(out).astype(int)[80:180, 80:320]
            tint = (np.minimum(a[..., 0], a[..., 2]) - a[..., 1]) > 4
            self.assertFalse(tint.any(), f"{int(tint.sum())} tinted pixels left")
            self.assertEqual(tuple(a[5, 5]), (250, 250, 250))

    def test_cli_min_area_finds_small_slots(self):
        # A logo slot of 0.5% of the page (a card header) is below the 1% default and was missed.
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            im = Image.new("RGB", (1000, 500), (243, 246, 245))
            ImageDraw.Draw(im).rectangle((100, 100, 199, 124), fill=(249, 2, 243))
            im.save(t / "p.png")
            Image.new("RGBA", (120, 40), (255, 0, 0, 255)).save(t / "l.png")
            self.assertNotEqual(_quiet_cli(["logo-slots", str(t / "p.png"), str(t / "l.png"), "--key", "magenta"]), 0)
            rc = _quiet_cli(["logo-slots", str(t / "p.png"), str(t / "l.png"), "--key", "magenta", "--min-area", "0.002"])
            self.assertEqual(rc, 0)
            self.assertEqual(Image.open(t / "p.png").convert("RGB").getpixel((150, 112)), (255, 0, 0))

    def test_cli_fit_makes_logo_fill_more_of_the_slot(self):
        # A client asked for bigger logos; the fixed 0.78 x 0.7 fit left half the slot empty.
        def logo_height(extra):
            with tempfile.TemporaryDirectory() as t:
                t = Path(t)
                im = Image.new("RGB", (1000, 500), (243, 246, 245))
                ImageDraw.Draw(im).rectangle((100, 100, 499, 199), fill=(249, 2, 243))
                im.save(t / "p.png")
                Image.new("RGBA", (200, 200), (255, 0, 0, 255)).save(t / "l.png")
                rc = _quiet_cli(["logo-slots", str(t / "p.png"), str(t / "l.png"), "--key", "magenta",
                                 "--min-area", "0.002", *extra])
                self.assertEqual(rc, 0)
                a = np.asarray(Image.open(t / "p.png").convert("RGB")).astype(int)
                red = (a[..., 0] > 200) & (a[..., 1] < 60) & (a[..., 2] < 60)
                return int(red.any(axis=1).sum())
        self.assertLess(logo_height([]), 75)
        self.assertGreaterEqual(logo_height(["--fit", "0.95", "0.95"]), 90)

    def test_cli_fit_rejects_out_of_range(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            Image.new("RGB", (100, 50)).save(t / "p.png")
            Image.new("RGBA", (10, 10)).save(t / "l.png")
            self.assertNotEqual(_quiet_cli(["logo-slots", str(t / "p.png"), str(t / "l.png"), "--fit", "1.5", "0.9"]), 0)


class SilentFailureWatermarkTest(unittest.TestCase):
    def test_mark_rejects_unknown_option(self):
        with self.assertRaisesRegex(TypeError, r"unknown watermark option\(s\): \['txt'\]"):
            watermark.mark(page(), txt="X")

    def test_unmark_rejects_unknown_option(self):
        with self.assertRaisesRegex(TypeError, "unknown watermark option"):
            watermark.unmark(page(), opacitiy=3)

    def test_grid_without_text_raises(self):
        with self.assertRaisesRegex(ValueError, "grid needs"):
            watermark.mark(page(), text="", grid=(2, 2))

    def test_logo_with_text_or_grid_raises(self):
        with self.assertRaisesRegex(ValueError, "logo watermark cannot be combined with text/grid"):
            watermark.mark(page(), logo="x.png", text="DECK")
        with self.assertRaisesRegex(ValueError, "logo watermark cannot be combined with text/grid"):
            watermark.mark(page(), logo="x.png", text="", grid=(2, 2))

    def test_cli_grid_without_watermark_fails(self):
        with tempfile.TemporaryDirectory() as d:
            t = Path(d)
            src = t / "src"
            src.mkdir()
            page().save(src / "01.png")
            self.assertEqual(_quiet_cli(["pdf", str(src), str(t / "o.pdf"), "--grid", "3x4", "--corner", "C"]), 1)
            self.assertEqual(_quiet_cli(["pdf", str(src), str(t / "o.pdf"), "--grid", "3x4"]), 1)
            page().save(t / "m.png")
            self.assertEqual(_quiet_cli(["unmark", str(t / "m.png"), str(t / "u.png"), "--watermark", "", "--grid", "3x4"]), 1)

    def test_cli_logo_with_text_fails(self):
        with tempfile.TemporaryDirectory() as d:
            t = Path(d)
            src = t / "src"
            src.mkdir()
            page().save(src / "01.png")
            Image.new("RGBA", (40, 20), (0, 0, 0, 255)).save(t / "l.png")
            self.assertEqual(_quiet_cli(["pdf", str(src), str(t / "o.pdf"), "--watermark", "X",
                                         "--watermark-logo", str(t / "l.png")]), 1)


class SilentFailureFontTest(unittest.TestCase):
    def test_explicit_missing_font_raises(self):
        with self.assertRaises(FileNotFoundError):
            fonts.load_font(20, "/nonexistent/none.ttf")
        with self.assertRaises(FileNotFoundError):
            fonts.find_font("/nonexistent/none.ttf")

    def test_explicit_unopenable_font_raises(self):
        with tempfile.TemporaryDirectory() as d:
            bad = Path(d) / "bad.ttf"
            bad.write_text("not a font")
            with self.assertRaises(FileNotFoundError):
                fonts.load_font(20, str(bad))
            with self.assertRaises(FileNotFoundError):
                fonts.find_font(str(bad))

    def test_no_path_still_falls_back(self):
        self.assertIsNotNone(fonts.load_font(20))


if __name__ == "__main__":
    unittest.main()


class ReplaceLineTest(unittest.TestCase):
    INK = (20, 30, 90)

    def setUp(self):
        self.font = fonts.find_font()
        self.bg = (235, 240, 245)
        self.img = Image.new("RGB", (500, 200), self.bg)
        self.box = (40, 60, 440, 120)
        old = patch.render_text("OLD TITLE HERE", self.font, 30, self.INK + (255,))
        patch.paste_text(self.img, old, (60, 100))
        self.old_bbox = patch.ink_bbox(self.img, self.box)

    def test_replaces_with_same_cap_height_and_ink_colour(self):
        out = patch.replace_line(self.img, self.box, "NEW LINE", self.font)
        new = patch.ink_bbox(out, self.box)
        self.assertIsNotNone(new)
        self.assertLessEqual(abs((new[3] - new[1]) - (self.old_bbox[3] - self.old_bbox[1])), 1)
        a = np.asarray(out).astype(int)
        sub = a[self.box[1]:self.box[3], self.box[0]:self.box[2]]
        # nothing darker than background outside the new glyph bbox
        mask = np.ones(sub.shape[:2], bool)
        mask[new[1] - self.box[1] - 2:new[3] - self.box[1] + 3, new[0] - self.box[0] - 2:new[2] - self.box[0] + 3] = False
        self.assertLess(np.abs(sub[mask] - np.array(self.bg)).max(), 3)
        darkest = sub.reshape(-1, 3)[sub.sum(axis=2).argmin()]
        self.assertLess(np.abs(darkest - np.array(self.INK)).max(), 25)
        # input untouched
        self.assertEqual(patch.ink_bbox(self.img, self.box), self.old_bbox)

    def test_explicit_fill_wins(self):
        out = patch.replace_line(self.img, self.box, "NEW", self.font, fill=(200, 0, 0))
        a = np.asarray(out).astype(int)[self.box[1]:self.box[3], self.box[0]:self.box[2]]
        self.assertGreater(a[..., 0].max() - a[..., 2].min(), 100)

    def test_too_wide_raises_and_squeeze_rescues_slight_overflow(self):
        with self.assertRaisesRegex(ValueError, "text wider than box"):
            patch.replace_line(self.img, self.box, "X" * 60, self.font)
        size = patch.size_for_cap(self.font, self.old_bbox[3] - self.old_bbox[1] + 1)
        f = ImageFont.truetype(self.font, size)
        avail = self.box[2] - self.box[0]
        text = "W"
        while f.getlength(text + "W") < avail:
            text += "W"
        while f.getlength(text) <= avail + 2:
            text += "i"
        n = len(text)
        w0 = f.getlength(text)
        self.assertLess(w0 - avail, 0.04 * size * (n - 1) - 2)
        with self.assertRaises(ValueError):
            patch.replace_line(self.img, self.box, text, self.font)
        out = patch.replace_line(self.img, self.box, text, self.font, squeeze=True)
        new = patch.ink_bbox(out, self.box)
        self.assertGreaterEqual(new[0], self.box[0])
        self.assertLessEqual(new[2], self.box[2])
        with self.assertRaises(ValueError):
            patch.replace_line(self.img, self.box, "X" * 60, self.font, squeeze=True)

    def test_no_ink_raises(self):
        with self.assertRaisesRegex(ValueError, "no ink in box"):
            patch.replace_line(self.img, (40, 140, 440, 190), "A", self.font)

    def test_align_right_keeps_right_edge(self):
        out = patch.replace_line(self.img, self.box, "SHORT", self.font, align="right")
        new = patch.ink_bbox(out, self.box)
        self.assertLessEqual(abs(new[2] - self.old_bbox[2]), 3)


class FillHelpersTest(unittest.TestCase):
    def test_lerp_fill_reproduces_horizontal_gradient(self):
        w, h = 300, 80
        ramp = np.linspace(40, 220, w)
        arr = np.tile(ramp[None, :, None], (h, 1, 3)).astype(np.uint8)
        img = Image.fromarray(arr)
        d = ImageDraw.Draw(img)
        d.rectangle((100, 20, 200, 60), fill=(0, 0, 0))
        out = patch.lerp_fill(img, (100, 20, 201, 61))
        err = np.abs(np.asarray(out).astype(int) - arr.astype(int))[20:61, 100:201]
        self.assertLess(err.max(), 8)

    def test_erase_between_flat_bg(self):
        img = Image.new("RGB", (100, 50), (10, 10, 10))
        out = patch.erase_between(img, (20, 10, 60, 30), bg=(200, 100, 50))
        self.assertEqual(out.getpixel((30, 20)), (200, 100, 50))
        self.assertEqual(out.getpixel((70, 20)), (10, 10, 10))

    def test_size_for_cap_monotonic_and_baseline(self):
        font = fonts.find_font()
        sizes = [patch.size_for_cap(font, c) for c in range(8, 60, 4)]
        self.assertEqual(sizes, sorted(sizes))
        self.assertGreater(sizes[-1], sizes[0])
        s = patch.size_for_cap(font, 30)
        b = patch.baseline_for_top(font, s, 100)
        self.assertLessEqual(abs((b - 100) - 30), 1)


def _logo_png(path):
    lg = Image.new("RGBA", (80, 40), (0, 0, 0, 0))
    ImageDraw.Draw(lg).rectangle([4, 4, 75, 35], fill=(10, 90, 160, 255))
    lg.save(path)


class WatermarkLogoGridTest(unittest.TestCase):
    def test_logo_mode_marks_several_separated_regions(self):
        with tempfile.TemporaryDirectory() as t:
            lp = Path(t) / "logo.png"
            _logo_png(lp)
            im = page((900, 600))
            out = watermark.mark(im, logo=str(lp), text="", corner_text="")
        diff = np.abs(np.asarray(out).astype(int) - np.asarray(im).astype(int)).max(axis=2) > 2
        self.assertGreater(diff.sum(), 0)
        # count blobs by coarse 150px cells that hold changes, then require spread
        cells = {(y // 150, x // 150) for y, x in zip(*np.nonzero(diff))}
        self.assertGreaterEqual(len(cells), 3)

    def test_grid_round_trip_light_and_dark(self):
        for im in (page(), page(colour=(20, 24, 40))):
            marked = watermark.mark(im, text="DECK", corner_text="", grid=(3, 4))
            self.assertGreater(np.abs(np.asarray(marked).astype(int) - np.asarray(im).astype(int)).max(), 5)
            back = watermark.unmark(marked, text="DECK", corner_text="", grid=(3, 4), dark=watermark.is_dark(im))
            err = np.abs(np.asarray(back).astype(int) - np.asarray(im).astype(int))
            self.assertLessEqual(err.max(), 2)

    def test_grid_places_text_in_every_cell(self):
        im = page((600, 800), (240, 240, 240))
        out = watermark.mark(im, text="DECK", corner_text="", grid=(3, 4))
        diff = np.abs(np.asarray(out).astype(int) - np.asarray(im).astype(int)).max(axis=2) > 2
        for r in range(4):
            for c in range(3):
                self.assertTrue(diff[r * 200:(r + 1) * 200, c * 200:(c + 1) * 200].any(), (r, c))

    def test_logo_unmark_refused(self):
        with self.assertRaisesRegex(ValueError, "logo watermark is not reversible"):
            watermark.unmark(page(), logo="x.png")

    def test_cli_pdf_with_watermark_logo(self):
        with tempfile.TemporaryDirectory() as t:
            src = Path(t) / "pages"
            src.mkdir()
            page((400, 300)).save(src / "01.png")
            lp = Path(t) / "logo.png"
            _logo_png(lp)
            out = Path(t) / "o.pdf"
            rc = _quiet_cli(["pdf", str(src), str(out), "--watermark-logo", str(lp)])
            self.assertEqual(rc, 0)
            self.assertTrue(out.read_bytes().startswith(b"%PDF"))

    def test_cli_pdf_grid_flag(self):
        with tempfile.TemporaryDirectory() as t:
            src = Path(t) / "pages"
            src.mkdir()
            page((400, 300)).save(src / "01.png")
            out = Path(t) / "o.pdf"
            self.assertEqual(_quiet_cli(["pdf", str(src), str(out), "--watermark", "X", "--grid", "3x4"]), 0)
            self.assertEqual(_quiet_cli(["pdf", str(src), str(out), "--watermark", "X", "--grid", "bad"]), 1)


def _ink_count(im, box, bg=(255, 255, 255)):
    arr = np.asarray(im.convert("RGB").crop(box)).astype(int)
    return int((np.abs(arr - np.array(bg)).sum(2) > 60).sum())


class BandOptionsTest(unittest.TestCase):
    def test_url_adds_ink_under_logo_and_grows_page(self):
        logo = Image.new("RGBA", (100, 40), (200, 0, 0, 255))
        plain = band.add_band(page((1000, 500)), "RAHASIA")
        with_url = band.add_band(page((1000, 500)), "RAHASIA", [logo], url="contoh.ai")
        b = int(1000 * 0.055)
        self.assertEqual(with_url.size, (1000, 500 + b))
        box = (800, 500 + int(b * 0.7), 1000, 500 + b)
        self.assertEqual(_ink_count(plain, box), 0)
        self.assertGreater(_ink_count(with_url, box), 0)

    def test_url_without_logos_sits_on_the_band_middle(self):
        # Header already carries the wordmark, so the band has no logo: the url line must
        # sit on the band's middle line, not low where it would hang under a missing logo.
        w, h = 2000, 1000
        b = int(w * 0.055)
        out = np.asarray(band.add_band(page((w, h)), "RAHASIA", [], url="www.contoh.ai", number=1, total=9).convert("RGB")).astype(int)
        strip = out[h:h + b, int(w * 0.55):int(w * 0.9)]
        rows = np.nonzero((np.abs(strip[3:] - strip[5, 5]).sum(2) > 60).any(1))[0] + 3   # skip the top rule
        self.assertGreater(len(rows), 0)
        centre = (rows.min() + rows.max()) / 2
        self.assertLess(abs(centre - b / 2), b * 0.08)

    def test_sub_line_adds_second_row_of_text(self):
        w, h = 1000, 500
        b = int(w * 0.095)
        one = band.add_band(page((w, h)), "Title", band_frac=0.095)
        two = band.add_band(page((w, h)), "Title", band_frac=0.095, sub="A short description line")
        low = (0, h + int(b * 0.62), int(w * 0.6), h + b)
        self.assertEqual(_ink_count(one, low), 0)
        self.assertGreater(_ink_count(two, low), 0)

    def test_long_text_shrinks_instead_of_running_under_logos(self):
        w, h = 1000, 500
        logo = Image.new("RGBA", (300, 100), (200, 0, 0, 255))
        out = band.add_band(page((w, h)), "W" * 40, [logo], band_frac=0.095, sub="W" * 70)
        a = np.asarray(out.convert("RGB")).astype(int)[h + 4:, :]
        red = (a[..., 0] > 180) & (a[..., 1] < 60)
        logo_left = int(np.nonzero(red.any(axis=0))[0].min())
        ink = (a.sum(axis=2) < 400) & ~red
        cols = np.nonzero(ink.any(axis=0))[0]
        self.assertLess(int(cols[cols < logo_left].max()), logo_left - 5)
        self.assertFalse(ink[:, logo_left:].any())

    def test_logo_with_opaque_white_margin_is_trimmed(self):
        # pci-logo.png is a 1600x1600 opaque white square with a small logo inside; the band drew
        # it at a fraction of the size of the other logos.
        lg = Image.new("RGBA", (1000, 1000), (255, 255, 255, 255))
        ImageDraw.Draw(lg).rectangle((400, 450, 600, 550), fill=(200, 0, 0, 255))
        self.assertEqual(band.trim(lg).size, (201, 101))

    def test_text_that_cannot_fit_raises(self):
        logo = Image.new("RGBA", (300, 100), (200, 0, 0, 255))
        with self.assertRaisesRegex(ValueError, "does not fit"):
            band.add_band(page((1000, 500)), "X", [logo], band_frac=0.095, sub="W" * 400)

    def test_secondary_frac_sets_second_logo_height(self):
        w, h = 1000, 500
        a = Image.new("RGBA", (100, 100), (200, 0, 0, 255))
        c = Image.new("RGBA", (100, 100), (0, 0, 200, 255))
        def blue_rows(frac):
            out = np.asarray(band.add_band(page((w, h)), "X", [a, c], band_frac=0.095,
                                           secondary_frac=frac).convert("RGB")).astype(int)
            blue = (out[..., 2] > 180) & (out[..., 0] < 60)
            return int(blue.any(axis=1).sum())
        self.assertGreater(blue_rows(0.7), blue_rows(0.34) + 20)

    def test_fit_canvas_letterboxes_before_band(self):
        out = band.add_band(Image.new("RGB", (900, 400), (10, 20, 30)), "X", fit_canvas=(1920, 1080))
        self.assertEqual(out.width, 1920)
        self.assertEqual(out.height, 1080 + int(1920 * 0.055))
        self.assertEqual(out.getpixel((5, 5)), (10, 20, 30))

    def test_number_drawn_right_end_only_when_given(self):
        w, h = 1000, 500
        b = int(w * 0.055)
        box = (int(w * 0.9), h + 2, w, h + b)
        without = band.add_band(page((w, h)), "X")
        with_n = band.add_band(page((w, h)), "X", number=3, total=10)
        self.assertEqual(_ink_count(without, box), 0)
        self.assertGreater(_ink_count(with_n, box), 0)

    def test_number_fmt(self):
        w, h = 1000, 500
        b = int(w * 0.055)
        box = (int(w * 0.8), h + 2, w, h + b)
        a = band.add_band(page((w, h)), "X", number=3, total=10)
        c = band.add_band(page((w, h)), "X", number=3, total=10, number_fmt="halaman {n} dari {total}")
        self.assertGreater(_ink_count(c, box), _ink_count(a, box))

    def test_cli_band_options(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            src, dst = t / "s", t / "d"
            src.mkdir()
            for n in ("01", "02"):
                page((400, 300)).save(src / f"{n}.png")
            rc = _quiet_cli(["band", str(src), str(dst), "--text", "X", "--url", "contoh.ai", "--numbers", "--approved",
                             "--number-fmt", "{n}/{total}", "--fit-canvas", "800x450"])
            self.assertEqual(rc, 0)
            self.assertEqual(Image.open(dst / "02.png").size, (800, 450 + int(800 * 0.055)))
            self.assertEqual(_quiet_cli(["band", str(src), str(dst), "--text", "X", "--fit-canvas", "bad"]), 1)


try:
    import pptx as _pptx  # noqa: F401
    HAVE_PPTX = True
except ImportError:
    HAVE_PPTX = False


@unittest.skipUnless(HAVE_PPTX, "python-pptx not importable (use the gaspol-video venv python)")
class PptxOptionsTest(unittest.TestCase):
    def _imgs(self, t, n=2):
        paths = []
        for i in range(n):
            p = Path(t) / f"{i + 1:02d}.png"
            page((400, 225)).save(p)
            paths.append(p)
        return paths

    def _zip(self, out):
        import zipfile
        return zipfile.ZipFile(out)

    def test_fade_transition_in_slide_xml(self):
        from tools.deckkit import pptx as dk
        with tempfile.TemporaryDirectory() as t:
            out = Path(t) / "o.pptx"
            self.assertEqual(dk.build_pptx(self._imgs(t), out, transition="fade"), 2)
            z = self._zip(out)
            xml = z.read("ppt/slides/slide1.xml").decode()
            self.assertIn("<p:transition", xml)
            self.assertIn("<p:fade", xml)
            plain = Path(t) / "p.pptx"
            dk.build_pptx(self._imgs(t), plain)
            self.assertNotIn("<p:transition", self._zip(plain).read("ppt/slides/slide1.xml").decode())

    def test_bad_transition_raises(self):
        from tools.deckkit import pptx as dk
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(ValueError):
                dk.build_pptx(self._imgs(t), Path(t) / "o.pptx", transition="wipe")

    def test_jpeg_quality_stores_jpeg(self):
        from tools.deckkit import pptx as dk
        with tempfile.TemporaryDirectory() as t:
            out = Path(t) / "o.pptx"
            dk.build_pptx(self._imgs(t), out, jpeg_quality=92)
            media = [n for n in self._zip(out).namelist() if n.startswith("ppt/media/")]
            self.assertTrue(media)
            self.assertTrue(all(n.lower().endswith((".jpg", ".jpeg")) for n in media), media)

    def test_cli_pptx_options(self):
        with tempfile.TemporaryDirectory() as t:
            out = Path(t) / "o.pptx"
            rc = _quiet_cli(["pptx", str(out), *map(str, self._imgs(t)), "--transition", "fade", "--jpeg-quality", "90"])
            self.assertEqual(rc, 0)
            self.assertIn("<p:fade", self._zip(out).read("ppt/slides/slide1.xml").decode())

    def test_fit_image_matches_page_aspect(self):
        # pages with a footer band are taller than 16:9; forcing 16:9 squashes them
        from pptx import Presentation
        from tools.deckkit import pptx as dk
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "01.png"
            page((2048, 1264)).save(p)
            out = Path(t) / "o.pptx"
            dk.build_pptx([p], out, fit_image=True)
            prs = Presentation(str(out))
            self.assertAlmostEqual(prs.slide_width / prs.slide_height, 2048 / 1264, places=3)
            pic = prs.slides[0].shapes[0]
            self.assertEqual((pic.width, pic.height), (prs.slide_width, prs.slide_height))

    def test_fit_image_rejects_mixed_aspects(self):
        from tools.deckkit import pptx as dk
        with tempfile.TemporaryDirectory() as t:
            a, b = Path(t) / "01.png", Path(t) / "02.png"
            page((2048, 1264)).save(a)
            page((1920, 1080)).save(b)
            with self.assertRaises(ValueError):
                dk.build_pptx([a, b], Path(t) / "o.pptx", fit_image=True)

    def test_cli_fit_image(self):
        from pptx import Presentation
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "01.png"
            page((2048, 1264)).save(p)
            out = Path(t) / "o.pptx"
            self.assertEqual(_quiet_cli(["pptx", str(out), str(p), "--fit-image"]), 0)
            prs = Presentation(str(out))
            self.assertAlmostEqual(prs.slide_width / prs.slide_height, 2048 / 1264, places=3)


class EmblemFillSideTest(unittest.TestCase):
    def setUp(self):
        self.font = fonts.find_font()

    def test_emblem_text_round_glow_lettering(self):
        em = patch.emblem_text("MONI", self.font, 40, (255, 255, 255), (0, 160, 255), ring=(0, 200, 255))
        self.assertEqual(em.mode, "RGBA")
        self.assertEqual(em.width, em.height)
        a = np.asarray(em)
        self.assertEqual(a[0, 0, 3], 0)  # corner outside the circle is transparent
        c = em.width // 2
        self.assertGreater(a[c - 40:c + 40, c - 40:c + 40, 3].max(), 200)  # lettering inside
        self.assertTrue((a[..., 3] > 200).any())

    def test_emblem_text_ring_optional_and_rejects_bad_font(self):
        plain = patch.emblem_text("M", self.font, 30, (255, 255, 255), (0, 160, 255))
        ringed = patch.emblem_text("M", self.font, 30, (255, 255, 255), (0, 160, 255), ring=(255, 0, 0))
        self.assertNotEqual(np.asarray(plain).tobytes(), np.asarray(ringed).tobytes())
        with self.assertRaises(FileNotFoundError):
            patch.emblem_text("M", "/nonexistent/none.ttf", 30, (255, 255, 255), (0, 160, 255))

    def test_fill_from_side_each_side(self):
        for side, probe, src in (("left", (50, 40), (25, 40)), ("right", (50, 40), (75, 40)),
                                 ("top", (50, 40), (50, 15)), ("bottom", (50, 40), (50, 65))):
            im = Image.new("RGB", (100, 80), (0, 0, 0))
            d = ImageDraw.Draw(im)
            for i in range(100):
                d.line([(i, 0), (i, 79)], fill=(i, 100, 0))   # horizontal gradient
            for j in range(80):
                if side in ("top", "bottom"):
                    d.line([(0, j), (99, j)], fill=(j * 3, 0, 50))
            box = (30, 20, 70, 60)
            ref = im.getpixel({"left": (29, 40), "right": (70, 40), "top": (50, 19), "bottom": (50, 60)}[side])
            out = patch.fill_from_side(im, box, side)
            self.assertIs(out, im)
            self.assertEqual(im.getpixel(probe), ref)

    def test_fill_from_side_errors(self):
        im = Image.new("RGB", (100, 80))
        with self.assertRaisesRegex(ValueError, "side"):
            patch.fill_from_side(im, (30, 20, 70, 60), "middle")
        with self.assertRaisesRegex(ValueError, "no pixels"):
            patch.fill_from_side(im, (0, 20, 40, 60), "left")


@unittest.skipUnless(HAVE_CV, "cv2 not importable (use the gaspol-video venv python)")
class PixelSlotsTest(unittest.TestCase):
    RECT = [(100, 80), (400, 80), (400, 300), (100, 300)]
    OCC = (150, 150, 200, 250)
    OCC_COLOUR = (10, 200, 10)

    def _page(self):
        im = _magenta_page([self.RECT])
        ImageDraw.Draw(im).rectangle(self.OCC, fill=self.OCC_COLOUR)
        return im

    def test_occluder_stays_in_front_of_logo(self):
        im = self._page()
        quad = slots.find_slots(im, key="magenta")[0]
        logo = Image.new("RGBA", (300, 220), (255, 255, 255, 255))
        out = slots.paste_quad(im, logo, quad, mode="pixel", fit=1.0)
        self.assertEqual(out.getpixel((175, 200)), self.OCC_COLOUR)   # occluder kept
        self.assertEqual(out.getpixel((300, 190)), (255, 255, 255))  # logo shows elsewhere
        flat = slots.paste_quad(im, logo, quad, fit=1.0)
        self.assertEqual(flat.getpixel((175, 200)), (255, 255, 255))  # flat mode covers it

    def test_fill_slots_pixel_requires_magenta(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "l.png"
            Image.new("RGBA", (50, 20), (255, 0, 0, 255)).save(p)
            with self.assertRaisesRegex(ValueError, "magenta"):
                slots.fill_slots(self._page(), [p], key="white", mode="pixel")
            out, quads = slots.fill_slots(self._page(), [p], key="magenta", mode="pixel")
            self.assertEqual(len(quads), 1)
            self.assertEqual(out.getpixel((175, 200)), self.OCC_COLOUR)

    def test_paste_quad_bad_mode(self):
        im = self._page()
        quad = slots.find_slots(im, key="magenta")[0]
        with self.assertRaisesRegex(ValueError, "mode"):
            slots.paste_quad(im, Image.new("RGBA", (5, 5)), quad, mode="nope")

    def test_cli_pixel_mode(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            self._page().save(t / "p.png")
            Image.new("RGBA", (300, 220), (255, 0, 0, 255)).save(t / "l.png")
            rc = _quiet_cli(["logo-slots", str(t / "p.png"), str(t / "l.png"), "--key", "magenta", "--mode", "pixel"])
            self.assertEqual(rc, 0)
            self.assertEqual(Image.open(t / "p.png").convert("RGB").getpixel((175, 200)), self.OCC_COLOUR)


class ReplaceBlockTest(unittest.TestCase):
    INK = (20, 30, 90)

    def setUp(self):
        self.font = fonts.find_font()
        self.bg = (235, 240, 245)
        self.img = Image.new("RGB", (500, 260), self.bg)
        self.box = (40, 40, 460, 240)
        for i, t in enumerate(("OLD LINE ONE", "OLD LINE TWO")):
            patch.paste_text(self.img, patch.render_text(t, self.font, 24, self.INK + (255,)), (60, 80 + i * 34))
        self.old = patch.ink_bbox(self.img, self.box)

    def test_more_lines_than_before_same_corner_and_colour(self):
        out = patch.replace_block(self.img, self.box, ["NEW ONE", "NEW TWO", "NEW THREE", "NEW FOUR"],
                                  self.font, max_size=24)
        new = patch.ink_bbox(out, self.box)
        self.assertLessEqual(abs(new[0] - self.old[0]), 3)
        self.assertLessEqual(abs(new[1] - self.old[1]), 4)
        self.assertGreater(new[3] - new[1], self.old[3] - self.old[1])
        a = np.asarray(out).astype(int)[self.box[1]:self.box[3], self.box[0]:self.box[2]].reshape(-1, 3)
        self.assertLess(np.abs(a[a.sum(1).argmin()] - np.array(self.INK)).max(), 25)
        self.assertEqual(patch.ink_bbox(self.img, self.box), self.old)

    def test_light_ink_on_dark_ground(self):
        img = Image.new("RGB", (400, 160), (15, 30, 55))
        patch.paste_text(img, patch.render_text("OLD", self.font, 24, (255, 255, 255, 255)), (30, 60))
        out = patch.replace_block(img, (20, 20, 380, 150), ["A", "B"], self.font, dark=False, max_size=20)
        a = np.asarray(out).astype(int)[20:150, 20:380].reshape(-1, 3)
        self.assertGreater(a.sum(1).max(), 600)

    def test_cap_from_ink_matches_old_height(self):
        img = Image.new("RGB", (400, 160), self.bg)
        patch.paste_text(img, patch.render_text("500", self.font, 60, self.INK + (255,)), (30, 120))
        old = patch.ink_bbox(img, (20, 20, 380, 150))
        out = patch.replace_block(img, (20, 20, 380, 150), ["750"], self.font, cap_from_ink=True)
        new = patch.ink_bbox(out, (20, 20, 380, 150))
        self.assertLessEqual(abs((new[3] - new[1]) - (old[3] - old[1])), 3)
        self.assertLessEqual(abs(new[1] - old[1]), 3)
        with self.assertRaisesRegex(ValueError, "old ink height"):
            patch.replace_block(img, (20, 20, 380, 150), ["750"], self.font, cap_from_ink=True, width=20)

    def test_missing_glyph_raises_instead_of_printing_a_box(self):
        # A font without U+2192 used to print a hollow box silently (eyebrow "SEBELUM → SESUDAH").
        cps = patch.missing_glyphs(self.font, "A\U0010FFFD")
        self.assertEqual(cps, ["\U0010FFFD"])
        with self.assertRaisesRegex(ValueError, "no glyph"):
            patch.replace_block(self.img, self.box, ["NEW \U0010FFFD"], self.font, max_size=24)
        with self.assertRaisesRegex(ValueError, "no glyph"):
            patch.replace_line(self.img, self.box, "NEW \U0010FFFD", self.font)

    def test_align_center_keeps_old_centre(self):
        img = Image.new("RGB", (400, 160), self.bg)
        patch.paste_text(img, patch.render_text("WWWWW", self.font, 40, self.INK + (255,)), (30, 110))
        old = patch.ink_bbox(img, (20, 20, 380, 150))
        out = patch.replace_block(img, (20, 20, 380, 150), ["ii"], self.font, cap_from_ink=True, align="center")
        new = patch.ink_bbox(out, (20, 20, 380, 150))
        self.assertLessEqual(abs((new[0] + new[2]) - (old[0] + old[2])) / 2, 4)
        with self.assertRaisesRegex(ValueError, "align"):
            patch.replace_block(img, (20, 20, 380, 150), ["x"], self.font, align="middle")

    def test_stretch_to_ink_fills_old_width(self):
        img = Image.new("RGB", (400, 160), self.bg)
        patch.paste_text(img, patch.render_text("WWWWW", self.font, 40, self.INK + (255,)), (30, 110))
        old = patch.ink_bbox(img, (20, 20, 380, 150))
        out = patch.replace_block(img, (20, 20, 380, 150), ["111"], self.font, cap_from_ink=True,
                                  stretch_to_ink=True)
        new = patch.ink_bbox(out, (20, 20, 380, 150))
        self.assertLessEqual(abs(new[0] - old[0]), 3)
        self.assertLessEqual(abs(new[2] - old[2]), 3)
        self.assertLessEqual(abs(new[1] - old[1]), 3)
        with self.assertRaisesRegex(ValueError, "one line"):
            patch.replace_block(img, (20, 20, 380, 150), ["1", "2"], self.font, stretch_to_ink=True)

    def test_thr_finds_mid_tone_light_ink(self):
        img = Image.new("RGB", (400, 160), (15, 30, 55))
        patch.paste_text(img, patch.render_text("RP 1,2", self.font, 40, (200, 140, 40, 255)), (30, 90))
        with self.assertRaisesRegex(ValueError, "no ink"):
            patch.replace_block(img, (20, 20, 380, 150), ["RP 1,45"], self.font, dark=False, max_size=40)
        out = patch.replace_block(img, (20, 20, 380, 150), ["RP 1,45"], self.font, dark=False, max_size=40, thr=100)
        a = np.asarray(out).astype(int)[20:150, 20:380].reshape(-1, 3)
        top = a[a.sum(1).argmax()]
        self.assertLess(np.abs(top - np.array((200, 140, 40))).max(), 30)

    def test_shrinks_to_width_and_raises_when_impossible(self):
        out = patch.replace_block(self.img, self.box, ["W" * 30], self.font, max_size=40)
        new = patch.ink_bbox(out, self.box)
        self.assertLessEqual(new[2], self.box[2])
        with self.assertRaisesRegex(ValueError, "text wider"):
            patch.replace_block(self.img, self.box, ["W" * 200], self.font, min_size=12)

    def test_overflow_bottom_and_no_ink_raise(self):
        with self.assertRaisesRegex(ValueError, "past the bottom"):
            patch.replace_block(self.img, self.box, ["X"] * 20, self.font, max_size=24, min_size=24)
        with self.assertRaisesRegex(ValueError, "no ink"):
            patch.replace_block(self.img, (40, 200, 460, 250), ["A"], self.font)


class RetypeTest(unittest.TestCase):
    def setUp(self):
        import os, tempfile
        self.dir = tempfile.mkdtemp()
        self.font = fonts.find_font()
        img = Image.new("RGB", (400, 200), (240, 240, 240))
        patch.paste_text(img, patch.render_text("OLD", self.font, 24, (20, 20, 20, 255)), (30, 60))
        img.save(os.path.join(self.dir, "a.png"))
        self.fix = {"src": "a.png", "dst": "b.png", "box": [20, 20, 380, 190], "lines": ["NEW", "TWO"],
                    "max_size": 24}

    def test_writes_dst_relative_to_base(self):
        import os
        out = patch.retype({"font": self.font, "fixes": [self.fix]}, self.dir)
        self.assertEqual(out, [os.path.abspath(os.path.join(self.dir, "b.png"))])
        self.assertTrue(os.path.exists(out[0]))

    def test_fixes_chain_on_one_page(self):
        import os
        img = Image.open(os.path.join(self.dir, "a.png"))
        patch.paste_text(img, patch.render_text("LOW", self.font, 24, (20, 20, 20, 255)), (30, 170))
        img.save(os.path.join(self.dir, "a.png"))
        f1 = dict(self.fix, box=[20, 20, 380, 120], dst="b.png")
        f2 = {"src": "b.png", "dst": "b.png", "box": [20, 140, 380, 195], "lines": ["NEW LOW"], "max_size": 24}
        out = patch.retype({"font": self.font, "fixes": [f1, f2]}, self.dir)
        self.assertEqual(out, [os.path.abspath(os.path.join(self.dir, "b.png"))])
        res = Image.open(out[0])
        self.assertIsNotNone(patch.ink_bbox(res, (20, 20, 380, 120)))
        self.assertIsNotNone(patch.ink_bbox(res, (20, 140, 380, 195)))

    def test_add_fix_writes_new_lines_into_an_empty_box(self):
        """2026-11-01 forklift slide 7: a missing sentence had to go into blank space; every
        retype fix measured old ink first and refused an empty box."""
        import os
        fix = {"src": "a.png", "dst": "n.png", "box": [20, 110, 380, 195], "lines": ["Start lewat", "aplikasi"],
               "add": {"size": 22, "fill": [21, 33, 43]}}
        out = patch.retype({"font": self.font, "fixes": [fix]}, self.dir)
        bb = patch.ink_bbox(Image.open(out[0]), (20, 110, 380, 195))
        self.assertIsNotNone(bb)
        self.assertGreaterEqual(bb[0], 20)
        self.assertLessEqual(bb[3], 195)

    def test_add_fix_checks_fit_and_options(self):
        bad = [{"add": {"size": 22}},                                   # no fill
               {"add": {"size": 60, "fill": [0, 0, 0]}},               # runs past the box
               {"add": {"size": 22, "fill": [0, 0, 0], "spin": 1}}]    # unknown option
        for extra in bad:
            fix = {"src": "a.png", "dst": "n.png", "box": [20, 110, 200, 160], "lines": ["Start lewat aplikasi"]}
            fix.update(extra)
            with self.assertRaises(ValueError):
                patch.retype({"font": self.font, "fixes": [fix]}, self.dir)

    def test_erase_fix_wipes_box(self):
        import os
        out = patch.retype({"fixes": [{"src": "a.png", "dst": "e.png", "box": [20, 40, 200, 100], "erase": True}]}, self.dir)
        self.assertIsNone(patch.ink_bbox(Image.open(out[0]), (20, 40, 200, 100)))
        with self.assertRaisesRegex(ValueError, "no lines"):
            patch.retype({"fixes": [{"src": "a.png", "dst": "e.png", "box": [20, 40, 200, 100], "erase": True,
                                     "lines": ["x"]}]}, self.dir)

    def test_bad_fix_writes_nothing(self):
        import os
        bad = dict(self.fix, dst="c.png", box=[20, 150, 380, 190])
        with self.assertRaisesRegex(ValueError, "fix 1"):
            patch.retype({"font": self.font, "fixes": [self.fix, bad]}, self.dir)
        self.assertFalse(os.path.exists(os.path.join(self.dir, "b.png")))
        with self.assertRaisesRegex(ValueError, "unknown keys"):
            patch.retype({"fixes": [dict(self.fix, colour=1)]}, self.dir)
        with self.assertRaisesRegex(ValueError, "no fixes"):
            patch.retype({}, self.dir)


class PasteQuadsTest(unittest.TestCase):
    def setUp(self):
        import os, tempfile
        self.dir = tempfile.mkdtemp()
        Image.new("RGB", (300, 200), (200, 200, 200)).save(os.path.join(self.dir, "a.png"))
        Image.new("RGB", (60, 20), (200, 0, 0)).save(os.path.join(self.dir, "logo.png"))
        self.spec = {"src": "a.png", "dst": "b.png", "logo": "logo.png", "plate": [255, 255, 255],
                     "quads": [[[20, 20], [140, 40], [140, 90], [20, 70]]]}

    def test_pastes_logo_on_plate_inside_quad(self):
        import os
        out = slots.paste_quads(self.spec, self.dir)
        a = np.asarray(Image.open(out)).astype(int)
        self.assertGreater(a[50, 80, 0] - a[50, 80, 2], 100)   # logo red in the middle
        self.assertEqual(tuple(a[150, 250]), (200, 200, 200))   # outside untouched
        self.assertTrue(os.path.exists(os.path.join(self.dir, "b.png")))

    def test_bad_quads_raise_before_writing(self):
        import os
        with self.assertRaisesRegex(ValueError, "outside"):
            slots.paste_quads(dict(self.spec, quads=[[[20, 20], [400, 40], [140, 90], [20, 70]]]), self.dir)
        with self.assertRaisesRegex(ValueError, "4"):
            slots.paste_quads(dict(self.spec, quads=[[[20, 20], [140, 40], [140, 90]]]), self.dir)
        self.assertFalse(os.path.exists(os.path.join(self.dir, "b.png")))

    def test_shade_and_multiply_follow_the_body(self):
        import os
        img = Image.new("RGB", (300, 200), (240, 240, 240))
        for x in range(80, 140):
            for y in range(0, 200):
                img.putpixel((x, y), (150, 150, 150))   # shadow band across the right half of the quad
        img.save(os.path.join(self.dir, "a.png"))
        Image.new("RGB", (60, 20), (200, 200, 200)).save(os.path.join(self.dir, "logo.png"))
        spec = dict(self.spec, plate=None, multiply=True, shade=True, fit=1.0)
        a = np.asarray(Image.open(slots.paste_quads(spec, self.dir))).astype(int)
        # a grey logo multiplied into the body keeps the body's light and shadow under it
        self.assertLessEqual(abs(a[55, 60, 0] - 240 * 200 // 255), 8)
        self.assertLess(a[55, 110, 0] / a[55, 60, 0], 0.75)

    def test_per_quad_options_override(self):
        spec = dict(self.spec, plate=None, quads=[{"quad": self.spec["quads"][0], "plate": [0, 0, 255]}])
        a = np.asarray(Image.open(slots.paste_quads(spec, self.dir))).astype(int)
        self.assertGreater(a[30, 40, 2] - a[30, 40, 0], 100)   # blue plate from the quad's own option
        with self.assertRaisesRegex(ValueError, "unknown keys"):
            slots.paste_quads(dict(self.spec, quads=[{"quad": self.spec["quads"][0], "colour": 1}]), self.dir)


    def test_pixel_mode_and_no_trim_for_an_app_screen(self):
        # A phone screen drawn magenta with rounded corners and a forklift in front: the app
        # screenshot fills the quad but lands only on magenta pixels. Its light-grey margin
        # (241) is part of the screen, so trim=false keeps it instead of cropping it as "white".
        import os
        img = Image.new("RGB", (300, 200), (30, 30, 30))
        for x in range(20, 141):
            for y in range(20, 181):
                img.putpixel((x, y), (255, 0, 255))
        for x in range(100, 160):
            for y in range(120, 200):
                img.putpixel((x, y), (220, 90, 30))      # forklift in front of the screen
        img.putpixel((20, 20), (30, 30, 30))            # rounded corner: bezel, not screen
        img.save(os.path.join(self.dir, "a.png"))
        app = Image.new("RGB", (121, 161), (241, 245, 249))
        for x in range(0, 121):
            for y in range(0, 30):
                app.putpixel((x, y), (15, 23, 42))       # navy header
        app.save(os.path.join(self.dir, "app.png"))
        spec = {"src": "a.png", "dst": "b.png", "logo": "app.png", "plate": None, "fit": 1.0,
                "mode": "pixel", "trim": False, "quads": [[[20, 20], [140, 20], [140, 180], [20, 180]]]}
        a = np.asarray(Image.open(slots.paste_quads(spec, self.dir))).astype(int)
        self.assertEqual(tuple(a[150, 120]), (220, 90, 30))   # forklift stays in front
        self.assertEqual(tuple(a[20, 20]), (30, 30, 30))      # rounded corner stays bezel
        self.assertLess(a[25, 60].sum(), 120)                 # navy header at the very top
        self.assertGreater(a[100, 23].min(), 230)             # light margin reaches the left edge
        with self.assertRaisesRegex(ValueError, "mode"):
            slots.paste_quads(dict(spec, mode="blend"), self.dir)

class BandUrlColourTest(unittest.TestCase):
    def test_url_colour_used(self):
        page = Image.new("RGB", (800, 450), (240, 240, 240))
        logo = Image.new("RGBA", (80, 20), (0, 0, 0, 255))
        out = band.add_band(page, "RAHASIA", [logo], url="www.x.ai", url_colour=(35, 133, 127))
        a = np.asarray(out).astype(int)[450:, 600:]
        teal = ((a[..., 1] - a[..., 0] > 60) & (a[..., 2] - a[..., 0] > 50)).sum()
        self.assertGreater(teal, 5)


class ComposeTest(unittest.TestCase):
    def setUp(self):
        import os, tempfile
        self.dir = tempfile.mkdtemp()
        im = Image.new("RGB", (800, 400), (240, 240, 240))
        d = ImageDraw.Draw(im)
        d.rectangle((100, 300, 180, 340), fill=(255, 0, 255))   # left store slot
        d.rectangle((200, 300, 280, 340), fill=(255, 0, 255))   # right store slot
        d.rectangle((500, 80, 700, 180), fill=(255, 0, 255))    # big slot
        im.save(os.path.join(self.dir, "page.png"))
        Image.new("RGB", (90, 40), (0, 0, 0)).save(os.path.join(self.dir, "black.png"))
        Image.new("RGB", (90, 40), (0, 0, 200)).save(os.path.join(self.dir, "blue.png"))

    def plan(self, ops, **kw):
        return dict({"src": "page.png", "dst": "out.png", "ops": ops}, **kw)

    def test_flat_logos_keep_their_own_ground_and_leave_no_magenta(self):
        import os
        dst, n, left = compose.run(self.plan([
            {"op": "logo", "slot": {"sort": "area", "index": 0}, "file": "black.png", "fit": 1.0},
            {"op": "logo", "slot": {"sort": "x", "index": 0}, "file": "black.png", "fit": 0.6},
            {"op": "logo", "slot": {"sort": "x", "index": 1}, "file": "blue.png", "fit": 0.6}],
            expect_slots=3), self.dir)
        a = np.asarray(Image.open(dst)).astype(int)
        self.assertEqual(n, 3)
        self.assertEqual(left, 0)
        # right store slot's edge is the page ground, not the black logo pasted beside it
        self.assertGreater(a[302, 204].sum(), 600)
        self.assertGreater(a[320, 240, 2] - a[320, 240, 0], 150)

    def test_text_font_resolves_against_plan_folder(self):
        import os, shutil
        shutil.copy(fonts.find_font(), os.path.join(self.dir, "plan-font.ttf"))
        dst, _, _ = compose.run(self.plan([
            {"op": "whiten", "colour": [240, 240, 240]},
            {"op": "text", "xy": [60, 60], "text": "5,0", "font": "plan-font.ttf", "size": 30}]), self.dir)
        self.assertTrue(os.path.exists(dst))

    def test_logo_slanted_slot_at_page_edge(self):
        # A truck side running off the right edge: the slope scan must stay inside the page.
        import os
        im = Image.new("RGBA", (300, 200), (90, 120, 160, 255))
        ImageDraw.Draw(im).polygon([(200, 60), (299, 50), (299, 110), (200, 120)], fill=(255, 0, 255, 255))
        compose.logo_slanted(im, {"box": (200, 50, 299, 120)}, os.path.join(self.dir, "black.png"))
        self.assertEqual(im.size, (300, 200))

    def test_slot_count_checked_and_unknown_op_rejected(self):
        with self.assertRaisesRegex(ValueError, "found 3"):
            compose.run(self.plan([], expect_slots=2), self.dir)
        with self.assertRaisesRegex(ValueError, "unknown op"):
            compose.run(self.plan([{"op": "sparkle"}]), self.dir)
        with self.assertRaisesRegex(ValueError, "out of range"):
            compose.run(self.plan([{"op": "logo", "slot": {"index": 9}, "file": "black.png"}]), self.dir)

    def test_flag_card_text_stars_image_draw(self):
        import os
        dst, _, left = compose.run(self.plan([
            {"op": "whiten", "colour": [240, 240, 240]},
            {"op": "card", "box": [20, 20, 300, 200]},
            {"op": "flag", "country": "sg", "center": [400, 60], "width": 60},
            {"op": "stars", "center": [60, 150], "count": 3},
            {"op": "text", "xy": [60, 60], "text": "5,0", "font": fonts.find_font(), "size": 30},
            {"op": "image", "file": "blue.png", "xy": [600, 250], "height": 40}]), self.dir)
        a = np.asarray(Image.open(dst)).astype(int)
        self.assertEqual(left, 0)
        self.assertGreater(a[50, 400, 0] - a[50, 400, 2], 100)   # red top half of the flag
        self.assertGreater(a[150, 60, 0] - a[150, 60, 2], 100)   # yellow star
        self.assertGreater(a[260, 620, 2] - a[260, 620, 0], 150)
        with self.assertRaisesRegex(ValueError, "no built-in"):
            compose.flag(Image.new("RGBA", (100, 100)), "xx", (50, 50))

    def test_whiten_dark_fringe_paints_purple_edge_on_dark_bezel(self):
        # Magenta anti-aliased into a dark phone bezel leaves dark purple (60,5,75), which the
        # light pink test (r > 150) misses. dark_fringe catches it inside the box only.
        im = Image.new("RGBA", (40, 20), (20, 24, 30, 255))
        px = im.load()
        px[5, 5] = (60, 5, 75, 255)      # dark fringe inside the box
        px[30, 5] = (60, 5, 75, 255)     # same colour outside the box: untouched
        px[6, 6] = (40, 120, 120, 255)   # teal glow: untouched
        compose.whiten(im, (20, 24, 30), box=(0, 0, 20, 20))
        self.assertEqual(px[5, 5][:3], (60, 5, 75))          # default stays as before
        compose.whiten(im, (20, 24, 30), box=(0, 0, 20, 20), dark_fringe=True)
        self.assertEqual(px[5, 5][:3], (20, 24, 30))
        self.assertEqual(px[30, 5][:3], (60, 5, 75))
        self.assertEqual(px[6, 6][:3], (40, 120, 120))

    def test_then_resorts_a_slice(self):
        slots = [dict(cx=x, cy=y, area=1) for x, y in ((300, 100), (500, 300), (100, 310))]
        got = compose.select(slots, {"sort": "y", "from": 1, "then": "x", "index": 0})
        self.assertEqual(got[0]["cx"], 100)


class TableFurnitureTest(unittest.TestCase):
    MD = """## 25 — PERBANDINGAN

**Kicker** — PERBANDINGAN · KAMI DAN DIA

**Headline** — Kami memperkuat, bukan mengganti.

**Sub** — sistem yang ada tetap dipakai

| | Kami | Dia |
|---|---|---|
| Ban | Ada | Tidak ada |
| Peta | Ada | Ada |

- Catatan satu.

**Pita** — DIPERKUAT, BUKAN DIGANTI
<!-- catatan: tidak ikut -->

## 26 — LAIN
"""

    def test_spec_from_md_reads_every_part(self):
        from tools.deckkit import table
        spec = table.spec_from_md(self.MD, 25)
        self.assertEqual(spec["columns"], ["", "Kami", "Dia"])
        self.assertEqual(len(spec["rows"]), 2)
        self.assertEqual(spec["ribbon"], "DIPERKUAT, BUKAN DIGANTI")
        self.assertEqual(spec["notes"], ["Catatan satu."])
        with self.assertRaisesRegex(ValueError, "no '## 99"):
            table.spec_from_md(self.MD, 99)

    def test_wide_column_wraps_at_its_own_width(self):
        # A wide column must not wrap at the width of the narrowest column.
        from tools.deckkit import table
        long = "Memeriksa gambar call dari enam belas line dan memutuskan PASS"
        spec = {"title": "T", "columns": ["A", "B", "C"], "widths": [0.12, 0.76, 0.12],
                "rows": [["x", long, "y"]]}
        boxes = table._layout(spec, (2752, 1536), None)
        self.assertEqual(len(boxes["cells"][(0, 1)]), 1)

    def test_highlight_rule_ribbon_draw(self):
        from tools.deckkit import table
        spec = table.spec_from_md(self.MD, 25)
        spec.update(highlight=1, widths=[0.3, 0.35, 0.35],
                    mark_rule={"col": 2, "equals": "Tidak ada", "bad": [2], "good": [1]})
        im = table.render(spec, size=(1376, 768))
        a = np.asarray(im).astype(int)
        self.assertGreater(a[-10, 680, 1] - a[-10, 680, 0], 60)          # teal ribbon at the bottom
        boxes = table.cell_boxes(spec, size=(1376, 768))
        x0, y0, x1, y1 = boxes[(0, 2)]
        bad = a[y1 - 4, x1 - 6]
        self.assertGreater(bad[0] - bad[1], 15)                           # "Tidak ada" cell is red
        with self.assertRaisesRegex(ValueError, "widths"):
            table.render(dict(spec, widths=[0.5, 0.5]), size=(1376, 768))


class BandMapTest(unittest.TestCase):
    def test_map_json_names_pages(self):
        import json, os, subprocess, sys, tempfile
        d = tempfile.mkdtemp()
        os.makedirs(os.path.join(d, "renders"))
        Image.new("RGB", (400, 225), (240, 240, 240)).save(os.path.join(d, "renders", "a.png"))
        os.makedirs(os.path.join(d, "tools"))
        json.dump({"01": "renders/a.png"}, open(os.path.join(d, "tools", "pilih.json"), "w"))
        root = Path(__file__).resolve().parents[2]
        r = subprocess.run([sys.executable, "-m", "tools.deckkit", "band", os.path.join(d, "tools", "pilih.json"),
                            os.path.join(d, "out"), "--text", "RAHASIA", "--prefix", "slide-"], cwd=root,
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(os.path.exists(os.path.join(d, "out", "slide-01.png")))


class SignTest(unittest.TestCase):
    def test_sign_places_images_at_anchor_and_keeps_text(self):
        try:
            import pymupdf
        except ImportError:
            self.skipTest('needs pymupdf')
        from tools.deckkit import sign
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            doc = pymupdf.open()
            doc.new_page().insert_text((72, 100), 'Budi Santoso di badan surat')
            doc.new_page().insert_text((300, 500), 'Budi Santoso')
            doc.save(d / 'surat.pdf')
            im = Image.new('RGB', (200, 100), 'white')
            ImageDraw.Draw(im).line((10, 90, 190, 10), fill='black', width=6)
            im.save(d / 'ttd.jpg')
            placed = sign.sign({'src': 'surat.pdf', 'dst': 'out/ttd.pdf',
                                'items': [{'image': 'ttd.jpg', 'anchor': 'Budi Santoso',
                                           'dx': 0, 'dy': -50, 'width': 100, 'opacity': 0.8,
                                           'trim': False}]}, base=d)
            self.assertEqual(placed[0][0], 2)  # last page holding the anchor, not the body mention
            x0, y0, x1, y1 = placed[0][1]
            self.assertAlmostEqual(x1 - x0, 100, places=0)
            self.assertAlmostEqual(y1 - y0, 50, places=0)
            out = pymupdf.open(d / 'out/ttd.pdf')
            self.assertEqual(len(out[1].get_images()), 1)
            self.assertEqual(len(out[0].get_images()), 0)
            self.assertIn('Budi Santoso', out[1].get_text())

    def test_sign_missing_anchor_raises(self):
        try:
            import pymupdf
        except ImportError:
            self.skipTest('needs pymupdf')
        from tools.deckkit import sign
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            doc = pymupdf.open(); doc.new_page().insert_text((72, 100), 'tanpa nama'); doc.save(d / 's.pdf')
            Image.new('RGB', (10, 10), 'black').save(d / 'x.png')
            with self.assertRaises(ValueError):
                sign.sign({'src': 's.pdf', 'dst': 'o.pdf', 'items': [{'image': 'x.png', 'anchor': 'Ali', 'width': 10}]}, base=d)

    def test_white_background_becomes_transparent(self):
        from tools.deckkit import sign
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'cap.png'
            im = Image.new('RGB', (4, 1), 'white'); im.putpixel((0, 0), (0, 100, 0)); im.save(p)
            data, size = sign._transparent_png(p, opacity=0.5, trim=False)
            out = Image.open(__import__('io').BytesIO(data))
            self.assertEqual(out.getpixel((1, 0))[3], 0)
            self.assertEqual(out.getpixel((0, 0))[3], 127)


class SignTrimTest(unittest.TestCase):
    def test_trim_crops_to_ink(self):
        from tools.deckkit import sign
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'ttd.png'
            im = Image.new('RGB', (100, 100), 'white')
            ImageDraw.Draw(im).rectangle((20, 40, 59, 49), fill='black')
            im.save(p)
            _, size = sign._transparent_png(p)
            self.assertEqual(size, (40, 10))
            _, size = sign._transparent_png(p, trim=False)
            self.assertEqual(size, (100, 100))


class LetterheadTest(unittest.TestCase):
    def test_plan_shift_moves_then_scales(self):
        try:
            import pymupdf
        except ImportError:
            self.skipTest('needs pymupdf')
        from tools.deckkit import letterhead
        dy, sc = letterhead.plan_shift(pymupdf.Rect(72, 80, 540, 700), 90, 792, gap=10, min_bottom=36)
        self.assertEqual((dy, sc), (20, 1.0))
        dy, sc = letterhead.plan_shift(pymupdf.Rect(72, 80, 540, 760), 90, 792, gap=10, min_bottom=36)
        self.assertIsNone(dy)
        self.assertAlmostEqual(sc, (756 - 100) / 680)

    def test_letterhead_on_first_page_keeps_text_and_other_pages(self):
        try:
            import pymupdf
        except ImportError:
            self.skipTest('needs pymupdf')
        from tools.deckkit import letterhead
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            doc = pymupdf.open()
            p0 = doc.new_page()
            p0.draw_rect(p0.rect, color=None, fill=(1, 1, 1))  # Word exports paint a white page
            p0.insert_text((72, 60), 'Batam, 19 Oktober 2026')
            doc.new_page().insert_text((72, 60), 'halaman dua')
            doc.save(d / 's.pdf')
            Image.new('RGB', (300, 60), 'black').save(d / 'logo.png')
            rep = letterhead.letterhead({'src': 's.pdf', 'dst': 'k.pdf', 'logo': 'logo.png',
                                         'lines': [{'text': 'PT CONTOH', 'bold': True, 'size': 11},
                                                   {'text': 'Jalan Contoh 1', 'size': 8}]}, base=d)
            self.assertEqual(rep[0][0], 1)
            out = pymupdf.open(d / 'k.pdf')
            self.assertEqual(len(out), 2)
            p1 = out[0]
            self.assertIn('PT CONTOH', p1.get_text())
            hit = p1.search_for('Batam, 19 Oktober 2026')[0]
            self.assertGreater(hit.y0, rep[0][1])  # body now below the header
            self.assertIn('halaman dua', out[1].get_text())
            self.assertNotIn('PT CONTOH', out[1].get_text())
            pix = p1.get_pixmap(clip=pymupdf.Rect(72, 25, 200, 70))
            self.assertLess(min(pix.samples), 50)  # the logo is visible, not covered by the page background


class LetterheadTrimTest(unittest.TestCase):
    def test_logo_trimmed_to_ink(self):
        from tools.deckkit import letterhead
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'logo.png'
            im = Image.new('RGBA', (100, 50), (255, 255, 255, 0))
            ImageDraw.Draw(im).rectangle((10, 5, 69, 24), fill=(20, 20, 20, 255))
            im.save(p)
            _, size = letterhead._trimmed(p)
            self.assertEqual(size, (60, 20))


class RepageTest(unittest.TestCase):
    def _letter(self, d, lines_per_page, pages):
        import pymupdf
        doc = pymupdf.open()
        for p in range(pages):
            pg = doc.new_page()
            pg.draw_rect(pg.rect, color=None, fill=(1, 1, 1))
            for k in range(lines_per_page[p]):
                pg.insert_text((72, 80 + k * 20), f'baris {p}-{k}')
        doc.save(d / 's.pdf')

    def test_four_pages_onto_three_with_numbers_and_no_hidden_text(self):
        try:
            import pymupdf
        except ImportError:
            self.skipTest('needs pymupdf')
        from tools.deckkit import repage
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            self._letter(d, [30, 30, 30, 5], 4)
            r = repage.repage({'src': 's.pdf', 'dst': 'o.pdf', 'pages': 3, 'top': 60, 'bottom': 50,
                               'footer': 'Halaman {n} dari {total}'}, base=d)
            self.assertEqual(r['pages'], 3)
            self.assertLessEqual(r['scale'], 1.0)
            out = pymupdf.open(d / 'o.pdf')
            self.assertEqual(len(out), 3)
            text = ''.join(p.get_text() for p in out)
            for p, n in enumerate([30, 30, 30, 5]):
                for k in range(n):
                    self.assertEqual(text.count(f'baris {p}-{k}\n'), 1, f'baris {p}-{k}')
            self.assertIn('Halaman 3 dari 3', out[2].get_text())

    def test_keep_group_is_not_split(self):
        try:
            import pymupdf
        except ImportError:
            self.skipTest('needs pymupdf')
        from tools.deckkit import repage
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            self._letter(d, [36], 1)
            r = repage.repage({'src': 's.pdf', 'dst': 'o.pdf', 'pages': 2, 'top': 60, 'bottom': 150, 'min_scale': 1.0,
                               'keep': [['baris 0-28', 'baris 0-35']]}, base=d)
            out = pymupdf.open(d / 'o.pdf')
            where = [i for i, p in enumerate(out) if 'baris 0-28' in p.get_text()]
            self.assertTrue(all('baris 0-35' in out[i].get_text() for i in where))
            self.assertEqual(r['pages'], 2)

    def test_too_long_raises(self):
        try:
            import pymupdf
        except ImportError:
            self.skipTest('needs pymupdf')
        from tools.deckkit import repage
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            self._letter(d, [34, 34, 34], 3)
            with self.assertRaises(ValueError):
                repage.repage({'src': 's.pdf', 'dst': 'o.pdf', 'pages': 1, 'min_scale': 0.9}, base=d)


class RepageHeadingTest(unittest.TestCase):
    def test_heading_moves_with_next_row(self):
        from tools.deckkit import repage
        units = [{'y0': 0, 'y1': 10, 'text': f'baris {k}', 'gap': 5} for k in range(5)]
        units.insert(3, {'y0': 0, 'y1': 10, 'text': 'Catatan :', 'gap': 5})
        # page holds rows at y 0,15,30,45 (bottom 60): heading would be the 4th row, its list row would not fit
        placed = repage.layout(units, 3, 60, 0, 0, 0, 1.0)
        page_of = {u['text']: p for p, _, u in placed}
        self.assertEqual(page_of['Catatan :'], page_of['baris 3'])
        self.assertTrue(repage.is_heading('Lingkup  :'))
        self.assertFalse(repage.is_heading('Harga untuk 150 unit pertama (menjadi aset SPS), dapat dilakukan:'))


class RepageParagraphTest(unittest.TestCase):
    def test_short_item_merges_long_paragraph_does_not(self):
        from tools.deckkit import repage
        row = lambda t, gap, y0=0: {'page': 0, 'y0': y0, 'y1': y0 + 12, 'text': t, 'gap': gap}
        units = [row('Harga untuk 150 unit pertama, dapat', 0), row('bertahap', 3),
                 row('Penambahan unit', 3), row('Catatan :', 3), row('isi', 3)]
        merged = repage._paragraphs(units, 4)
        self.assertEqual([u['text'] for u in merged],
                         ['Harga untuk 150 unit pertama, dapat bertahap', 'Penambahan unit', 'Catatan :', 'isi'])
        long = [row('Paragraf', 0)] + [row('lanjut', 3) for _ in range(6)]
        self.assertEqual(len(repage._paragraphs(long, 4)), 7)
        self.assertTrue(repage.starts_item('7. Tim berpengalaman'))
        self.assertFalse(repage.starts_item('2026 mengenai'))


def _logo(path, size, box, colour, bg=(255, 255, 255, 255)):
    im = Image.new("RGBA", size, bg)
    ImageDraw.Draw(im).rectangle(box, fill=colour)
    im.save(path)
    return path


class LogoSquareTest(unittest.TestCase):
    # Google Business Profile wants a square logo and shows it in a circle; a wide wordmark must
    # sit inside that circle.
    def test_square_canvas_with_logo_inside_the_circle(self):
        with tempfile.TemporaryDirectory() as d:
            p = _logo(Path(d) / "w.png", (1200, 300), (100, 100, 1099, 199), (20, 20, 20, 255))
            out = lockup.square(p, size=720, safe=0.8, bg=(255, 255, 255))
            self.assertEqual(out.size, (720, 720))
            self.assertEqual(out.mode, "RGB")
            a = np.asarray(out).astype(int)
            ys, xs = np.nonzero(a.sum(axis=2) < 300)
            r = np.sqrt((xs - 359.5) ** 2 + (ys - 359.5) ** 2).max()
            self.assertLessEqual(r, 0.8 * 720 / 2 + 1)
            self.assertGreater(xs.max() - xs.min(), 400)
            self.assertEqual(tuple(a[5, 5]), (255, 255, 255))

    def test_square_background_colour(self):
        with tempfile.TemporaryDirectory() as d:
            p = _logo(Path(d) / "w.png", (400, 200), (100, 50, 299, 149), (230, 180, 40, 255))
            out = lockup.square(p, size=300, bg=(21, 33, 43))
            self.assertEqual(out.getpixel((2, 2)), (21, 33, 43))

    def test_cli_logo_square(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            p = _logo(d / "w.png", (600, 200), (50, 50, 549, 149), (20, 20, 20, 255))
            self.assertEqual(_quiet_cli(["logo-square", str(p), str(d / "o.png"), "--size", "720"]), 0)
            self.assertEqual(Image.open(d / "o.png").size, (720, 720))
            self.assertNotEqual(_quiet_cli(["logo-square", str(p), str(d / "o.png"), "--safe", "1.5"]), 0)


class LockupTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        d = Path(self.tmp.name)
        # 200x100 canvases, white margin, content 60x40 and 40x20
        self.a = _logo(d / "a.png", (200, 100), (50, 30, 109, 69), (200, 0, 0, 255))
        self.b = _logo(d / "b.png", (200, 100), (10, 10, 49, 29), (0, 0, 200, 255))
        self.out = d / "out.png"

    def test_trim_removes_white_and_transparent_margin(self):
        with Image.open(self.a) as im:
            self.assertEqual(lockup.trim(im, 18).size, (60, 40))
        clear = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        ImageDraw.Draw(clear).rectangle((20, 20, 39, 49), fill=(0, 0, 0, 255))
        self.assertEqual(lockup.trim(clear, 18).size, (20, 30))

    def test_trim_white_becomes_transparent(self):
        im = Image.new("RGBA", (40, 20), (255, 255, 255, 255))
        d = ImageDraw.Draw(im)
        d.rectangle((0, 0, 9, 19), fill=(200, 0, 0, 255))
        d.rectangle((20, 0, 29, 19), fill=(200, 0, 0, 255))
        out = lockup.trim(im, 18)
        self.assertEqual(out.size, (30, 20))
        self.assertEqual(out.getpixel((5, 5))[3], 255)
        self.assertEqual(out.getpixel((15, 5))[3], 0)

    def test_blank_image_is_an_error(self):
        with self.assertRaises(ValueError):
            lockup.trim(Image.new("RGBA", (20, 20), (255, 255, 255, 255)), 18)

    def test_lockup_height_and_width(self):
        res = lockup.lockup([self.a, self.b], height=100, gap=10, second_scale=0.5, sep_width=20)
        self.assertEqual(res.mode, "RGBA")
        self.assertEqual(res.height, 100)
        first = round(60 * 100 / 40)          # 150, scaled to full height
        second = round(40 * 50 / 20)          # 100, scaled to half height
        self.assertEqual(res.width, first + 10 + 20 + 10 + second)
        self.assertEqual(res.getpixel((first + 10, 0))[3], 0)  # gap stays transparent

    def test_lockup_keeps_both_logos_and_sep_ink(self):
        res = lockup.lockup([self.a, self.b], height=100, gap=10, second_scale=0.5, sep_width=20)
        self.assertEqual(res.getpixel((10, 50))[:3], (200, 0, 0))
        self.assertEqual(res.getpixel((res.width - 10, 50))[:3], (0, 0, 200))
        mid = res.crop((150 + 10, 0, 150 + 30, 100))
        self.assertIsNotNone(mid.getchannel("A").getbbox())

    def test_lockup_separator_is_configurable_and_font_must_exist(self):
        res = lockup.lockup([self.a, self.b], height=100, sep="+", gap=10, second_scale=0.5, sep_width=20)
        self.assertEqual(res.height, 100)
        with self.assertRaises(FileNotFoundError):
            lockup.lockup([self.a, self.b], height=100, font="/no/such/font.ttf")

    def test_lockup_missing_empty_or_wrong_count(self):
        with self.assertRaises(FileNotFoundError):
            lockup.lockup([self.a, Path(self.tmp.name) / "nope.png"])
        empty = Path(self.tmp.name) / "empty.png"
        empty.write_bytes(b"")
        with self.assertRaises(ValueError):
            lockup.lockup([self.a, empty])
        with self.assertRaises(ValueError):
            lockup.lockup([self.a])

    def test_cli_writes_lockup_and_trimmed_logos(self):
        from tools.deckkit.__main__ import main
        trims = Path(self.tmp.name) / "trimmed"
        rc = main(["lockup", str(self.out), str(self.a), str(self.b), "--height", "100", "--trim-out", str(trims)])
        self.assertEqual(rc, 0)
        with Image.open(self.out) as im:
            self.assertEqual(im.height, 100)
        with Image.open(trims / "a.png") as t:
            self.assertEqual(t.height, 100)
        self.assertTrue((trims / "b.png").exists())
        self.assertEqual(main(["lockup", str(self.out), str(self.a), str(Path(self.tmp.name) / "nope.png")]), 1)


def _gradient_page(size=(120, 60)):
    """Light page whose background darkens by row, so a flat single colour is visibly wrong."""
    a = np.zeros((size[1], size[0], 3), dtype=np.uint8)
    for y in range(size[1]):
        a[y, :] = (250 - y, 250 - y, 250 - y)
    return Image.fromarray(a)


def _two_letters(img):
    """Navy blocks left and right of a gap (x 40-59), like the p and o of a headline."""
    d = ImageDraw.Draw(img)
    d.rectangle((20, 10, 39, 50), fill=(10, 20, 80))
    d.rectangle((60, 10, 79, 50), fill=(10, 20, 80))
    d.rectangle((45, 20, 52, 30), fill=(10, 20, 80))  # the stray mark to erase
    return img


class FlatEraseTest(unittest.TestCase):
    def test_default_erase_stains_when_box_touches_letters(self):
        img = _two_letters(_gradient_page())
        patch.erase_between(img, (40, 10, 60, 51))
        stain = np.asarray(img)[30, 50].astype(int)
        self.assertLess(stain.sum(), 400)  # navy pulled into the box: the bug being fixed

    def test_flat_fill_paints_background_per_row(self):
        img = _two_letters(_gradient_page())
        patch.flat_fill(img, (40, 10, 60, 51), bg_x=100)
        a = np.asarray(img).astype(int)
        for y in (10, 25, 50):
            self.assertTrue((a[y, 40:60] == a[y, 100]).all(), y)
        self.assertEqual(tuple(a[50, 39]), (10, 20, 80))  # neighbour letters untouched
        self.assertEqual(tuple(a[50, 60]), (10, 20, 80))

    def test_flat_fill_default_sample_is_right_of_box(self):
        img = _gradient_page()
        patch.flat_fill(img, (40, 10, 60, 20))
        a = np.asarray(img).astype(int)
        self.assertTrue((a[15, 40:60] == a[15, 60]).all())

    def test_flat_fill_bad_column(self):
        with self.assertRaisesRegex(ValueError, "bg_x"):
            patch.flat_fill(_gradient_page(), (40, 10, 60, 20), bg_x=500)

    def test_erase_between_bg_from(self):
        img = _two_letters(_gradient_page())
        patch.erase_between(img, (40, 10, 60, 51), bg_from=100)
        a = np.asarray(img).astype(int)
        self.assertTrue((a[30, 40:60] == a[30, 100]).all())

    def test_retype_erase_flat_and_bg_from(self):
        import os, tempfile
        d = tempfile.mkdtemp()
        img = _two_letters(_gradient_page())
        ImageDraw.Draw(img).rectangle((85, 20, 90, 30), fill=(10, 20, 80))  # stray mark in open ground
        img.save(os.path.join(d, "a.png"))
        out = patch.retype({"fixes": [
            {"src": "a.png", "dst": "f.png", "box": [82, 10, 100, 51], "erase": "flat"},
            {"src": "a.png", "dst": "g.png", "box": [40, 10, 60, 51], "erase": True, "bg_from": 100}]}, d)
        flat = np.asarray(Image.open(out[0])).astype(int)
        self.assertTrue((flat[25, 82:100] == flat[25, 100]).all())
        gap = np.asarray(Image.open(out[1])).astype(int)
        self.assertTrue((gap[30, 40:60] == gap[30, 100]).all())  # no navy stain between the letters

    def test_retype_erase_flat_bad_value(self):
        import os, tempfile
        d = tempfile.mkdtemp()
        _gradient_page().save(os.path.join(d, "a.png"))
        with self.assertRaisesRegex(ValueError, "erase"):
            patch.retype({"fixes": [{"src": "a.png", "dst": "f.png", "box": [1, 1, 5, 5], "erase": "blur"}]}, d)


def _title_line(dark=True):
    """Two-row text band: three words (x 10-39, 60-99, 120-139) and a tail pixel below the band."""
    bg, ink = ((250, 250, 250), (10, 20, 80)) if dark else ((10, 20, 80), (250, 250, 250))
    img = Image.new("RGB", (200, 80), bg)
    d = ImageDraw.Draw(img)
    for x0, x1 in ((10, 39), (60, 99), (120, 139)):
        d.rectangle((x0, 20, x1, 35), fill=ink)
    d.rectangle((70, 36, 72, 45), fill=ink)  # descender of the word above: outside the band
    return img


class ReflowTest(unittest.TestCase):
    def test_line_words_splits_on_gap(self):
        self.assertEqual(patch.line_words(_title_line(), 20, 36, 0, 200), [(10, 39), (60, 99), (120, 139)])

    def test_line_words_small_gap_joins(self):
        # blank run between words is 20 columns: split only when it is > gap
        self.assertEqual(len(patch.line_words(_title_line(), 20, 36, 0, 200, gap=19)), 3)
        self.assertEqual(patch.line_words(_title_line(), 20, 36, 0, 200, gap=20), [(10, 139)])

    def test_line_words_light_ink_and_empty(self):
        self.assertEqual(len(patch.line_words(_title_line(dark=False), 20, 36, 0, 200, dark=False)), 3)
        self.assertEqual(patch.line_words(_title_line(), 60, 70, 0, 200), [])

    def test_move_ink_moves_word_and_clears_source(self):
        img = _title_line()
        patch.move_ink(img, (120, 20, 140, 36), (150, 20))
        a = np.asarray(img).astype(int)
        self.assertEqual(tuple(a[25, 125]), (250, 250, 250))  # source cleared
        self.assertEqual(tuple(a[25, 155]), (10, 20, 80))     # ink arrived
        self.assertEqual(tuple(a[25, 145]), (250, 250, 250))  # no background box pasted

    def test_move_ink_leaves_neighbour_tails(self):
        img = _title_line()
        patch.move_ink(img, (120, 20, 140, 36), (150, 20))
        self.assertEqual(tuple(np.asarray(img)[40, 71]), (10, 20, 80))

    def test_move_ink_copies_only_ink_over_gradient(self):
        img = _gradient_page((120, 60))
        ImageDraw.Draw(img).rectangle((20, 10, 29, 20), fill=(10, 20, 80))
        before = np.asarray(img).astype(int).copy()
        patch.move_ink(img, (15, 5, 35, 25), (70, 30), clear=False)
        a = np.asarray(img).astype(int)
        self.assertEqual(tuple(a[40, 75]), (10, 20, 80))
        self.assertTrue((a[26:46, 65:70] == before[26:46, 65:70]).all())  # surrounding gradient kept
        self.assertTrue((a[:25, 15:35] == before[:25, 15:35]).all())      # clear=False: source stays

    def test_move_ink_clear_uses_row_background(self):
        img = _gradient_page((120, 60))
        ImageDraw.Draw(img).rectangle((20, 10, 29, 20), fill=(10, 20, 80))
        patch.move_ink(img, (15, 5, 35, 25), (70, 30), bg_x=60)
        a = np.asarray(img).astype(int)
        for y in (5, 15, 24):
            self.assertTrue((a[y, 15:35] == a[y, 60]).all(), y)

    def test_move_ink_light_ink_on_dark(self):
        img = _title_line(dark=False)
        patch.move_ink(img, (120, 20, 140, 36), (150, 20), dark=False)
        a = np.asarray(img).astype(int)
        self.assertEqual(tuple(a[25, 155]), (250, 250, 250))
        self.assertEqual(tuple(a[25, 125]), (10, 20, 80))

    def test_move_ink_errors(self):
        with self.assertRaisesRegex(ValueError, "no ink"):
            patch.move_ink(_title_line(), (150, 20, 190, 36), (10, 50))
        with self.assertRaisesRegex(ValueError, "outside"):
            patch.move_ink(_title_line(), (120, 20, 140, 36), (190, 20))

    def test_reflow_plan_moves_word_by_index_and_validates_first(self):
        import os, tempfile
        d = tempfile.mkdtemp()
        _title_line().save(os.path.join(d, "a.png"))
        spec = {"fixes": [{"src": "a.png", "dst": "b.png", "ops": [
            {"op": "move", "line": [20, 36, 0, 200], "word": 2, "to": [150, 20]},
            {"op": "clear", "box": [60, 20, 100, 36]}]}]}
        out, report = patch.reflow(spec, d)
        a = np.asarray(Image.open(out[0])).astype(int)
        self.assertEqual(tuple(a[25, 155]), (10, 20, 80))
        self.assertEqual(tuple(a[25, 80]), (250, 250, 250))
        bad = {"fixes": [spec["fixes"][0], {"src": "a.png", "dst": "c.png", "ops": [{"op": "zap"}]}]}
        with self.assertRaisesRegex(ValueError, "fix 1"):
            patch.reflow(bad, d)
        self.assertFalse(os.path.exists(os.path.join(d, "c.png")))
        with self.assertRaisesRegex(ValueError, "word"):
            patch.reflow({"fixes": [{"src": "a.png", "dst": "c.png", "ops": [
                {"op": "move", "line": [20, 36, 0, 200], "word": 9, "to": [1, 1]}]}]}, d)

    def test_reflow_words_op_reports(self):
        import os, tempfile
        d = tempfile.mkdtemp()
        _title_line().save(os.path.join(d, "a.png"))
        out, report = patch.reflow({"fixes": [{"src": "a.png", "dst": "b.png", "ops": [
            {"op": "words", "line": [20, 36, 0, 200]}]}]}, d)
        self.assertEqual(report[0], [[10, 39], [60, 99], [120, 139]])
