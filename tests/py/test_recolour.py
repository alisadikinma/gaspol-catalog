import contextlib
import io
import tempfile
import unittest
from pathlib import Path

try:
    import numpy as np
    from PIL import Image
except ImportError:
    raise unittest.SkipTest('needs Pillow + numpy: use the gaspol-video venv python')

from tools.deckkit import __main__ as cli
from tools.deckkit import recolour

W, H = 600, 400
BG = (245, 245, 245)
TEAL = (35, 133, 127)
BARS_Y = [(40, 100), (150, 210), (260, 330)]  # (y0, y1), top to bottom
BAR_X, BAR_W = 400, 5
WANT = ["#2c5d99", "#a8712a", "#15212b"]


def rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def page(bars=BARS_Y, bar_x=BAR_X):
    img = Image.new("RGB", (W, H), BG)
    for y0, y1 in bars:
        img.paste(TEAL, (bar_x, y0, bar_x + BAR_W, y1))
    img.paste(TEAL, (450, 20, 530, 60))  # teal blob, not a bar
    return img


def near(a, b, tol=6):
    return all(abs(int(x) - int(y)) <= tol for x, y in zip(a, b))


class BarsTest(unittest.TestCase):
    def test_recolours_top_to_bottom(self):
        out = recolour.bars(page(), WANT, x_from=0.55)
        for (y0, y1), hx in zip(BARS_Y, WANT):
            c = out.getpixel((BAR_X + 2, (y0 + y1) // 2))
            self.assertTrue(near(c, rgb(hx)), (c, hx))

    def test_pixels_outside_bars_unchanged(self):
        src = page()
        out = recolour.bars(src, WANT)
        a, b = np.asarray(src), np.asarray(out)
        diff = (a != b).any(2)
        allowed = np.zeros((H, W), bool)
        for y0, y1 in BARS_Y:
            allowed[y0 - 4:y1 + 4, BAR_X - 4:BAR_X + BAR_W + 4] = True
        self.assertTrue(diff.any())
        self.assertFalse((diff & ~allowed).any())

    def test_blob_ignored(self):
        out = recolour.bars(page(), WANT)
        self.assertEqual(out.getpixel((490, 40)), TEAL)

    def test_input_not_mutated(self):
        src = page()
        before = src.copy()
        recolour.bars(src, WANT)
        self.assertEqual(src.tobytes(), before.tobytes())

    def test_mismatch_raises_and_input_unchanged(self):
        src = page()
        before = src.copy()
        with self.assertRaises(ValueError) as cm:
            recolour.bars(src, WANT + ["#000000"])
        self.assertEqual(str(cm.exception), "found 3 bars, expected 4")
        self.assertEqual(src.tobytes(), before.tobytes())

    def test_bars_left_of_x_from_ignored(self):
        img = page()
        img.paste(TEAL, (100, 40, 100 + BAR_W, 100))  # left half bar
        out = recolour.bars(img, WANT, x_from=0.55)
        self.assertEqual(out.getpixel((102, 70)), TEAL)
        self.assertTrue(near(out.getpixel((BAR_X + 2, 70)), rgb(WANT[0])))

    def test_custom_source_colour(self):
        img = Image.new("RGB", (W, H), BG)
        red = (200, 30, 30)
        img.paste(red, (BAR_X, 40, BAR_X + BAR_W, 100))
        out = recolour.bars(img, ["#2c5d99"], source="#c81e1e")
        self.assertTrue(near(out.getpixel((BAR_X + 2, 70)), (44, 93, 153)))

    def test_bad_hex_raises(self):
        with self.assertRaises(ValueError):
            recolour.bars(page(), ["red", "#a8712a", "#15212b"])


class CliTest(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        page().save(self.d / "p.png")

    def run_cli(self, argv):
        with contextlib.redirect_stdout(io.StringIO()) as so, contextlib.redirect_stderr(io.StringIO()):
            rc = cli.main(argv)
        return rc, so.getvalue()

    def test_out_path_printed_input_kept(self):
        out = self.d / "o.png"
        rc, so = self.run_cli(["recolour", str(self.d / "p.png"), "--colours", *WANT, "--out", str(out)])
        self.assertEqual(rc, 0)
        self.assertEqual(so.strip(), str(out))
        self.assertTrue(near(Image.open(out).getpixel((BAR_X + 2, 70)), rgb(WANT[0])))
        self.assertEqual(Image.open(self.d / "p.png").getpixel((BAR_X + 2, 70)), TEAL)

    def test_default_overwrites(self):
        rc, _ = self.run_cli(["recolour", str(self.d / "p.png"), "--colours", *WANT])
        self.assertEqual(rc, 0)
        self.assertTrue(near(Image.open(self.d / "p.png").getpixel((BAR_X + 2, 70)), rgb(WANT[0])))

    def test_mismatch_fails(self):
        rc, _ = self.run_cli(["recolour", str(self.d / "p.png"), "--colours", "#000000"])
        self.assertEqual(rc, 1)


class SilentFailureTest(unittest.TestCase):
    def test_bar_core_near_background_raises(self):
        img = Image.new("RGB", (W, H), (100, 133, 127))
        for y0, y1 in BARS_Y:
            img.paste((85, 133, 127), (BAR_X, y0, BAR_X + BAR_W, y1))
        with self.assertRaisesRegex(ValueError, "bar 0"):
            recolour.bars(img, WANT)

    def test_unverifiable_result_raises(self):
        from unittest import mock
        with mock.patch.object(recolour, "VERIFY_TOL", -1):
            with self.assertRaisesRegex(ValueError, "bar 0"):
                recolour.bars(page(), WANT)

    def test_normal_page_still_verifies(self):
        out = recolour.bars(page(), WANT)
        self.assertEqual(out.size, (W, H))


if __name__ == "__main__":
    unittest.main()
