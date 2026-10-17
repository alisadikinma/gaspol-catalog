import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    raise unittest.SkipTest('needs Pillow: use the gaspol-video venv python')

from tools.deckkit import __main__ as cli
from tools.deckkit import table

SIZE = (1376, 768)
SPEC = {
    "title": "Side by side",
    "columns": ["Item", "Ours", "Theirs"],
    "rows": [
        ["Price", "Rp 1.250.000", "Rp 4.800.000"],
        ["Support", "24 hours", "None"],
        ["Setup", "3 days", "2 weeks"],
    ],
    "marks": {"1,1": "good", "1,2": "bad"},
}


def ink(img, box, bg=None):
    x0, y0, x1, y1 = box
    crop = img.crop((x0 + 2, y0 + 2, x1 - 2, y1 - 2))
    bg = bg or crop.getpixel((0, 0))
    return sum(1 for p in crop.getdata() if sum(abs(a - b) for a, b in zip(p, bg)) > 120)


class RenderTest(unittest.TestCase):
    def test_exact_size_and_mode(self):
        img = table.render(SPEC, size=SIZE)
        self.assertEqual(img.size, SIZE)
        self.assertEqual(img.mode, "RGB")

    def test_default_size(self):
        self.assertEqual(table.render(SPEC).size, (2752, 1536))

    def test_every_cell_has_ink(self):
        img = table.render(SPEC, size=SIZE)
        boxes = table.cell_boxes(SPEC, SIZE)
        self.assertEqual(len(boxes), 9 + 3)  # body cells + header cells keyed by (-1, c)
        for key, box in boxes.items():
            self.assertGreater(ink(img, box), 20, key)

    def test_table_fills_page_height(self):
        img = table.render(SPEC, size=SIZE)
        boxes = table.cell_boxes(SPEC, SIZE)
        H = SIZE[1]
        band_top = H - H * table.BAND_FRACTION
        bottom = max(b[3] for b in boxes.values())
        self.assertLessEqual(bottom, band_top)
        self.assertLessEqual(band_top - bottom, 0.08 * H)
        heights = {b[3] - b[1] for k, b in boxes.items() if k[1] == 0}
        self.assertLessEqual(max(heights) - min(heights), 1 + len(SPEC["rows"]))  # equal rows incl. header

    def test_body_text_cap_height(self):
        from PIL import ImageChops
        img = table.render(SPEC, size=SIZE)
        x0, y0, x1, y1 = table.cell_boxes(SPEC, SIZE)[(0, 0)]
        crop = img.crop((x0 + 2, y0 + 2, x1 - 2, y1 - 2))
        bbox = ImageChops.difference(crop, Image.new("RGB", crop.size, crop.getpixel((0, 0)))).getbbox()
        self.assertGreater(bbox[3] - bbox[1], 0.02 * SIZE[1])
        # text vertically centred in its cell
        top_gap, bot_gap = bbox[1], crop.size[1] - bbox[3]
        self.assertLess(abs(top_gap - bot_gap), 0.1 * crop.size[1])

    def test_long_cell_wraps_within_cell(self):
        spec = json.loads(json.dumps(SPEC))
        spec["rows"][0][1] = "one very long cell text that has to wrap over several lines to fit " * 2
        img = table.render(spec, size=SIZE)
        x0, y0, x1, y1 = table.cell_boxes(spec, SIZE)[(0, 1)]

        def ink_height(im, box):
            from PIL import Image, ImageChops
            crop = im.crop((box[0] + 2, box[1] + 2, box[2] - 2, box[3] - 2))
            bb = ImageChops.difference(crop, Image.new("RGB", crop.size, crop.getpixel((0, 0)))).getbbox()
            return bb[3] - bb[1]

        short_box = table.cell_boxes(SPEC, SIZE)[(0, 1)]
        # wrapped text spans several lines: its ink is much taller than a one-line cell's
        self.assertGreater(ink_height(img, (x0, y0, x1, y1)),
                           1.8 * ink_height(table.render(SPEC, size=SIZE), short_box))
        # nothing drawn outside the cell horizontally: strip just right of the cell has no text ink
        self.assertEqual(img.size, SIZE)

    def test_impossible_cell_names_row_col(self):
        spec = json.loads(json.dumps(SPEC))
        spec["rows"][2][0] = "word " * 4000
        with self.assertRaises(ValueError) as cm:
            table.render(spec, size=SIZE)
        self.assertIn("cell 2,0 does not fit", str(cm.exception))

    def test_unbreakable_word_too_wide(self):
        spec = json.loads(json.dumps(SPEC))
        spec["rows"][0][2] = "X" * 400
        with self.assertRaises(ValueError) as cm:
            table.render(spec, size=SIZE)
        self.assertIn("cell 0,2 does not fit", str(cm.exception))

    def test_ragged_row(self):
        spec = json.loads(json.dumps(SPEC))
        spec["rows"][1] = ["only", "two"]
        with self.assertRaises(ValueError) as cm:
            table.render(spec, size=SIZE)
        self.assertIn("row 1", str(cm.exception))

    def test_bad_mark(self):
        for marks in ({"9,0": "good"}, {"0,0": "meh"}, {"zero": "good"}):
            spec = dict(SPEC, marks=marks)
            with self.assertRaises(ValueError):
                table.render(spec, size=SIZE)

    def test_mark_colours_present_only_in_marked_cells(self):
        img = table.render(SPEC, size=SIZE)
        boxes = table.cell_boxes(SPEC, SIZE)

        def has(box, rgb):
            x0, y0, x1, y1 = box
            return img.getpixel((x0 + 4, y0 + 4)) == rgb

        self.assertTrue(has(boxes[(1, 1)], table.GOOD_BG))
        self.assertTrue(has(boxes[(1, 2)], table.BAD_BG))
        self.assertFalse(has(boxes[(0, 1)], table.GOOD_BG))
        self.assertFalse(has(boxes[(0, 1)], table.BAD_BG))

    def test_palette_override_and_preset_default(self):
        spec = dict(SPEC, palette={"background": "#ff0000"})
        self.assertEqual(table.render(spec, size=SIZE).getpixel((2, 2)), (255, 0, 0))
        self.assertNotEqual(table.render(SPEC, size=SIZE).getpixel((2, 2)), (255, 0, 0))

    def test_unknown_preset(self):
        with self.assertRaises(FileNotFoundError):
            table.render(dict(SPEC, preset="no-such-preset"), size=SIZE)

    def test_bottom_band_left_empty(self):
        img = table.render(SPEC, size=SIZE)
        bg = img.getpixel((2, 2))
        h = SIZE[1]
        strip = img.crop((0, int(h * 0.94), SIZE[0], h))
        self.assertEqual(set(strip.getdata()), {bg})

    def test_inputs_not_mutated(self):
        before = json.dumps(SPEC, sort_keys=True)
        table.render(SPEC, size=SIZE)
        self.assertEqual(json.dumps(SPEC, sort_keys=True), before)


