import contextlib
import io
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock

try:
    from PIL import Image
except ImportError:
    raise unittest.SkipTest('needs Pillow: use the gaspol-video venv python')

from tools.deckkit import __main__ as cli
from tools.deckkit import chips, chrome


def _real_chrome():
    try:
        return chrome.find_chrome()
    except RuntimeError:
        return None


class ChipsTest(unittest.TestCase):
    def test_pill_corners_transparent_centre_opaque(self):
        im = chips.pill("Hello", size=28)
        self.assertEqual(im.mode, "RGBA")
        w, h = im.size
        for xy in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
            self.assertEqual(im.getpixel(xy)[3], 0, xy)
        self.assertEqual(im.getpixel((3, h // 2))[3], 255)
        self.assertEqual(im.getpixel((3, h // 2))[:3], (35, 133, 127))

    def test_pill_grows_with_text_and_padding(self):
        a = chips.pill("Hi", size=28)
        b = chips.pill("Hi there, longer", size=28)
        c = chips.pill("Hi", size=28, pad=(40, 8))
        self.assertGreater(b.width, a.width)
        self.assertGreater(c.width, a.width)

    def test_pill_empty_text_still_valid(self):
        self.assertGreater(chips.pill("").width, 0)

    def test_flag_horizontal(self):
        im = chips.flag([(255, 0, 0), (255, 255, 255)], (60, 40))
        self.assertEqual(im.mode, "RGB")
        self.assertEqual(im.size, (60, 40))
        self.assertEqual(im.getpixel((30, 5)), (255, 0, 0))
        self.assertEqual(im.getpixel((30, 35)), (255, 255, 255))

    def test_flag_vertical_three(self):
        cols = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
        im = chips.flag(cols, (90, 20), stripes="v")
        self.assertEqual([im.getpixel((x, 10)) for x in (5, 45, 85)], cols)

    def test_flag_bad_input(self):
        with self.assertRaises(ValueError):
            chips.flag([], (10, 10))
        with self.assertRaises(ValueError):
            chips.flag([(0, 0, 0)], (10, 10), stripes="x")


class FindChromeTest(unittest.TestCase):
    def test_env_wins(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "mychrome"
            p.write_text("#!/bin/sh\n")
            self.assertEqual(chrome.find_chrome({"CHROME_BIN": str(p), "PATH": ""}), str(p))

    def test_raises_when_nothing_found(self):
        with mock.patch.object(chrome.os.path, "isfile", return_value=False):
            with self.assertRaisesRegex(RuntimeError, "Chrome not found: set CHROME_BIN"):
                chrome.find_chrome({"PATH": ""})

    def test_env_pointing_nowhere_is_skipped(self):
        with mock.patch.object(chrome.os.path, "isfile", return_value=False):
            with self.assertRaises(RuntimeError):
                chrome.find_chrome({"CHROME_BIN": "/nonexistent/x", "PATH": ""})


def _fake(d, body):
    p = Path(d) / "fakechrome"
    p.write_text("#!/bin/sh\n" + body)
    p.chmod(p.stat().st_mode | stat.S_IEXEC)
    return str(p)


class ShotTest(unittest.TestCase):
    def test_failing_chrome_raises_with_stderr_tail(self):
        with tempfile.TemporaryDirectory() as d:
            fake = _fake(d, "echo 'boom: gpu died' >&2\nexit 1\n")
            html = Path(d) / "a.html"
            html.write_text("<html></html>")
            with mock.patch.dict(os.environ, {"CHROME_BIN": fake}):
                with self.assertRaisesRegex(RuntimeError, "boom: gpu died"):
                    chrome.shot(html, Path(d) / "o.png", size=(100, 50))
                with self.assertRaisesRegex(RuntimeError, "boom: gpu died"):
                    chrome.print_pdf(html, Path(d) / "o.pdf")

    def test_missing_output_raises(self):
        with tempfile.TemporaryDirectory() as d:
            fake = _fake(d, "exit 0\n")
            html = Path(d) / "a.html"
            html.write_text("<html></html>")
            with mock.patch.dict(os.environ, {"CHROME_BIN": fake}):
                with self.assertRaises(RuntimeError):
                    chrome.shot(html, Path(d) / "o.png", size=(100, 50))

    def test_smaller_output_raises_larger_is_cropped(self):
        with tempfile.TemporaryDirectory() as d:
            html = Path(d) / "a.html"
            html.write_text("<html></html>")
            for w, h, ok in [(80, 50, False), (120, 90, True)]:
                src = Path(d) / f"src{w}.png"
                Image.new("RGB", (w, h), "red").save(src)
                fake = _fake(d, 'for a in "$@"; do case "$a" in --screenshot=*) cp '
                                f'"{src}" "${{a#--screenshot=}}";; esac; done\n')
                out = Path(d) / f"o{w}.png"
                with mock.patch.dict(os.environ, {"CHROME_BIN": fake}):
                    if ok:
                        chrome.shot(html, out, size=(100, 50))
                        with Image.open(out) as im:
                            self.assertEqual(im.size, (100, 50))
                    else:
                        with self.assertRaisesRegex(RuntimeError, "smaller"):
                            chrome.shot(html, out, size=(100, 50))

    @unittest.skipUnless(_real_chrome(), "Chrome not found")
    def test_real_chrome_exact_size(self):
        with tempfile.TemporaryDirectory() as d:
            html = Path(d) / "a.html"
            html.write_text("<html><body style='margin:0;background:#fa0'>x</body></html>")
            out = Path(d) / "o.png"
            chrome.shot(html, out, size=(320, 200))
            with Image.open(out) as im:
                self.assertEqual(im.size, (320, 200))


class CliTest(unittest.TestCase):
    def test_shot_bad_size(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            rc = cli.main(["shot", "a.html", "o.png", "--size", "big"])
        self.assertEqual(rc, 1)
        self.assertIn("--size", err.getvalue())

    def test_shot_failure_exit_1(self):
        with tempfile.TemporaryDirectory() as d:
            fake = _fake(d, "echo nope >&2\nexit 2\n")
            html = Path(d) / "a.html"
            html.write_text("x")
            err = io.StringIO()
            with mock.patch.dict(os.environ, {"CHROME_BIN": fake}), contextlib.redirect_stderr(err):
                rc = cli.main(["shot", str(html), str(Path(d) / "o.png"), "--size", "100x50"])
            self.assertEqual(rc, 1)
            self.assertIn("nope", err.getvalue())


class ChromeSilentFailureTest(unittest.TestCase):
    def test_missing_html_raises(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(FileNotFoundError):
                chrome.shot(Path(d) / "nope.html", Path(d) / "o.png")
            with self.assertRaises(FileNotFoundError):
                chrome.print_pdf(Path(d) / "nope.html", Path(d) / "o.pdf")
            with self.assertRaises(FileNotFoundError):
                chrome.shot(d, Path(d) / "o.png")

    def test_virtual_time_budget_in_both_commands(self):
        with tempfile.TemporaryDirectory() as d:
            html = Path(d) / "a.html"
            html.write_text("<html></html>")
            for call in (lambda: chrome.shot(html, Path(d) / "o.png"),
                         lambda: chrome.print_pdf(html, Path(d) / "o.pdf")):
                with mock.patch.object(chrome, "_run") as run:
                    with self.assertRaises(RuntimeError):
                        call()
                self.assertIn("--virtual-time-budget=5000", run.call_args.args[0])


if __name__ == "__main__":
    unittest.main()


class ChromeBinMissingTest(unittest.TestCase):
    def test_set_but_missing_chrome_bin_is_an_error(self):
        # A typo in CHROME_BIN must not silently fall back to another browser.
        with self.assertRaises(RuntimeError) as ctx:
            chrome.find_chrome(env={"CHROME_BIN": "/nonexistent/chrome-typo", "PATH": ""})
        self.assertIn("/nonexistent/chrome-typo", str(ctx.exception))
