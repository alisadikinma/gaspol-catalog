import tempfile
import unittest
from pathlib import Path

try:
    import numpy as np
    from PIL import Image, ImageDraw
except ImportError:
    raise unittest.SkipTest('needs Pillow + numpy: use the gaspol-video venv python')

from tools.deckkit import band, patch, pdf, slots, stamp, watermark


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


if __name__ == "__main__":
    unittest.main()
