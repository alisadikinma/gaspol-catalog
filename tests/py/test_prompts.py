import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from tools.deckkit import __main__ as cli
from tools.deckkit import prompts

PRESET = {
    "name": "t",
    "intro": "INTRO {language} {seller} {audience}.",
    "style": "STYLE for {seller}.",
    "guard": "RULES {seller}{ai}. No people, no faces, no hands. End.",
    "ai_clause": " plus AI",
    "people_clause_from": "No people, no faces, no hands. ",
    "people_clause_to": "No people other than the figures described. ",
    "text_header": "TEXT:",
    "roles": {"head": "headline, large bold navy"},
    "palette": {},
    "fonts": {},
}
HOUSE = {"seller": "ContohAI", "preset": "isometrik-terang", "language": "Indonesian"}


def slide(n, **kw):
    s = {"n": n, "sid": f"s{n}", "layout": f"lay{n}", "visual": f"vis{n}",
         "text": [["head", f"Judul {n}"]], "refs": [], "ai": False, "people": False, "extra": ""}
    s.update(kw)
    return s


class Base(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.addCleanup(self._t.cleanup)
        self.dir = Path(self._t.name)

    def spec(self, slides, **top):
        data = {"audience": "a distributor", "client": "PT X", "ref_dir": "ref", "slides": slides}
        data.update(top)
        p = self.dir / "slides.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        return p

    def build(self, slides, house=HOUSE, **kw):
        return prompts.build(self.spec(slides), house=house, preset=PRESET_NAME, **kw)


PRESET_NAME = "isometrik-terang"


class RenderPromptTest(unittest.TestCase):
    CTX = {"seller": "ContohAI", "language": "Indonesian", "audience": "a distributor"}

    def test_exact_layout(self):
        out = prompts.render_prompt(slide(2), PRESET, self.CTX)
        self.assertEqual(out, (
            "INTRO Indonesian ContohAI a distributor.\n\n"
            "LAYOUT: lay2\n\n"
            "VISUAL: vis2\n\n"
            "STYLE for ContohAI.\n\n"
            'TEXT:\n- headline, large bold navy: "Judul 2"\n\n'
            "RULES ContohAI. No people, no faces, no hands. End."))

    def test_ai_true_adds_clause(self):
        self.assertIn("RULES ContohAI plus AI.", prompts.render_prompt(slide(2, ai=True), PRESET, self.CTX))

    def test_ai_false_no_clause(self):
        out = prompts.render_prompt(slide(2), PRESET, self.CTX)
        self.assertNotIn("plus AI", out)
        self.assertNotIn("{ai}", out)

    def test_people_swaps_clause(self):
        out = prompts.render_prompt(slide(2, people=True), PRESET, self.CTX)
        self.assertIn("No people other than the figures described. End.", out)
        self.assertNotIn("No people, no faces", out)

    def test_extra_empty_vs_set(self):
        self.assertIn("\n\nSTYLE for ContohAI.\n\nTEXT:", prompts.render_prompt(slide(2), PRESET, self.CTX))
        out = prompts.render_prompt(slide(2, extra="More."), PRESET, self.CTX)
        self.assertIn("\n\nSTYLE for ContohAI. More.\n\nTEXT:", out)

    def test_literal_role_kept(self):
        s = slide(2, text=[["eyebrow, small caps", "A"], ["head", "B"]])
        out = prompts.render_prompt(s, PRESET, self.CTX)
        self.assertIn('- eyebrow, small caps: "A"\n- headline, large bold navy: "B"', out)

    def test_quote_in_text_names_slide_and_role(self):
        s = slide(7, text=[["head", 'say "hi"']])
        with self.assertRaises(ValueError) as c:
            prompts.render_prompt(s, PRESET, self.CTX)
        self.assertIn("slide 7", str(c.exception))
        self.assertIn("headline, large bold navy", str(c.exception))

    def test_empty_text_refused(self):
        for bad in ([], None):
            with self.assertRaises(ValueError) as c:
                prompts.render_prompt(slide(3, text=bad), PRESET, self.CTX)
            self.assertIn("slide 3", str(c.exception))
            self.assertIn("text", str(c.exception))


class BuildTest(Base):
    def test_writes_files_and_manifest(self):
        n = self.build([slide(2), slide(10)])
        self.assertEqual(n, 2)
        out = self.dir / "prompts"
        self.assertTrue((out / "slide-02.md").is_file())
        self.assertTrue((out / "slide-10.md").is_file())
        man = json.loads((out / "manifest.json").read_text())
        self.assertEqual([m["n"] for m in man], [2, 10])
        self.assertEqual(man[0]["prompt_file"], "prompts/slide-02.md")
        self.assertEqual(man[0]["sid"], "s2")
        self.assertIn("ContohAI", (out / "slide-02.md").read_text())

    def test_refs_house_first_then_slide_absolute(self):
        (self.dir / "ref").mkdir()
        (self.dir / "ref" / "a.jpg").write_bytes(b"x")
        (self.dir / "style.png").write_bytes(b"x")
        house = dict(HOUSE, style_refs=[str(self.dir / "style.png")])
        self.build([slide(2, refs=["a.jpg"])], house=house)
        man = json.loads((self.dir / "prompts" / "manifest.json").read_text())
        self.assertEqual(man[0]["refs"], [str((self.dir / "style.png").resolve()),
                                           str((self.dir / "ref" / "a.jpg").resolve())])
        self.assertTrue(all(Path(r).is_absolute() for r in man[0]["refs"]))

    def test_missing_ref_names_path(self):
        with self.assertRaises(ValueError) as c:
            self.build([slide(2, refs=["gone.jpg"])])
        self.assertIn("gone.jpg", str(c.exception))
        self.assertIn("slide 2", str(c.exception))
        self.assertFalse((self.dir / "prompts").exists())

    def test_duplicate_n_names_slide(self):
        with self.assertRaises(ValueError) as c:
            self.build([slide(2), slide(2, sid="other")])
        self.assertIn("duplicate", str(c.exception))
        self.assertIn("2", str(c.exception))

    def test_duplicate_footer_text_names_both_slides(self):
        a = slide(3, text=[["head", "A"], ["footer line", "Sumber X"]])
        b = slide(5, text=[["head", "B"], ["Band, bottom", "Sumber X"]])
        c = slide(6, text=[["footer", "Sumber Y"], ["band", "Sumber X"]])
        with self.assertRaises(ValueError) as ctx:
            self.build([a, b, c])
        self.assertIn("slide 3", str(ctx.exception))
        self.assertIn("slide 5", str(ctx.exception))

    def test_same_text_in_non_footer_roles_allowed(self):
        self.build([slide(2, text=[["head", "Sama"]]), slide(3, text=[["head", "Sama"]])])

    def test_only_writes_subset_manifest_all(self):
        n = self.build([slide(2), slide(3)], only=[2])
        self.assertEqual(n, 1)
        out = self.dir / "prompts"
        self.assertTrue((out / "slide-02.md").is_file())
        self.assertFalse((out / "slide-03.md").exists())
        self.assertEqual([m["n"] for m in json.loads((out / "manifest.json").read_text())], [2, 3])

    def test_only_unknown_slide_refused(self):
        with self.assertRaises(ValueError) as c:
            self.build([slide(2)], only=[9])
        self.assertIn("9", str(c.exception))

    def test_house_absent_refusal(self):
        with self.assertRaises(ValueError) as c:
            self.build([slide(2)], house=None)
        self.assertEqual(str(c.exception), "no seller: pass --house or set GASPOL_CATALOG_HOUSE")

    def test_preset_defaults_to_house_preset(self):
        p = prompts.build(self.spec([slide(2)]), house=HOUSE)
        self.assertEqual(p, 1)
        self.assertIn("A finished 16:9", (self.dir / "prompts" / "slide-02.md").read_text())

    def test_no_preset_anywhere_refused(self):
        with self.assertRaises(ValueError):
            prompts.build(self.spec([slide(2)]), house={"seller": "S"})

    def test_out_dir_override(self):
        out = self.dir / "elsewhere"
        prompts.build(self.spec([slide(2)]), house=HOUSE, preset=PRESET_NAME, out_dir=out)
        self.assertTrue((out / "slide-02.md").is_file())
        man = json.loads((out / "manifest.json").read_text())
        self.assertEqual(man[0]["prompt_file"], "elsewhere/slide-02.md")

    def test_bad_spec_missing_slides(self):
        p = self.dir / "slides.json"
        p.write_text("{}", encoding="utf-8")
        with self.assertRaises(ValueError):
            prompts.build(p, house=HOUSE, preset=PRESET_NAME)


class CliTest(Base):
    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = cli.main(list(argv))
        return rc, out.getvalue(), err.getvalue()

    def house_file(self):
        f = self.dir / "house.md"
        f.write_text("```json\n" + json.dumps(HOUSE) + "\n```\n", encoding="utf-8")
        return f

    def test_cli_builds(self):
        spec = self.spec([slide(2), slide(3)])
        rc, out, _ = self.run_cli("prompts", str(spec), "--house", str(self.house_file()), "--only", "2")
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), f"1 prompt -> {self.dir.resolve() / 'prompts'}")

    def test_cli_no_house_fails(self):
        spec = self.spec([slide(2)])
        import os
        old = os.environ.pop("GASPOL_CATALOG_HOUSE", None)
        self.addCleanup(lambda: os.environ.__setitem__("GASPOL_CATALOG_HOUSE", old) if old else None)
        rc, _, err = self.run_cli("prompts", str(spec))
        self.assertEqual(rc, 1)
        self.assertEqual(err.strip(), "FAIL: no seller: pass --house or set GASPOL_CATALOG_HOUSE")


if __name__ == "__main__":
    unittest.main()
