import tempfile
import unittest
from pathlib import Path

from tools.deckkit import house

FENCE = "`" * 3


def md(body, extra=""):
    return f"# Title\n\nprose\n\n{FENCE}json\n{body}\n{FENCE}\n\n{extra}"


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        self.addCleanup(self._tmp.cleanup)

    def write(self, rel, text):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p


class LoadJsonBlockTest(Base):
    def test_first_block_wins(self):
        p = self.write("a.md", md('{"a": 1}', extra=f"{FENCE}json\n{{\"a\": 2}}\n{FENCE}\n"))
        self.assertEqual(house.load_json_block(p), {"a": 1})

    def test_missing_block_raises(self):
        p = self.write("a.md", "no block here")
        with self.assertRaisesRegex(ValueError, "no json block in"):
            house.load_json_block(p)

    def test_bad_json_raises(self):
        p = self.write("a.md", md("{nope"))
        with self.assertRaisesRegex(ValueError, "bad json in"):
            house.load_json_block(p)

    def test_non_object_raises(self):
        p = self.write("a.md", md("[1, 2]"))
        with self.assertRaisesRegex(ValueError, "bad json in"):
            house.load_json_block(p)


class ResolveTest(Base):
    def setUp(self):
        super().setUp()
        self.explicit = self.write("explicit.md", md('{"seller": "E", "preset": "p"}'))
        self.envfile = self.write("env.md", md('{"seller": "V", "preset": "p"}'))
        self.filehouse = self.write("fh.md", md('{"seller": "F", "preset": "p"}'))
        self.write("proj/.gaspol/context-sources.md", f"- x: y\nhouse-standard: {self.filehouse}\n")
        (self.root / "proj" / "a" / "b").mkdir(parents=True)

    def test_explicit_beats_env_and_file(self):
        got = house.resolve(self.explicit, self.root / "proj",
                            env={"GASPOL_CATALOG_HOUSE": str(self.envfile)})
        self.assertEqual(got, self.explicit)

    def test_env_beats_file(self):
        got = house.resolve(None, self.root / "proj",
                            env={"GASPOL_CATALOG_HOUSE": str(self.envfile)})
        self.assertEqual(got, self.envfile)

    def test_context_sources_in_grandparent(self):
        got = house.resolve(None, self.root / "proj" / "a" / "b", env={})
        self.assertEqual(got, self.filehouse)

    def test_tilde_expands_from_env_home(self):
        self.write("home/h.md", md('{"seller": "H", "preset": "p"}'))
        self.write("p2/.gaspol/context-sources.md", "house-standard: ~/h.md\n")
        got = house.resolve(None, self.root / "p2", env={"HOME": str(self.root / "home")})
        self.assertEqual(got, self.root / "home" / "h.md")

    def test_context_sources_without_key_falls_through_to_none(self):
        self.write("p3/.gaspol/context-sources.md", "- other: thing\n")
        self.assertIsNone(house.resolve(None, self.root / "p3", env={}))

    def test_nothing_returns_none(self):
        self.assertIsNone(house.resolve(None, self.root / "empty-start", env={}))

    def test_named_path_missing_raises(self):
        with self.assertRaises(FileNotFoundError):
            house.resolve(self.root / "ghost.md", self.root, env={})
        with self.assertRaises(FileNotFoundError):
            house.resolve(None, self.root, env={"GASPOL_CATALOG_HOUSE": str(self.root / "ghost.md")})

    def test_context_sources_path_missing_raises(self):
        self.write("p4/.gaspol/context-sources.md", f"house-standard: {self.root}/ghost.md\n")
        with self.assertRaises(FileNotFoundError):
            house.resolve(None, self.root / "p4", env={})


class LoadTest(Base):
    def test_valid(self):
        p = self.write("h.md", md('{"seller": "S", "preset": "p", "site": "x.test"}'))
        self.assertEqual(house.load(p)["site"], "x.test")

    def test_language_default_filled(self):
        p = self.write("h.md", md('{"seller": "S", "preset": "p"}'))
        self.assertEqual(house.load(p)["language"], "Indonesian")

    def test_empty_object_missing_seller(self):
        p = self.write("h.md", md("{}"))
        with self.assertRaisesRegex(ValueError, "missing key: seller"):
            house.load(p)

    def test_missing_preset(self):
        p = self.write("h.md", md('{"seller": "S"}'))
        with self.assertRaisesRegex(ValueError, "missing key: preset"):
            house.load(p)


class LoadPresetTest(Base):
    def test_loads_from_styles_dir(self):
        self.write("styles/alpha.md", md('{"name": "alpha"}'))
        self.assertEqual(house.load_preset("alpha", styles_dir=self.root / "styles"), {"name": "alpha"})

    def test_unknown_lists_available(self):
        self.write("styles/alpha.md", md("{}"))
        self.write("styles/beta.md", md("{}"))
        with self.assertRaises(FileNotFoundError) as cm:
            house.load_preset("zzz", styles_dir=self.root / "styles")
        self.assertIn("alpha", str(cm.exception))
        self.assertIn("beta", str(cm.exception))

    def test_missing_styles_dir_lists_none(self):
        with self.assertRaises(FileNotFoundError) as cm:
            house.load_preset("zzz", styles_dir=self.root / "nope")
        self.assertIn("none", str(cm.exception))

    def test_default_dir_unknown_name_raises(self):
        with self.assertRaises(FileNotFoundError):
            house.load_preset("definitely-not-a-preset")

    def test_rejects_path_separators(self):
        with self.assertRaises(ValueError):
            house.load_preset("../x")


if __name__ == "__main__":
    unittest.main()
