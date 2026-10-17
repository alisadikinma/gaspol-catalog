import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from tools.deckkit import __main__ as cli
from tools.deckkit import deckmd


def write_prompt(d, name, lines):
    body = 'intro\n\nLAYOUT: x\n\nTEXT:\n' + "\n".join(f'- {r}: "{t}"' for r, t in lines) + "\n\nguard\n"
    (Path(d) / name).write_text(body, encoding="utf-8")


class ReviewHtmlTest(unittest.TestCase):
    MD = "# Deck\n\n## Slide 01\n- headline: Hello\n\n## Slide 02\n- headline: Bye\n"

    def test_is_standalone_html_with_title(self):
        out = deckmd.review_html(self.MD, "My Deck")
        self.assertTrue(out.lstrip().lower().startswith("<!doctype html>"))
        self.assertIn("<style>", out)
        self.assertIn("<title>My Deck</title>", out)
        self.assertIn('name="viewport"', out)

    def test_every_heading_and_card(self):
        out = deckmd.review_html(self.MD, "T")
        self.assertIn("Slide 01", out)
        self.assertIn("Slide 02", out)
        self.assertEqual(out.count('class="card"'), 2)

    def test_escapes_script(self):
        out = deckmd.review_html("## A <b>\n- x: <script>alert(1)</script>\n", "<i>T</i>")
        self.assertIn("&lt;script&gt;", out)
        self.assertNotIn("<script>", out)
        self.assertIn("A &lt;b&gt;", out)
        self.assertIn("&lt;i&gt;T&lt;/i&gt;", out)

    def test_comments_and_front_matter_dropped(self):
        out = deckmd.review_html("---\nmarp: true\n---\n<!-- secret -->\n## S\ntext\n", "T")
        self.assertNotIn("secret", out)
        self.assertNotIn("marp", out)

    def test_empty_input_still_valid(self):
        out = deckmd.review_html("", "T")
        self.assertIn("</html>", out)


class FromPromptsTest(unittest.TestCase):
    def test_numeric_order_and_bullets(self):
        with tempfile.TemporaryDirectory() as d:
            write_prompt(d, "slide-10.md", [("headline", "Ten")])
            write_prompt(d, "slide-02.md", [("eyebrow", "Two"), ("headline", "Two <b>")])
            md = deckmd.from_prompts(d)
        self.assertLess(md.index("## Slide 02"), md.index("## Slide 10"))
        self.assertIn("- eyebrow: Two", md)
        self.assertIn("- headline: Two <b>", md)
        self.assertNotIn("guard", md)

    def test_ignores_other_files_and_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            write_prompt(d, "slide-01.md", [("headline", "One")])
            write_prompt(d, "notes.md", [("headline", "Nope")])
            (Path(d) / "manifest.json").write_text("{}")
            (Path(d) / "_rejected").mkdir()
            write_prompt(Path(d) / "_rejected", "slide-03.md", [("headline", "Bad")])
            md = deckmd.from_prompts(d)
        self.assertIn("## Slide 01", md)
        self.assertNotIn("Nope", md)
        self.assertNotIn("Slide 03", md)

    def test_empty_dir_raises(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, "no slide-NN.md in "):
                deckmd.from_prompts(d)

    def test_roundtrip_to_review(self):
        with tempfile.TemporaryDirectory() as d:
            write_prompt(d, "slide-01.md", [("headline", "A & B")])
            out = deckmd.review_html(deckmd.from_prompts(d), "T")
        self.assertIn("Slide 01", out)
        self.assertIn("A &amp; B", out)


class CliTest(unittest.TestCase):
    def run_cli(self, *argv):
        err = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            rc = cli.main(list(argv))
        return rc, err.getvalue()

    def test_deckmd_then_review(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "prompts"
            p.mkdir()
            write_prompt(p, "slide-01.md", [("headline", "Hi")])
            rc, _ = self.run_cli("deckmd", str(p), str(Path(d) / "deck.md"))
            self.assertEqual(rc, 0)
            rc, _ = self.run_cli("review", str(Path(d) / "deck.md"), str(Path(d) / "r.html"), "--title", "Deck T")
            self.assertEqual(rc, 0)
            html = (Path(d) / "r.html").read_text(encoding="utf-8")
        self.assertIn("<title>Deck T</title>", html)
        self.assertIn("Slide 01", html)

    def test_deckmd_empty_dir_fails_cleanly(self):
        with tempfile.TemporaryDirectory() as d:
            rc, err = self.run_cli("deckmd", d, str(Path(d) / "o.md"))
        self.assertEqual(rc, 1)
        self.assertIn("FAIL: no slide-NN.md in", err)


if __name__ == "__main__":
    unittest.main()
