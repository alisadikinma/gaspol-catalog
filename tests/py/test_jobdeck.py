import contextlib
import io
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from tools.deckkit import __main__ as cli
from tools.deckkit import chrome as chrome_mod
from tools.deckkit import jobdeck

FIXTURE = Path(__file__).parent / "fixtures" / "jobdeck"
DECK = (FIXTURE / "deck.html").read_text(encoding="utf-8")


def _real_chrome():
    try:
        return chrome_mod.find_chrome()
    except RuntimeError:
        return None


def png_runner(calls=None, fail_on=None, size=(1920, 1080)):
    """Fake Chrome: finds --screenshot=<png> in argv and writes a PNG there."""
    def run(argv, timeout):
        if calls is not None:
            calls.append(list(argv))
        if fail_on is not None and len(calls) == fail_on:
            raise RuntimeError("boom")
        shot = next(a for a in argv if a.startswith("--screenshot=")).split("=", 1)[1]
        Image.new("RGB", size, (10, 20, 30)).save(shot)
    return run


def pdf_pages(path):
    import re
    return len(re.findall(rb"/Type\s*/Page(?![s\w])", Path(path).read_bytes()))


class FillTest(unittest.TestCase):
    def test_replaces_inner_text_and_keeps_rest_byte_identical(self):
        out = jobdeck.fill(DECK, {"cover-head": "New *bold* head"})
        want = DECK.replace("Original <em>cover</em> head", "New <em>bold</em> head")
        self.assertEqual(out, want)

    def test_escapes_ampersand_and_quotes(self):
        out = jobdeck.fill(DECK, {"cover-sub": 'Fish & "chips"'})
        self.assertIn("Fish &amp; &quot;chips&quot;", out)

    def test_empty_slots_unchanged(self):
        self.assertEqual(jobdeck.fill(DECK, {}), DECK)

    def test_multiple_slots(self):
        out = jobdeck.fill(DECK, {"cover-eye": "A", "cta-sub": "B"})
        self.assertIn(">A</p>", out)
        self.assertIn(">B</p>", out)

    def test_unknown_slot_refused(self):
        with self.assertRaises(ValueError) as cm:
            jobdeck.fill(DECK, {"nope": "x"})
        self.assertIn("nope", str(cm.exception))

    def test_slot_not_in_deck_refused(self):
        with self.assertRaises(ValueError) as cm:
            jobdeck.fill(DECK, {"cta-tile-1-title": "x"})
        self.assertIn("cta-tile-1-title", str(cm.exception))

    def test_too_long_refused_with_explicit_max(self):
        with self.assertRaises(ValueError) as cm:
            jobdeck.fill(DECK, {"cover-eye": "x" * 41})
        self.assertIn("cover-eye", str(cm.exception))
        jobdeck.fill(DECK, {"cover-eye": "x" * 40})

    def test_default_max_is_120(self):
        jobdeck.fill(DECK, {"cover-sub": "x" * 120})
        with self.assertRaises(ValueError) as cm:
            jobdeck.fill(DECK, {"cover-sub": "x" * 121})
        self.assertIn("cover-sub", str(cm.exception))

    def test_emphasis_markers_do_not_count(self):
        jobdeck.fill(DECK, {"cover-eye": "*" + "x" * 40 + "*"})

    def test_angle_brackets_refused(self):
        for bad in ("a<b", "a>b", "<script>"):
            with self.subTest(bad=bad), self.assertRaises(ValueError) as cm:
                jobdeck.fill(DECK, {"cover-head": bad})
            self.assertIn("cover-head", str(cm.exception))

    def test_non_string_refused(self):
        with self.assertRaises(ValueError) as cm:
            jobdeck.fill(DECK, {"cover-head": 5})
        self.assertIn("cover-head", str(cm.exception))

    def test_nested_slot_refused(self):
        nested = ('<div data-job="cover-head"><span data-job="cover-sub">x</span></div>')
        with self.assertRaises(ValueError) as cm:
            jobdeck.fill(nested, {"cover-sub": "y"})
        self.assertIn("nested", str(cm.exception))

    def test_nested_same_tag_inside_slot_finds_right_end(self):
        html = '<div data-job="cover-head">a<div>b</div>c</div><p>after</p>'
        self.assertEqual(jobdeck.fill(html, {"cover-head": "Z"}),
                         '<div data-job="cover-head">Z</div><p>after</p>')

    def test_void_slot_element_refused(self):
        with self.assertRaises(ValueError):
            jobdeck.fill('<img data-job="cover-head" src="x.png">', {"cover-head": "x"})

    def test_bad_max_attribute_refused(self):
        html = '<p data-job="cover-head" data-job-max="abc">x</p>'
        with self.assertRaises(ValueError) as cm:
            jobdeck.fill(html, {"cover-head": "x"})
        self.assertIn("cover-head", str(cm.exception))

    def test_crlf_deck_offsets(self):
        crlf = DECK.replace("\n", "\r\n")
        out = jobdeck.fill(crlf, {"cta-head": "Hi"})
        self.assertEqual(out, crlf.replace("Original CTA head", "Hi"))


