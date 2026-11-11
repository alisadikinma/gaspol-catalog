"""deckkit vidkit: run gaspol-video's photo tools from deckkit without copying them."""
import os
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from tools.deckkit import vidbridge


def _fake_video(root):
    (root / "tools" / "vidkit").mkdir(parents=True)
    (root / "tools" / "vidkit" / "__main__.py").write_text("")
    return root


class FindRoot(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.t = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_env_wins(self):
        vid = _fake_video(self.t / "anywhere")
        here = self.t / "x" / "gaspol-catalog" / "tools" / "deckkit" / "vidbridge.py"
        self.assertEqual(vidbridge.find_root({vidbridge.ENV_ROOT: str(vid)}, here), vid.resolve())

    def test_env_without_vidkit_refuses(self):
        (self.t / "empty").mkdir()
        with self.assertRaisesRegex(FileNotFoundError, vidbridge.ENV_ROOT):
            vidbridge.find_root({vidbridge.ENV_ROOT: str(self.t / "empty")}, self.t / "a" / "b" / "c" / "d.py")

    def test_dev_layout_sibling(self):
        vid = _fake_video(self.t / "gaspol-video")
        here = self.t / "gaspol-catalog" / "tools" / "deckkit" / "vidbridge.py"
        self.assertEqual(vidbridge.find_root({}, here), vid.resolve())

    def test_cache_layout_highest_version(self):
        for v in ("3.9.0", "3.44.0", "3.39.0"):
            _fake_video(self.t / "gaspol-video" / v)
        (self.t / "gaspol-video" / "notes").mkdir()
        here = self.t / "gaspol-catalog" / "0.9.1" / "tools" / "deckkit" / "vidbridge.py"
        self.assertEqual(vidbridge.find_root({}, here), (self.t / "gaspol-video" / "3.44.0").resolve())

    def test_not_found_names_the_fix(self):
        here = self.t / "gaspol-catalog" / "tools" / "deckkit" / "vidbridge.py"
        with self.assertRaisesRegex(FileNotFoundError, vidbridge.ENV_ROOT):
            vidbridge.find_root({}, here)


class Command(unittest.TestCase):
    def test_unknown_tool_refused(self):
        with self.assertRaisesRegex(ValueError, "grain"):
            vidbridge.command(Path("/v"), "grain", [])

    def test_argv_shape(self):
        argv = vidbridge.command(Path("/v"), "retint", ["a.png", "b.png"], python="py")
        self.assertEqual(argv[0], "py")
        self.assertEqual(argv[-4:], ["/v", "retint", "a.png", "b.png"])


@unittest.skipUnless(vidbridge.find_root_or_none(), "gaspol-video not found")
class RealVidkit(unittest.TestCase):
    """Runs the real vidkit retint, from a cwd where `tools` is deckkit's own package."""

    def test_retint_runs_through_cli(self):
        from tools.deckkit.__main__ import main
        with tempfile.TemporaryDirectory() as d:
            src, out = Path(d) / "in.png", Path(d) / "out.png"
            Image.new("RGB", (40, 30), (40, 90, 230)).save(src)
            rc = main(["vidkit", "retint", str(src), str(out), "--to", "#071A33"])
            self.assertEqual(rc, 0)
            with Image.open(out) as im:
                r, g, b = im.convert("RGB").getpixel((5, 5))
            self.assertLess(b, 150)  # royal blue moved toward navy

    def test_vidkit_error_exit_code_passes_through(self):
        from tools.deckkit.__main__ import main
        with tempfile.TemporaryDirectory() as d:
            rc = main(["vidkit", "retint", str(Path(d) / "missing.png"), str(Path(d) / "o.png"), "--to", "#071A33"])
            self.assertNotEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
