"""deckkit refgate: a slide that names a registered real place or object must carry its photo ref.

Real case: Marathon-RFID-System slide 3, 2026-10-21. The prompt named HarbourBay Batam, no photo of it
went in, and the render showed a Jakarta-style skyline. Ali: "harusnya Harbourbay Batam bukan gedung
tinggi kayak jakarta".
"""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from tools.deckkit import __main__ as cli
from tools.deckkit import refgate

REG = {"entities": [
    {"names": ["HarbourBay", "Harbour Bay"], "ref": ["harbourbay"]},
    {"names": ["AOI machine"], "ref": ["aoi-ref"]},
]}


class Deck:
    """deck/ref/real-refs.json + deck/prompts/{manifest.json, slide-NN.md}."""

    def __init__(self, tmp, registry=REG):
        self.root = Path(tmp) / "deck"
        (self.root / "prompts").mkdir(parents=True)
        (self.root / "ref").mkdir()
        if registry is not None:
            (self.root / "ref" / "real-refs.json").write_text(json.dumps(registry))
        self.items = []

    def slide(self, n, text, refs):
        (self.root / "prompts" / f"slide-{n:02d}.md").write_text(text)
        self.items.append({"n": n, "prompt_file": f"slide-{n:02d}.md", "refs": refs})
        (self.root / "prompts" / "manifest.json").write_text(json.dumps(self.items))
        return self

    @property
    def manifest(self):
        return self.root / "prompts" / "manifest.json"


class CheckTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_named_place_without_its_photo_is_a_finding(self):
        d = Deck(self.tmp.name).slide(3, "VISUAL: a race route along the HarbourBay Batam waterfront.",
                                      ["/x/indusia-wordmark.jpg", "/x/style.jpg"])
        got = refgate.check(d.manifest)
        self.assertEqual([(f["n"], f["entity"]) for f in got], [(3, "HarbourBay")])

    def test_photo_present_passes(self):
        d = Deck(self.tmp.name).slide(3, "the HarbourBay Batam waterfront",
                                      ["/x/style.jpg", "/deck/ref/harbourbay-batam.png"])
        self.assertEqual(refgate.check(d.manifest), [])

    def test_match_is_case_insensitive_and_whole_word(self):
        d = Deck(self.tmp.name).slide(1, "harbour bay at dusk", []).slide(2, "an AOI machines-row", [])
        got = refgate.check(d.manifest)
        self.assertEqual([(f["n"], f["entity"]) for f in got], [(1, "Harbour Bay")])  # the name as written

    def test_name_inside_quoted_on_screen_text_is_not_a_depiction(self):
        # Real false alarms (2026-10-25): PCI slide 2 headline "Golden-image SPI and AOI machines mark
        # good boards as NG." and Marathon slide 10 card title "AI VISUAL INSPECTION · PCI, BATAM".
        d = Deck(self.tmp.name).slide(2, 'headline: "Golden-image AOI machine marks good boards as NG."', []) \
            .slide(10, 'card 1 title: “AI VISUAL INSPECTION · PCI, HARBOURBAY”', []) \
            .slide(3, 'VISUAL: the HarbourBay waterfront. headline: "Race day"', [])
        self.assertEqual([(f["n"], f["entity"]) for f in refgate.check(d.manifest)], [(3, "HarbourBay")])

    def test_registry_found_in_parent_folders_and_merged(self):
        d = Deck(self.tmp.name, registry={"entities": [{"names": ["HarbourBay"], "ref": ["harbourbay"]}]})
        (Path(self.tmp.name) / "ref").mkdir()
        (Path(self.tmp.name) / "ref" / "real-refs.json").write_text(
            json.dumps({"entities": [{"names": ["SPI machine"], "ref": ["spi-ref"]}]}))
        d.slide(1, "an SPI machine beside HarbourBay", [])
        self.assertEqual(sorted(f["entity"] for f in refgate.check(d.manifest)), ["HarbourBay", "SPI machine"])

    def test_no_registry_means_no_findings(self):
        d = Deck(self.tmp.name, registry=None).slide(1, "HarbourBay", [])
        self.assertEqual(refgate.check(d.manifest), [])

    def test_bad_registry_is_refused(self):
        d = Deck(self.tmp.name, registry={"entities": [{"names": "HarbourBay"}]}).slide(1, "x", [])
        with self.assertRaises(refgate.Refused):
            refgate.check(d.manifest)


class CliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def run_cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = cli.main(list(args))
        return rc, out.getvalue(), err.getvalue()

    def test_finding_exits_1_and_names_slide_entity_and_needed_ref(self):
        d = Deck(self.tmp.name).slide(3, "HarbourBay waterfront", [])
        rc, out, _ = self.run_cli("refgate", str(d.manifest))
        self.assertEqual(rc, 1)
        for text in ("03", "HarbourBay", "harbourbay"):
            self.assertIn(text, out)

    def test_clean_exits_0(self):
        d = Deck(self.tmp.name).slide(3, "HarbourBay", ["/r/harbourbay.png"])
        self.assertEqual(self.run_cli("refgate", str(d.manifest))[0], 0)

    def test_gen_refuses_before_rendering(self):
        d = Deck(self.tmp.name).slide(3, "HarbourBay waterfront", [])
        rc, _, err = self.run_cli("gen", str(d.manifest), "--model", "x")
        self.assertEqual(rc, 1)
        self.assertIn("refgate", err)
        self.assertFalse((d.root / "renders").exists())


if __name__ == "__main__":
    unittest.main()