class SlideIdsTest(unittest.TestCase):
    def test_ids_in_order(self):
        self.assertEqual(jobdeck.slide_ids(DECK), ["s1", "s2"])

    def test_ignores_non_slide_and_no_id(self):
        html = '<div class="slide" id="a"></div><div class="x" id="b"></div><div class="slide"></div>'
        self.assertEqual(jobdeck.slide_ids(html), ["a"])


class RenderTest(unittest.TestCase):
    def setUp(self):
        self.td = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.td, True)
        self.deck_dir = self.td / "deck"
        shutil.copytree(FIXTURE, self.deck_dir)
        self.deck = self.deck_dir / "deck.html"
        self.out = self.td / "out" / "job.pdf"

    def leftovers(self):
        return sorted(p.name for p in self.deck_dir.glob("_jobdeck_*"))

    def test_one_page_per_slide_and_temp_removed(self):
        calls = []
        path = jobdeck.render(self.deck, {"cover-head": "Hi"}, self.out, chrome=png_runner(calls))
        self.assertEqual(Path(path), self.out)
        self.assertEqual(pdf_pages(self.out), 2)
        self.assertEqual(len(calls), 2)
        self.assertEqual(self.leftovers(), [])

    def test_chrome_args_and_page_content(self):
        seen = []

        def run(argv, timeout):
            page = Path(argv[-1].removeprefix("file://"))
            self.assertEqual(page.parent, self.deck_dir.resolve())
            self.assertTrue(page.name.startswith("_jobdeck_"))
            text = page.read_text(encoding="utf-8")
            seen.append(text)
            self.assertIn("New head", text)
            self.assertIn("display:none !important}", text)
            self.assertLessEqual(timeout, 50)
            for flag in ("--headless=new", "--disable-gpu", "--hide-scrollbars",
                         "--window-size=1920,1080", "--virtual-time-budget=8000"):
                self.assertIn(flag, argv)
            png_runner()(argv, timeout)

        jobdeck.render(self.deck, {"cover-head": "New head"}, self.out, chrome=run)
        self.assertIn('.slide:not([id="s1"]){display:none !important}', seen[0])
        self.assertIn('.slide:not([id="s2"]){display:none !important}', seen[1])
        # appended inside the last style block, before </style>
        self.assertLess(seen[0].index("display:none !important"), seen[0].index("</style>"))

    def test_temp_removed_when_runner_raises(self):
        calls = []
        with self.assertRaises(RuntimeError):
            jobdeck.render(self.deck, {}, self.out, chrome=png_runner(calls, fail_on=2))
        self.assertEqual(self.leftovers(), [])
        self.assertFalse(self.out.exists())

    def test_bad_slot_raises_before_chrome(self):
        calls = []
        with self.assertRaises(ValueError):
            jobdeck.render(self.deck, {"bogus": "x"}, self.out, chrome=png_runner(calls))
        self.assertEqual(calls, [])
        self.assertEqual(self.leftovers(), [])

    def test_missing_chrome(self):
        old = {k: os.environ.get(k) for k in ("CHROME_BIN", "PATH")}
        self.addCleanup(lambda: [os.environ.__setitem__(k, v) if v is not None
                                 else os.environ.pop(k, None) for k, v in old.items()])
        os.environ.pop("CHROME_BIN", None)
        os.environ["PATH"] = ""
        orig = chrome_mod.MAC_APP
        chrome_mod.MAC_APP = "/nonexistent/chrome"
        self.addCleanup(setattr, chrome_mod, "MAC_APP", orig)
        with self.assertRaisesRegex(RuntimeError, "chrome not found"):
            jobdeck.render(self.deck, {}, self.out)
        self.assertEqual(self.leftovers(), [])

    def test_missing_deck(self):
        with self.assertRaises(FileNotFoundError):
            jobdeck.render(self.td / "nope.html", {}, self.out, chrome=png_runner())

    def test_small_screenshot_raises(self):
        with self.assertRaises(RuntimeError):
            jobdeck.render(self.deck, {}, self.out, chrome=png_runner(size=(800, 600)))
        self.assertEqual(self.leftovers(), [])

    def test_no_slides_refused(self):
        bare = self.deck_dir / "bare.html"
        bare.write_text("<style></style><p>x</p>", encoding="utf-8")
        with self.assertRaises(ValueError):
            jobdeck.render(bare, {}, self.out, chrome=png_runner())

    def _deck_with_ids(self, *ids):
        body = "".join(f"<div id='{i}' class='slide'>{i}</div>" for i in ids)
        d = self.deck_dir / "ids.html"
        d.write_text(f"<style>.slide{{width:1px}}</style>{body}", encoding="utf-8")
        return d

    def test_slide_ids_digit_leading_and_dot_use_attribute_selector(self):
        seen = []

        def run(argv, timeout):
            seen.append(Path(argv[-1].removeprefix("file://")).read_text(encoding="utf-8"))
            png_runner()(argv, timeout)

        jobdeck.render(self._deck_with_ids("1st", "a.b"), {}, self.out, chrome=run)
        self.assertIn('.slide:not([id="1st"]){display:none !important}', seen[0])
        self.assertIn('.slide:not([id="a.b"]){display:none !important}', seen[1])
        self.assertNotIn(":not(#", seen[0])

    def test_slide_id_with_quote_or_backslash_refused(self):
        for bad in ('a"b', "a\\b"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                jobdeck.render(self._deck_with_ids(bad),
                               {}, self.out, chrome=png_runner())
        self.assertEqual(self.leftovers(), [])

    def test_total_deadline_shared_across_slides(self):
        import time
        from unittest import mock
        times = []
        clock = [1000.0]

        def run(argv, timeout):
            times.append(timeout)
            clock[0] += 20
            png_runner()(argv, timeout)

        with mock.patch.object(jobdeck.time, "monotonic", lambda: clock[0]):
            jobdeck.render(self.deck, {}, self.out, chrome=run, timeout=50)
        self.assertEqual(times, [50, 30])

    def test_deadline_exhausted_raises_and_cleans(self):
        from unittest import mock
        clock = [0.0]

        def run(argv, timeout):
            clock[0] += 100
            png_runner()(argv, timeout)

        with mock.patch.object(jobdeck.time, "monotonic", lambda: clock[0]):
            with self.assertRaisesRegex(RuntimeError, "time"):
                jobdeck.render(self.deck, {}, self.out, chrome=run, timeout=50)
        self.assertEqual(self.leftovers(), [])
        self.assertFalse(self.out.exists())

    def test_default_timeout_is_50(self):
        import inspect
        self.assertEqual(inspect.signature(jobdeck.render).parameters["timeout"].default, 50)

    def test_two_renders_do_not_share_page_names(self):
        names = []

        def run(argv, timeout):
            names.append(Path(argv[-1].removeprefix("file://")).name)
            png_runner()(argv, timeout)

        jobdeck.render(self.deck, {}, self.out, chrome=run)
        jobdeck.render(self.deck, {}, self.out, chrome=run)
        self.assertEqual(len(set(names)), 4)
        self.assertTrue(all(n.startswith("_jobdeck_") and n.endswith(".html") for n in names))

    def test_other_renders_pages_survive(self):
        other = self.deck_dir / "_jobdeck_other.html"
        other.write_text("x")
        jobdeck.render(self.deck, {}, self.out, chrome=png_runner())
        self.assertTrue(other.exists())

    def test_pdf_written_atomically(self):
        self.out.parent.mkdir(parents=True)
        self.out.write_bytes(b"OLD")
        with self.assertRaises(RuntimeError):
            jobdeck.render(self.deck, {}, self.out, chrome=png_runner(calls=[], fail_on=2))
        self.assertEqual(self.out.read_bytes(), b"OLD")
        jobdeck.render(self.deck, {}, self.out, chrome=png_runner())
        self.assertTrue(self.out.read_bytes().startswith(b"%PDF"))
        self.assertEqual([p.name for p in self.out.parent.iterdir()], ["job.pdf"])

    @unittest.skipUnless(_real_chrome(), "Chrome not installed")
    def test_real_chrome(self):
        jobdeck.render(self.deck, {"cover-head": "Real *Chrome* run"}, self.out, timeout=120)
        self.assertEqual(pdf_pages(self.out), 2)
        self.assertEqual(self.leftovers(), [])
        try:
            import pymupdf as fitz
        except ImportError:
            return   # page count is checked; the colour check needs pymupdf
        with fitz.open(self.out) as doc:
            self.assertEqual(round(doc[0].rect.width / doc[0].rect.height, 2), round(1920 / 1080, 2))
            # slide 1 is pale blue, slide 2 pale green: proves each page shows its own slide
            c1 = doc[0].get_pixmap(dpi=20).pixel(2, 2)
            c2 = doc[1].get_pixmap(dpi=20).pixel(2, 2)
            self.assertNotEqual(c1, c2)
            self.assertGreater(c1[2], c1[1])   # blue-ish
            self.assertGreater(c2[1], c2[2])   # green-ish (grid slide not broken)


class CliTest(unittest.TestCase):
    def setUp(self):
        self.td = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.td, True)
        shutil.copytree(FIXTURE, self.td / "deck")
        self.deck = str(self.td / "deck" / "deck.html")
        self.out = str(self.td / "o.pdf")

    def slots(self, obj):
        p = self.td / "slots.json"
        p.write_text(obj if isinstance(obj, str) else json.dumps(obj), encoding="utf-8")
        return str(p)

    def run_cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = cli.main(["jobdeck", *args])
        return rc, out.getvalue(), err.getvalue()

    def test_bad_slot_exit_2_names_slot(self):
        rc, _, err = self.run_cli(self.deck, self.slots({"bogus": "x"}), self.out)
        self.assertEqual(rc, 2)
        self.assertIn("bogus", err)

    def test_bad_json_exit_2(self):
        rc, _, err = self.run_cli(self.deck, self.slots("{nope"), self.out)
        self.assertEqual(rc, 2)

    def test_slots_not_object_exit_2(self):
        rc, _, _ = self.run_cli(self.deck, self.slots("[1]"), self.out)
        self.assertEqual(rc, 2)

    def test_missing_deck_exit_2(self):
        rc, _, _ = self.run_cli(str(self.td / "none.html"), self.slots({}), self.out)
        self.assertEqual(rc, 2)

    def test_render_failure_exit_3(self):
        orig = jobdeck.render

        def boom(*a, **k):
            raise RuntimeError("chrome not found")
        jobdeck.render = boom
        self.addCleanup(setattr, jobdeck, "render", orig)
        rc, _, err = self.run_cli(self.deck, self.slots({}), self.out)
        self.assertEqual(rc, 3)
        self.assertIn("chrome not found", err)

    def test_render_oserror_exit_3(self):
        for exc in (FileNotFoundError("chrome"), PermissionError("ro"),
                    Image.UnidentifiedImageError("bad png"), OSError("disk full")):
            with self.subTest(exc=type(exc).__name__):
                orig = jobdeck.render

                def boom(*a, _e=exc, **k):
                    raise _e
                jobdeck.render = boom
                try:
                    rc, _, err = self.run_cli(self.deck, self.slots({}), self.out)
                finally:
                    jobdeck.render = orig
                self.assertEqual(rc, 3)
                self.assertIn("FAIL", err)

    def test_render_valueerror_still_exit_2(self):
        rc, _, _ = self.run_cli(self.deck, self.slots({"cover-head": "a<b"}), self.out)
        self.assertEqual(rc, 2)

    def test_timeout_option_passed(self):
        got = {}
        orig = jobdeck.render

        def fake(deck, slots, out, **k):
            got.update(k)
            return out
        jobdeck.render = fake
        self.addCleanup(setattr, jobdeck, "render", orig)
        rc, _, _ = self.run_cli(self.deck, self.slots({}), self.out, "--timeout", "12")
        self.assertEqual(rc, 0)
        self.assertEqual(got["timeout"], 12)

    def test_ok_exit_0_prints_path(self):
        orig = jobdeck.render
        jobdeck.render = lambda deck, slots, out, **k: out
        self.addCleanup(setattr, jobdeck, "render", orig)
        rc, out, _ = self.run_cli(self.deck, self.slots({"cover-head": "x"}), self.out)
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), self.out)


if __name__ == "__main__":
    unittest.main()
