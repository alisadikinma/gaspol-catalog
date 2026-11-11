import contextlib
import copy
import io
import json
import re
import tempfile
import unittest
from pathlib import Path

from tools.deckkit import __main__ as cli
from tools.deckkit import chrome, jdpage

FIXTURE = Path(__file__).parent / "fixtures" / "jdpage-good.json"


def good():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _real_chrome():
    try:
        return chrome.find_chrome()
    except RuntimeError:
        return None


def pdf_pages(path):
    """Page count read from the bytes: leaf nodes are '/Type /Page' not followed by 's'."""
    return len(re.findall(rb"/Type\s*/Page(?![s\w])", Path(path).read_bytes()))


def pdf_text(path):
    import pymupdf as fitz
    with fitz.open(path) as doc:
        return "\n".join(p.get_text() for p in doc)


class ValidateTest(unittest.TestCase):
    def bad(self, mutate, field):
        d = good()
        mutate(d)
        with self.assertRaises(ValueError) as cm:
            jdpage.validate(d)
        self.assertTrue(str(cm.exception).startswith(field + ":"), str(cm.exception))
        return str(cm.exception)

    def test_good_passes(self):
        jdpage.validate(good())

    def test_each_missing_top_field(self):
        for k in ("title", "problem", "flow", "phases", "risks", "proof", "cta", "brand"):
            with self.subTest(k=k):
                self.bad(lambda d, k=k: d.pop(k), k)

    def test_missing_nested_fields(self):
        self.bad(lambda d: d["phases"][0].pop("days"), "phases[0].days")
        self.bad(lambda d: d["phases"][1].pop("name"), "phases[1].name")
        self.bad(lambda d: d["risks"][0].pop("mitigation"), "risks[0].mitigation")
        self.bad(lambda d: d["proof"][0].pop("source"), "proof[0].source")
        self.bad(lambda d: d["brand"].pop("color"), "brand.color")

    def test_not_a_dict_and_wrong_types(self):
        with self.assertRaises(ValueError):
            jdpage.validate(None)
        with self.assertRaises(ValueError):
            jdpage.validate([])
        self.bad(lambda d: d.update(title=5), "title")
        self.bad(lambda d: d.update(title=""), "title")
        self.bad(lambda d: d.update(flow="a,b,c"), "flow")
        self.bad(lambda d: d["flow"].__setitem__(0, None), "flow[0]")

    def test_phase_count_exactly_three(self):
        self.bad(lambda d: d["phases"].pop(), "phases")
        self.bad(lambda d: d["phases"].append(copy.deepcopy(d["phases"][0])), "phases")

    def test_flow_bounds(self):
        self.bad(lambda d: d.update(flow=["a", "b"]), "flow")
        self.bad(lambda d: d.update(flow=list("abcdefg")), "flow")
        d = good()
        d["flow"] = list("abc")
        jdpage.validate(d)
        d["flow"] = list("abcdef")
        jdpage.validate(d)

    def test_risk_and_proof_bounds(self):
        self.bad(lambda d: d["risks"].pop(), "risks")
        self.bad(lambda d: d["risks"].extend(copy.deepcopy(d["risks"]) + copy.deepcopy(d["risks"][:1])), "risks")
        self.bad(lambda d: d.update(proof=[]), "proof")
        self.bad(lambda d: d["proof"].extend(copy.deepcopy(d["proof"]) * 3), "proof")

    def test_length_limits(self):
        self.bad(lambda d: d.update(title="x" * 91), "title")
        self.bad(lambda d: d.update(problem="x" * 281), "problem")
        d = good()
        d["title"], d["problem"] = "x" * 90, "y" * 280
        jdpage.validate(d)

    def test_color_must_be_hex(self):
        self.bad(lambda d: d["brand"].update(color="red"), "brand.color")
        self.bad(lambda d: d["brand"].update(color="#12345"), "brand.color")
        self.bad(lambda d: d["brand"].update(color="#fff;}</style>"), "brand.color")

    def test_links_rejected_in_every_string_field(self):
        bad_values = ["see https://example.com now", "go to www.example.org", "mail me a@b.co",
                      "ping @someone", "visit example.com", "ftp://x.y/z"]
        paths = [
            ("title", lambda d, v: d.update(title=v)),
            ("problem", lambda d, v: d.update(problem=v)),
            ("flow[1]", lambda d, v: d["flow"].__setitem__(1, v)),
            ("phases[2].name", lambda d, v: d["phases"][2].update(name=v)),
            ("phases[0].deliverable", lambda d, v: d["phases"][0].update(deliverable=v)),
            ("phases[1].days", lambda d, v: d["phases"][1].update(days=v)),
            ("risks[1].risk", lambda d, v: d["risks"][1].update(risk=v)),
            ("risks[0].mitigation", lambda d, v: d["risks"][0].update(mitigation=v)),
            ("proof[0].label", lambda d, v: d["proof"][0].update(label=v)),
            ("proof[0].number", lambda d, v: d["proof"][0].update(number=v)),
            ("proof[0].source", lambda d, v: d["proof"][0].update(source=v)),
            ("cta", lambda d, v: d.update(cta=v)),
            ("brand.name", lambda d, v: d["brand"].update(name=v)),
        ]
        for field, setter in paths:
            for v in bad_values:
                with self.subTest(field=field, v=v):
                    msg = self.bad(lambda d: setter(d, v), field)
                    self.assertIn("no links on the JD page", msg)

    def test_normal_text_is_not_a_link(self):
        d = good()
        d["cta"] = "Costs 3.5 hours, e.g. Node.js or v2.0 work. Start at 9 a.m. today."
        jdpage.validate(d)


