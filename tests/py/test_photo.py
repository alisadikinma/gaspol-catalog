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
from tools.deckkit import photo


def run_cli(argv):
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return cli.main(argv)

PAGE = (200, 120)
BOX = (40, 30, 80, 50)


def page():
    return Image.new("RGB", PAGE, (250, 250, 250))


def pic(size=(60, 60), colour=(200, 20, 20), mode="RGB"):
    return Image.new(mode, size, colour)


def outside_unchanged(before, after, inside):
    a, b = np.asarray(before.convert("RGB")), np.asarray(after.convert("RGB"))
    diff = (a != b).any(2)
    return not (diff & ~inside).any()


def box_mask(box):
    m = np.zeros((PAGE[1], PAGE[0]), bool)
    x, y, w, h = box
    m[y:y + h, x:x + w] = True
    return m


class CoverTest(unittest.TestCase):
    def test_exact_size_landscape_and_portrait_sources(self):
        self.assertEqual(photo.cover(pic((300, 100)), (80, 50)).size, (80, 50))
        self.assertEqual(photo.cover(pic((100, 300)), (80, 50)).size, (80, 50))
        self.assertEqual(photo.cover(pic((50, 80)), (120, 40)).size, (120, 40))

    def test_keeps_centre(self):
        src = Image.new("RGB", (300, 100), (0, 0, 255))
        src.paste((255, 0, 0), (100, 0, 200, 100))  # centre third red
        out = photo.cover(src, (50, 50))
        self.assertEqual(out.getpixel((25, 25)), (255, 0, 0))

    def test_bad_size_raises(self):
        with self.assertRaises(ValueError):
            photo.cover(pic(), (0, 10))


class PlaceTest(unittest.TestCase):
    def test_changes_only_inside_box_and_input_untouched(self):
        pg = page()
        out = photo.place(pg, pic((40, 90)), BOX)
        self.assertTrue(outside_unchanged(pg, out, box_mask(BOX)))
        self.assertEqual(out.getpixel((80, 55)), (200, 20, 20))
        self.assertEqual(pg.getpixel((80, 55)), (250, 250, 250))
        self.assertEqual(out.size, PAGE)

    def test_landscape_photo_into_portrait_box(self):
        box = (10, 10, 40, 90)
        out = photo.place(page(), pic((120, 40)), box)
        self.assertTrue(outside_unchanged(page(), out, box_mask(box)))
        self.assertEqual(out.getpixel((30, 55)), (200, 20, 20))

    def test_radius_zero_fills_corners(self):
        out = photo.place(page(), pic(), BOX, radius=0)
        self.assertEqual(out.getpixel((40, 30)), (200, 20, 20))

    def test_radius_rounds_corners(self):
        out = photo.place(page(), pic(), BOX, radius=12)
        self.assertEqual(out.getpixel((40, 30)), (250, 250, 250))
        self.assertEqual(out.getpixel((80, 55)), (200, 20, 20))
        self.assertTrue(outside_unchanged(page(), out, box_mask(BOX)))

    def test_radius_larger_than_half_side_is_clamped(self):
        out = photo.place(page(), pic(), BOX, radius=999)  # clamps to 25 -> stadium
        self.assertEqual(out.getpixel((80, 55)), (200, 20, 20))
        self.assertEqual(out.getpixel((40, 30)), (250, 250, 250))

    def test_negative_radius_raises(self):
        with self.assertRaises(ValueError):
            photo.place(page(), pic(), BOX, radius=-1)

    def test_rgba_photo(self):
        out = photo.place(page(), pic(mode="RGBA", colour=(200, 20, 20, 255)), BOX)
        self.assertEqual(out.mode, "RGB")
        self.assertEqual(out.getpixel((80, 55)), (200, 20, 20))

    def test_transparent_rgba_leaves_page(self):
        out = photo.place(page(), pic(mode="RGBA", colour=(200, 20, 20, 0)), BOX)
        self.assertEqual(out.getpixel((80, 55)), (250, 250, 250))

    def test_box_outside_page_raises(self):
        for box in [(150, 30, 80, 50), (-1, 0, 20, 20), (0, 100, 20, 30), (0, 0, 0, 10)]:
            with self.assertRaises(ValueError, msg=str(box)):
                photo.place(page(), pic(), box)


class CircleTest(unittest.TestCase):
    def test_changes_only_inside_circle(self):
        pg = page()
        out = photo.circle(pg, pic(), (100, 60), 40)
        yy, xx = np.mgrid[0:PAGE[1], 0:PAGE[0]]
        inside = (xx - 99.5) ** 2 + (yy - 59.5) ** 2 <= 41 ** 2
        self.assertTrue(outside_unchanged(pg, out, inside))
        self.assertEqual(out.getpixel((100, 60)), (200, 20, 20))
        self.assertEqual(out.getpixel((62, 22)), (250, 250, 250))  # square corner stays page

    def test_circle_outside_page_raises(self):
        with self.assertRaises(ValueError):
            photo.circle(page(), pic(), (10, 10), 40)

    def test_nonpositive_radius_raises(self):
        with self.assertRaises(ValueError):
            photo.circle(page(), pic(), (100, 60), 0)


class CliTest(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        page().save(self.d / "p.png")
        pic().save(self.d / "f.png")

    def test_box_writes_out_and_leaves_input(self):
        out = self.d / "o.png"
        rc = run_cli(["photo", str(self.d / "p.png"), str(self.d / "f.png"),
                       "--box", "40,30,80,50", "--radius", "8", "--out", str(out)])
        self.assertEqual(rc, 0)
        self.assertEqual(Image.open(out).getpixel((80, 55)), (200, 20, 20))
        self.assertEqual(Image.open(self.d / "p.png").getpixel((80, 55)), (250, 250, 250))

    def test_default_overwrites_image(self):
        rc = run_cli(["photo", str(self.d / "p.png"), str(self.d / "f.png"), "--box", "40,30,80,50"])
        self.assertEqual(rc, 0)
        self.assertEqual(Image.open(self.d / "p.png").getpixel((80, 55)), (200, 20, 20))

    def test_circle_uses_box_centre_and_half_min_side(self):
        out = self.d / "c.png"
        rc = run_cli(["photo", str(self.d / "p.png"), str(self.d / "f.png"),
                       "--box", "60,20,80,80", "--circle", "--out", str(out)])
        self.assertEqual(rc, 0)
        im = Image.open(out)
        self.assertEqual(im.getpixel((100, 60)), (200, 20, 20))
        self.assertEqual(im.getpixel((62, 22)), (250, 250, 250))

    def test_bad_box_fails(self):
        rc = run_cli(["photo", str(self.d / "p.png"), str(self.d / "f.png"), "--box", "1,2,3"])
        self.assertEqual(rc, 1)
        rc = run_cli(["photo", str(self.d / "p.png"), str(self.d / "f.png"), "--box", "190,0,50,50"])
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
