"""CAT-2 code-review findings 1-11: one test class per finding group."""
import contextlib
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path

try:
    import numpy as np
    from PIL import Image, ImageDraw
except ImportError:
    raise unittest.SkipTest('needs Pillow + numpy: use the gaspol-video venv python')

from tools.deckkit import __main__ as cli
from tools.deckkit import fonts, gen, patch, prompts, watermark
from tests.py.test_prompts import HOUSE, PRESET_NAME, slide


def _png_bytes(color=(200, 30, 30)):
    b = io.BytesIO()
    Image.new("RGB", (160, 90), color).save(b, "PNG")
    return b.getvalue()


def _cli(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = cli.main(argv)
    return rc, out.getvalue(), err.getvalue()


class Tmp(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.addCleanup(self._t.cleanup)
        self.dir = Path(self._t.name).resolve()

    def spec(self, slides, **top):
        data = {"audience": "a distributor", "ref_dir": "ref", "slides": slides}
        data.update(top)
        p = self.dir / "slides.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        return p

    def build(self, slides, house=HOUSE, **kw):
        return prompts.build(self.spec(slides), house=house, preset=PRESET_NAME, **kw)


class RoundTripTest(Tmp):
    """Finding 1 + 2."""

    def setUp(self):
        super().setUp()
        self.src = self.dir / "src.png"
        self.src.write_bytes(_png_bytes())
        self.seen = []

    def fake(self, **kw):
        self.seen.append(kw["prompt"])
        return f"OK local: {self.src}"

    def test_default_out(self):
        self.build([slide(2), slide(3)])
        res = gen.run(self.dir / "prompts" / "manifest.json", self.fake, model="m")
        self.assertEqual(res, [(2, "OK"), (3, "OK")])
        self.assertTrue((self.dir / "renders" / "slide-02.png").is_file())

    def test_out_nested_deeper(self):
        out = self.dir / "a" / "b" / "prompts"
        self.build([slide(2)], out_dir=out)
        man = json.loads((out / "manifest.json").read_text())
        self.assertEqual(man[0]["prompt_file"], "slide-02.md")
        self.assertEqual(gen.run(out / "manifest.json", self.fake, model="m", out_dir=self.dir / "r"), [(2, "OK")])

    def test_out_outside_spec_dir(self):
        with tempfile.TemporaryDirectory() as other:
            out = Path(other).resolve() / "p"
            self.build([slide(2)], out_dir=out)
            self.assertEqual(gen.run(out / "manifest.json", self.fake, model="m",
                                     out_dir=self.dir / "r", raw_dir=self.dir / "raw"), [(2, "OK")])

    def test_absolute_prompt_file_still_accepted(self):
        pf = self.dir / "abs.md"
        pf.write_text("P\n", encoding="utf-8")
        m = self.dir / "sub" / "manifest.json"
        m.parent.mkdir()
        m.write_text(json.dumps([{"n": 1, "prompt_file": str(pf), "refs": []}]), encoding="utf-8")
        self.assertEqual(gen.run(m, self.fake, model="m", out_dir=self.dir / "r"), [(1, "OK")])

    def test_raw_dir_with_space(self):
        self.build([slide(2)])
        raw = self.dir / "raw dir"
        raw.mkdir()
        spaced = raw / "my image.png"
        spaced.write_bytes(_png_bytes())
        res = gen.run(self.dir / "prompts" / "manifest.json", lambda **kw: f"OK done local: {spaced}",
                      model="m", raw_dir=raw)
        self.assertEqual(res, [(2, "OK")])


class RevisionLogTest(Tmp):
    """Finding 3."""

    def read(self, n=2):
        return (self.dir / "prompts" / f"slide-{n:02d}.md").read_text(encoding="utf-8")

    def test_new_file_ends_with_empty_revision_log(self):
        self.build([slide(2)])
        t = self.read()
        self.assertTrue(t.endswith("\n\nREVISION LOG\n"), repr(t[-40:]))

    def test_log_field_appends_dated_line(self):
        self.build([slide(2, log="guard restored")])
        import re
        self.assertRegex(self.read(), r"REVISION LOG\n- \d{4}-\d{2}-\d{2} guard restored\n\Z")

    def test_rewrite_carries_old_lines_and_appends(self):
        self.build([slide(2, log="first")])
        self.build([slide(2, text=[["head", "Baru"]], log="second")])
        t = self.read()
        self.assertIn('"Baru"', t)
        tail = t.split("REVISION LOG\n")[1].splitlines()
        self.assertEqual(len(tail), 2)
        self.assertTrue(tail[0].endswith(" first") and tail[1].endswith(" second"))

    def test_unchanged_no_log_is_byte_identical(self):
        self.build([slide(2, log="first")])
        before = self.read()
        self.build([slide(2)])
        self.assertEqual(self.read(), before)

    def test_hand_added_line_survives(self):
        self.build([slide(2)])
        p = self.dir / "prompts" / "slide-02.md"
        p.write_text(p.read_text() + "- 2026-01-01 by hand\n", encoding="utf-8")
        self.build([slide(2, text=[["head", "Baru"]])])
        self.assertTrue(self.read().endswith("REVISION LOG\n- 2026-01-01 by hand\n"))

    def test_log_must_be_string(self):
        with self.assertRaisesRegex(ValueError, "slide 2.*log"):
            self.build([slide(2, log=5)])

    def test_render_prompt_ends_with_heading(self):
        ctx = {"seller": "S", "language": "L", "audience": "A"}
        from tests.py.test_prompts import PRESET
        self.assertTrue(prompts.render_prompt(slide(2), PRESET, ctx).endswith("\n\nREVISION LOG"))


class ValidationTest(Tmp):
    """Finding 4."""

    def test_non_string_text_and_role(self):
        with self.assertRaisesRegex(ValueError, "slide 2.*text"):
            self.build([slide(2, text=[["head", 250000]])])
        with self.assertRaisesRegex(ValueError, "slide 2.*role"):
            self.build([slide(2, text=[[5, "x"]])])

    def test_missing_keys_name_slide_and_field(self):
        for key in ("layout", "visual", "text"):
            s = slide(4)
            del s[key]
            with self.assertRaisesRegex(ValueError, f"slide 4.*{key}"):
                self.build([s])

    def test_missing_n_names_index(self):
        s = slide(1)
        del s["n"]
        with self.assertRaisesRegex(ValueError, r"index 0.*'n'"):
            self.build([s])

    def test_cli_returns_1_not_traceback(self):
        spec = self.spec([slide(2, text=[["head", 250000]])])
        h = self.dir / "h.md"
        h.write_text("```json\n" + json.dumps(HOUSE) + "\n```\n", encoding="utf-8")
        rc, _, err = _cli(["prompts", str(spec), "--house", str(h)])
        self.assertEqual(rc, 1)
        self.assertIn("slide 2", err)


class VersionedNamesTest(Tmp):
    """Finding 5."""

    def setUp(self):
        super().setUp()
        self.src = self.dir / "src.png"
        self.src.write_bytes(_png_bytes())

    def test_ver_makes_subdir(self):
        self.build([slide(2)])
        gen.run(self.dir / "prompts" / "manifest.json", lambda **kw: f"OK local: {self.src}", model="m", ver="r1")
        self.assertTrue((self.dir / "renders" / "r1" / "02.png").is_file())

    def test_ver_with_path_part_refused(self):
        self.build([slide(2)])
        with self.assertRaisesRegex(ValueError, "ver"):
            gen.run(self.dir / "prompts" / "manifest.json", lambda **kw: "x", model="m", ver="../x")

    def test_default_versioned_dir_matches_pdf_and_stamp_patterns(self):
        import re
        self.assertTrue(re.fullmatch(r"\d{2}\.png|slide-\d+\.png", "02.png"))

    def test_band_numbers_duplicate_page_refused(self):
        src, dst = self.dir / "s", self.dir / "d"
        src.mkdir()
        for n in ("01.png", "slide-01.png"):
            Image.new("RGB", (400, 300)).save(src / n)
        rc, _, err = _cli(["band", str(src), str(dst), "--text", "X", "--numbers", "--approved"])
        self.assertEqual(rc, 1)
        self.assertIn("same page number", err)


class PatchFixesTest(unittest.TestCase):
    """Findings 6, 8."""

    def test_emblem_text_default_font(self):
        em = patch.emblem_text("M", None, 30, (255, 255, 255), (0, 160, 255))
        self.assertEqual(em.width, em.height)

    def test_replace_line_light_text_on_dark_band(self):
        font = fonts.find_font()
        img = Image.new("RGB", (500, 200), (20, 30, 50))
        old = patch.render_text("OLD TITLE", font, 30, (240, 200, 60, 255))
        patch.paste_text(img, old, (60, 100))
        box = (40, 60, 440, 120)
        out = patch.replace_line(img, box, "NEW", font, dark=False)
        bb = patch.ink_bbox(out, box, dark=False)
        self.assertIsNotNone(bb)
        a = np.asarray(out).astype(int)[bb[1]:bb[3] + 1, bb[0]:bb[2] + 1].reshape(-1, 3)
        brightest = a[a.sum(axis=1).argmax()]
        self.assertLess(np.abs(brightest - np.array([240, 200, 60])).max(), 30)


class WatermarkLogoTest(Tmp):
    """Finding 7."""

    def test_transparent_logo(self):
        p = self.dir / "t.png"
        Image.new("RGBA", (60, 30), (0, 0, 0, 0)).save(p)
        with self.assertRaisesRegex(ValueError, "logo has no visible pixels"):
            watermark.mark(Image.new("RGB", (400, 300), "white"), logo=str(p), corner_text="")

    def test_uniform_opaque_logo(self):
        p = self.dir / "u.png"
        Image.new("RGB", (60, 30), (10, 90, 160)).save(p)
        with self.assertRaisesRegex(ValueError, "logo has no visible pixels"):
            watermark.mark(Image.new("RGB", (400, 300), "white"), logo=str(p), corner_text="")

    def test_uniform_alpha_full_logo(self):
        p = self.dir / "f.png"
        Image.new("RGBA", (60, 30), (10, 90, 160, 255)).save(p)
        with self.assertRaisesRegex(ValueError, "logo has no visible pixels"):
            watermark.mark(Image.new("RGB", (400, 300), "white"), logo=str(p), corner_text="")


class ApprovedGuardTest(Tmp):
    """Finding 9."""

    MSG = "page numbers are stamped only after the renders are approved: pass --approved"

    def setUp(self):
        super().setUp()
        self.src = self.dir / "s"
        self.src.mkdir()
        Image.new("RGB", (400, 300)).save(self.src / "01.png")

    def test_band_numbers_needs_approved(self):
        rc, _, err = _cli(["band", str(self.src), str(self.dir / "d"), "--text", "X", "--numbers"])
        self.assertEqual(rc, 1)
        self.assertIn(self.MSG, err)
        self.assertFalse((self.dir / "d" / "01.png").exists())

    def test_band_without_numbers_unaffected(self):
        rc, _, _ = _cli(["band", str(self.src), str(self.dir / "d"), "--text", "X"])
        self.assertEqual(rc, 0)

    def test_stamp_needs_approved(self):
        rc, _, err = _cli(["stamp", str(self.src), str(self.dir / "d")])
        self.assertEqual(rc, 1)
        self.assertIn(self.MSG, err)
        rc, out, _ = _cli(["stamp", str(self.src), str(self.dir / "d"), "--approved"])
        self.assertEqual(rc, 0)
        self.assertTrue((self.dir / "d" / "01.png").is_file())


class StaleRenderTest(Tmp):
    """Finding 10."""

    def setUp(self):
        super().setUp()
        self.src = self.dir / "src.png"
        self.src.write_bytes(_png_bytes())
        self.calls = 0

    def g(self, **kw):
        self.calls += 1
        return f"OK local: {self.src}"

    def man(self):
        return self.dir / "prompts" / "manifest.json"

    def test_manifest_sha_excludes_revision_log(self):
        self.build([slide(2, log="one")])
        m = json.loads(self.man().read_text())[0]
        text = (self.dir / "prompts" / "slide-02.md").read_text()
        body = text.split("\n\nREVISION LOG")[0]
        self.assertEqual(m["sha"], hashlib.sha256(body.encode("utf-8")).hexdigest())
        self.assertRegex(m["sha"], r"^[0-9a-f]{64}$")
        self.build([slide(2, log="two")])
        self.assertEqual(json.loads(self.man().read_text())[0]["sha"], m["sha"])
        self.build([slide(2, text=[["head", "Lain"]])])
        self.assertNotEqual(json.loads(self.man().read_text())[0]["sha"], m["sha"])

    def test_same_sha_exists_then_changed_is_stale(self):
        self.build([slide(2)])
        self.assertEqual(gen.run(self.man(), self.g, model="m"), [(2, "OK")])
        side = self.dir / "renders" / "slide-02.png.sha"
        self.assertTrue(side.is_file())
        self.assertEqual(gen.run(self.man(), self.g, model="m"), [(2, "exists")])
        self.build([slide(2, text=[["head", "Lain"]])])
        res = gen.run(self.man(), self.g, model="m")
        self.assertTrue(res[0][1].startswith("stale: prompt changed since render"), res)
        self.assertIn("prompts/_rejected/", res[0][1])
        self.assertEqual(self.calls, 1)   # never re-rendered, never overwritten

    def test_log_only_change_not_stale(self):
        self.build([slide(2)])
        gen.run(self.man(), self.g, model="m")
        self.build([slide(2, log="note")])
        self.assertEqual(gen.run(self.man(), self.g, model="m"), [(2, "exists")])

    def test_no_sidecar_no_manifest_sha_exists(self):
        (self.dir / "prompts").mkdir()
        (self.dir / "prompts" / "slide-01.md").write_text("P\n", encoding="utf-8")
        self.man().write_text(json.dumps([{"n": 1, "prompt_file": "slide-01.md", "refs": []}]))
        (self.dir / "renders").mkdir()
        (self.dir / "renders" / "slide-01.png").write_bytes(b"old")
        self.assertEqual(gen.run(self.man(), self.g, model="m"), [(1, "exists")])

    def test_no_sidecar_but_manifest_sha_is_stale(self):
        self.build([slide(2)])
        (self.dir / "renders").mkdir()
        (self.dir / "renders" / "slide-02.png").write_bytes(b"old")
        res = gen.run(self.man(), self.g, model="m")
        self.assertTrue(res[0][1].startswith("stale"))

    def test_hand_edit_of_prompt_file_is_stale(self):
        """Re-review B: a revision edits the prompt file; the manifest sha must not hide it."""
        self.build([slide(2)])
        gen.run(self.man(), self.g, model="m")
        pf = self.dir / "prompts" / "slide-02.md"
        pf.write_text(pf.read_text().replace("Judul 2", "Judul Dua"), encoding="utf-8")
        res = gen.run(self.man(), self.g, model="m")
        self.assertTrue(res[0][1].startswith("stale"), res)
        self.assertEqual(self.calls, 1)

    def test_render_after_hand_edit_then_exists(self):
        """Re-review B reverse: a fresh render from a hand-edited file is not reported stale later."""
        self.build([slide(2)])
        pf = self.dir / "prompts" / "slide-02.md"
        pf.write_text(pf.read_text().replace("Judul 2", "Judul Dua"), encoding="utf-8")
        self.assertEqual(gen.run(self.man(), self.g, model="m"), [(2, "OK")])
        self.assertEqual(gen.run(self.man(), self.g, model="m"), [(2, "exists")])

    def test_revision_log_not_sent_to_model(self):
        """Re-review A: the REVISION LOG names old defect text; the model must never see it."""
        self.build([slide(2, log="hapus Hemat 30 persen ganda")])
        sent = []
        def g(**kw):
            sent.append(kw["prompt"])
            return f"OK local: {self.src}"
        gen.run(self.man(), g, model="m")
        self.assertNotIn("REVISION LOG", sent[0])
        self.assertNotIn("Hemat 30 persen", sent[0])
        self.assertIn("Judul 2", sent[0])

    def test_cli_stale_exit_1(self):
        self.build([slide(2)])
        h = self.dir / "house.md"
        h.write_text("```json\n" + json.dumps({"seller": "S", "preset": "p", "image_client": "/x",
                                               "image_model": "hm"}) + "\n```\n")
        from unittest import mock
        with mock.patch.object(gen, "load_generator", return_value=self.g):
            self.assertEqual(_cli(["gen", str(self.man()), "--house", str(h)])[0], 0)
            self.build([slide(2, text=[["head", "Lain"]])])
            rc, out, _ = _cli(["gen", str(self.man()), "--house", str(h)])
        self.assertEqual(rc, 1)
        self.assertIn("02 stale", out)


class StyleRefsTest(Tmp):
    """Finding 11."""

    def test_relative_resolves_against_house_dir(self):
        hd = self.dir / "house"
        hd.mkdir()
        (hd / "style.png").write_bytes(b"x")
        house = dict(HOUSE, style_refs=["style.png"])
        self.build([slide(2)], house=house, house_path=hd / "house.md")
        man = json.loads((self.dir / "prompts" / "manifest.json").read_text())
        self.assertEqual(man[0]["refs"], [str((hd / "style.png").resolve())])

    def test_relative_without_house_path_refused(self):
        with self.assertRaisesRegex(ValueError, "style_refs.*house_path"):
            self.build([slide(2)], house=dict(HOUSE, style_refs=["style.png"]))

    def test_cli_passes_house_path(self):
        hd = self.dir / "house"
        hd.mkdir()
        (hd / "style.png").write_bytes(b"x")
        h = hd / "house.md"
        h.write_text("```json\n" + json.dumps(dict(HOUSE, style_refs=["style.png"])) + "\n```\n")
        rc, _, err = _cli(["prompts", str(self.spec([slide(2)])), "--house", str(h)])
        self.assertEqual(rc, 0, err)


if __name__ == "__main__":
    unittest.main()