class HtmlTest(unittest.TestCase):
    def test_script_in_title_is_escaped(self):
        d = good()
        d["title"] = "<script>alert(1)</script> & more"
        html = jdpage.build_html(d)
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("&amp; more", html)

    def test_every_dynamic_string_escaped(self):
        d = good()
        mark = "<b>x</b>"
        d["problem"] = mark
        d["flow"][0] = mark
        d["phases"][0]["name"] = mark
        d["risks"][0]["risk"] = mark
        d["proof"][0]["label"] = mark
        d["cta"] = mark
        d["brand"]["name"] = mark
        self.assertNotIn(mark, jdpage.build_html(d))

    def test_no_link_slots_in_template(self):
        html = jdpage.build_html(good())
        self.assertNotRegex(html, r"(?i)href=|mailto:|https?://|<a[ >]")

    def test_brand_colour_used(self):
        self.assertIn("#1F6F5C", jdpage.build_html(good()))

    def test_content_present(self):
        html = jdpage.build_html(good())
        for s in ("Map", "Build", "Hand over", good()["cta"], "Example Studio"):
            self.assertIn(s, html)


@unittest.skipUnless(_real_chrome(), "needs Chrome (set CHROME_BIN)")
class RenderTest(unittest.TestCase):
    def test_one_a4_page_with_title_phases_cta(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "jd.pdf"
            self.assertEqual(jdpage.render(good(), out), str(out))
            self.assertEqual(pdf_pages(out), 1)
            try:
                import pymupdf as fitz
            except ImportError:
                self.skipTest("needs pymupdf (use the gaspol-video venv python)")
            with fitz.open(out) as doc:
                r = doc[0].rect
                self.assertAlmostEqual(r.width, 595, delta=3)
                self.assertAlmostEqual(r.height, 842, delta=3)
            text = " ".join(pdf_text(out).split())
            d = good()
            for s in (d["title"], "Map", "Build", "Hand over", d["cta"]):
                self.assertIn(s, text)

    def test_maximum_content_still_one_page(self):
        d = good()
        d["title"], d["problem"] = "T" * 90, ("word " * 56).strip()
        d["flow"] = [("step " * 16).strip()] * 6
        d["phases"] = [{"name": "N" * 40, "deliverable": ("d " * 60).strip(), "days": 99}] * 3
        d["risks"] = [{"risk": ("r " * 60).strip(), "mitigation": ("m " * 80).strip()}] * 4
        d["proof"] = [{"label": "L" * 40, "number": "9" * 20, "source": "S" * 60}] * 3
        d["cta"] = ("c " * 80).strip()
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "max.pdf"
            jdpage.render(d, out)
            self.assertEqual(pdf_pages(out), 1)

    def test_invalid_data_writes_nothing(self):
        d = good()
        d["cta"] = "see https://example.com"
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "x.pdf"
            with self.assertRaises(ValueError):
                jdpage.render(d, out)
            self.assertFalse(out.exists())


class CliTest(unittest.TestCase):
    def run_cli(self, data, out):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "d.json"
            p.write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")
            o, e = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(o), contextlib.redirect_stderr(e):
                rc = cli.main(["jdpage", str(p), str(Path(td) / out)])
            return rc, o.getvalue(), e.getvalue(), Path(td) / out

    def test_link_exits_2_with_field(self):
        d = good()
        d["cta"] = "write to me at a@b.co"
        rc, _, err, out = self.run_cli(d, "o.pdf")
        self.assertEqual(rc, 2)
        self.assertIn("cta: no links on the JD page", err)
        self.assertFalse(out.exists())

    def test_missing_field_exits_2(self):
        d = good()
        del d["phases"]
        rc, _, err, _ = self.run_cli(d, "o.pdf")
        self.assertEqual(rc, 2)
        self.assertIn("phases:", err)

    def test_bad_json_exits_2(self):
        rc, _, err, _ = self.run_cli("{nope", "o.pdf")
        self.assertEqual(rc, 2)
        self.assertIn("json", err.lower())

    @unittest.skipUnless(_real_chrome(), "needs Chrome (set CHROME_BIN)")
    def test_good_exits_0_and_prints_path(self):
        rc, out, _, path = self.run_cli(good(), "o.pdf")
        self.assertEqual(rc, 0)
        self.assertIn("o.pdf", out)


if __name__ == "__main__":
    unittest.main()