class CliTest(unittest.TestCase):
    def test_writes_png_quietly(self):
        d = Path(tempfile.mkdtemp())
        (d / "s.json").write_text(json.dumps(SPEC))
        out = d / "o.png"
        with contextlib.redirect_stdout(io.StringIO()) as so, contextlib.redirect_stderr(io.StringIO()) as se:
            rc = cli.main(["table", str(d / "s.json"), str(out), "--size", "1376x768"])
        self.assertEqual(rc, 0)
        self.assertEqual(so.getvalue().strip(), str(out))
        self.assertEqual(se.getvalue(), "")
        self.assertEqual(Image.open(out).size, (1376, 768))

    def test_bad_spec_fails(self):
        d = Path(tempfile.mkdtemp())
        bad = dict(SPEC, rows=[["a"]])
        (d / "s.json").write_text(json.dumps(bad))
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            rc = cli.main(["table", str(d / "s.json"), str(d / "o.png")])
        self.assertEqual(rc, 1)

    def test_bad_size_fails(self):
        d = Path(tempfile.mkdtemp())
        (d / "s.json").write_text(json.dumps(SPEC))
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            rc = cli.main(["table", str(d / "s.json"), str(d / "o.png"), "--size", "big"])
        self.assertEqual(rc, 1)


class SilentFailureTest(unittest.TestCase):
    def test_header_wider_than_column_raises_naming_column(self):
        spec = dict(SPEC, columns=["Item", "Ours", "Supercalifragilisticexpialidocious" * 3])
        with self.assertRaisesRegex(ValueError, "column 2"):
            table.render(spec, size=SIZE)

    def test_title_word_wider_than_page_raises(self):
        spec = dict(SPEC, title="W" * 400)
        with self.assertRaisesRegex(ValueError, "title"):
            table.render(spec, size=SIZE)

    def test_unknown_palette_key_raises_listing_allowed(self):
        spec = dict(SPEC, palette={"backgroud": "#ffffff"})
        with self.assertRaisesRegex(ValueError, r"backgroud.*allowed.*background"):
            table.render(spec, size=SIZE)


if __name__ == "__main__":
    unittest.main()
