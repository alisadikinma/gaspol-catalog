import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.deckkit import __main__ as cli
from tools.deckkit import gen

PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d49444154789c6360000002000001e221bc330000000049454e44ae426082")


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        (self.root / "prompts").mkdir()
        self.src = self.root / "src.png"
        self.src.write_bytes(PNG)
        self.calls = []

    def manifest(self, ns=(1, 2), write=True):
        items = []
        for n in ns:
            items.append({"n": n, "sid": "", "prompt_file": f"prompts/slide-{n:02d}.md", "refs": ["r.png"] if n == 1 else []})
            if write:
                (self.root / "prompts" / f"slide-{n:02d}.md").write_text(f"PROMPT {n}\n", encoding="utf-8")
        p = self.root / "prompts" / "manifest.json"
        p.write_text(json.dumps(items), encoding="utf-8")
        return p

    def fake(self, **kw):
        def g(prompt, model, mode, aspect, resolution, output_format, output_dir, refs):
            self.calls.append(dict(prompt=prompt, model=model, mode=mode, aspect=aspect,
                                   resolution=resolution, output_format=output_format,
                                   output_dir=output_dir, refs=refs))
            return f"OK done local: {self.src}"
        return g


class RunTest(Base):
    def test_all_ok_defaults(self):
        res = gen.run(self.manifest(), self.fake(), model="m1", ver="r1")
        self.assertEqual(res, [(1, "OK"), (2, "OK")])
        self.assertTrue((self.root / "renders" / "01-r1.png").is_file())
        self.assertTrue((self.root / "renders" / "02-r1.png").is_file())
        c = next(x for x in self.calls if x["prompt"].startswith("PROMPT 1"))
        self.assertEqual((c["prompt"].strip(), c["model"], c["aspect"], c["resolution"], c["output_format"]),
                         ("PROMPT 1", "m1", "16:9", "2K", "png"))
        self.assertEqual(c["output_dir"], str(self.root / ".tmp" / "mentah"))
        self.assertEqual(c["refs"], ["r.png"])
        self.assertIsNone(next(x for x in self.calls if x["prompt"].startswith("PROMPT 2"))["refs"])

    def test_no_ver_names_slide(self):
        gen.run(self.manifest((3,)), self.fake(), model="m")
        self.assertTrue((self.root / "renders" / "slide-03.png").is_file())

    def test_custom_dirs(self):
        out, raw = self.root / "o", self.root / "w"
        gen.run(self.manifest((1,)), self.fake(), out_dir=out, raw_dir=raw, model="m")
        self.assertTrue((out / "slide-01.png").is_file())
        self.assertEqual(self.calls[0]["output_dir"], str(raw))

    def test_only(self):
        res = gen.run(self.manifest(), self.fake(), model="m", only=[2])
        self.assertEqual(res, [(2, "OK")])
        self.assertFalse((self.root / "renders" / "slide-01.png").exists())

    def test_existing_not_overwritten(self):
        (self.root / "renders").mkdir()
        keep = self.root / "renders" / "slide-01.png"
        keep.write_bytes(b"approved")
        res = gen.run(self.manifest(), self.fake(), model="m")
        self.assertEqual(res, [(1, "exists"), (2, "OK")])
        self.assertEqual(keep.read_bytes(), b"approved")
        self.assertEqual(len(self.calls), 1)

    def test_missing_prompt(self):
        m = self.manifest(write=False)
        res = gen.run(m, self.fake(), model="m")
        self.assertEqual(len(res), 2)
        self.assertTrue(res[0][1].startswith("FAIL missing prompt "))
        self.assertEqual(self.calls, [])

    def test_all_tries_fail_others_continue(self):
        def g(prompt, **kw):
            self.calls.append(prompt)
            if "PROMPT 1" in prompt:
                return "ERR quota"
            return f"OK local: {self.src}"
        res = gen.run(self.manifest(), g, model="m", tries=3, workers=1)
        self.assertEqual(res[0][0], 1)
        self.assertEqual(res[0][1], "FAIL ERR quota")
        self.assertEqual(res[1], (2, "OK"))
        self.assertEqual(sum("PROMPT 1" in c for c in self.calls), 3)

    def test_exception_then_success(self):
        state = {"n": 0}

        def g(**kw):
            state["n"] += 1
            if state["n"] < 3:
                raise RuntimeError("boom")
            return f"OK local: {self.src}"
        res = gen.run(self.manifest((1,)), g, model="m", tries=3)
        self.assertEqual(res, [(1, "OK")])
        self.assertEqual(state["n"], 3)

    def test_exception_exhausted_message(self):
        def g(**kw):
            raise RuntimeError("boom")
        res = gen.run(self.manifest((1,)), g, model="m", tries=2)
        self.assertIn("boom", res[0][1])
        self.assertTrue(res[0][1].startswith("FAIL"))

    def test_ok_without_local_is_failure(self):
        res = gen.run(self.manifest((1,)), lambda **kw: "OK but no path", model="m", tries=1)
        self.assertTrue(res[0][1].startswith("FAIL"))

    def test_error_truncated_200(self):
        res = gen.run(self.manifest((1,)), lambda **kw: "ERR " + "x" * 500, model="m", tries=1)
        self.assertEqual(len(res[0][1]), len("FAIL ") + 200)

    def test_style_only_when_accepted(self):
        seen = {}

        def g(prompt, style, **kw):
            seen.update(style=style)
            return f"OK local: {self.src}"
        gen.run(self.manifest((1,)), g, model="m")
        self.assertEqual(seen["style"], "None")

    def test_kwargs_generator_gets_no_style(self):
        got = {}

        def g(**kw):
            got.update(kw)
            return f"OK local: {self.src}"
        gen.run(self.manifest((1,)), g, model="m")
        self.assertNotIn("style", got)

    def test_no_model_raises(self):
        with self.assertRaises(ValueError) as cm:
            gen.run(self.manifest(), self.fake())
        self.assertIn("no model: pass --model or set image_model in the house standard", str(cm.exception))

    def test_mode_passed(self):
        gen.run(self.manifest((2,)), self.fake(), model="m", mode="fast", resolution="4K")
        self.assertEqual((self.calls[0]["mode"], self.calls[0]["resolution"]), ("fast", "4K"))

    def test_workers_keep_manifest_order(self):
        res = gen.run(self.manifest((1, 2, 3, 4)), self.fake(), model="m", workers=4)
        self.assertEqual([n for n, _ in res], [1, 2, 3, 4])


class LoadGeneratorTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self._path = list(sys.path)
        sys.modules.pop("mcp_image_server", None)
        self.addCleanup(self.restore)

    def restore(self):
        sys.modules.pop("mcp_image_server", None)
        sys.path[:] = self._path

    def write(self, body):
        (Path(self.tmp.name) / "mcp_image_server.py").write_text(body, encoding="utf-8")

    def test_plain_function(self):
        self.write("def generate_image(**kw):\n    return 'OK plain'\n")
        g = gen.load_generator(self.tmp.name)
        self.assertEqual(g(), "OK plain")

    def test_unwraps_fn(self):
        self.write("class W:\n    def fn(self, **kw):\n        return 'OK unwrapped'\n"
                   "    def __call__(self, **kw):\n        return 'wrapped'\n"
                   "generate_image = W()\n")
        self.assertEqual(gen.load_generator(self.tmp.name)(), "OK unwrapped")

    def test_none_dir(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(RuntimeError) as cm:
                gen.load_generator(None)
        self.assertIn("no image client: set image_client in the house standard or DECKKIT_IMAGE_CLIENT", str(cm.exception))

    def test_import_failure_names_dir(self):
        with self.assertRaises(RuntimeError) as cm:
            gen.load_generator(self.tmp.name)
        self.assertIn(self.tmp.name, str(cm.exception))


class CliTest(Base):
    def run_cli(self, argv, generator=None):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(gen, "load_generator", return_value=generator or self.fake()):
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                rc = cli.main(argv)
        return rc, out.getvalue(), err.getvalue()

    def house(self, **kw):
        h = {"seller": "S", "preset": "p", "image_client": "/x", "image_model": "hm"}
        h.update(kw)
        p = self.root / "house.md"
        p.write_text("```json\n" + json.dumps(h) + "\n```\n", encoding="utf-8")
        return p

    def test_ok_lines_and_house_model(self):
        m = self.manifest()
        rc, out, _ = self.run_cli(["gen", str(m), "--house", str(self.house()), "--ver", "r1"])
        self.assertEqual(rc, 0)
        self.assertEqual(out.split("\n")[:2], ["01 OK", "02 OK"])
        self.assertEqual(self.calls[0]["model"], "hm")

    def test_model_flag_wins(self):
        m = self.manifest((1,))
        self.run_cli(["gen", str(m), "--house", str(self.house()), "--model", "cli"])
        self.assertEqual(self.calls[0]["model"], "cli")

    def test_exists_and_fail_exit_1(self):
        m = self.manifest(write=False)
        (self.root / "prompts" / "slide-01.md").write_text("P", encoding="utf-8")
        (self.root / "renders").mkdir()
        (self.root / "renders" / "slide-01.png").write_bytes(b"x")
        rc, out, _ = self.run_cli(["gen", str(m), "--house", str(self.house())])
        self.assertEqual(rc, 1)
        lines = out.strip().split("\n")
        self.assertEqual(lines[0], "01 exists")
        self.assertTrue(lines[1].startswith("02 FAIL missing prompt"))

    def test_no_model_error_exit_1(self):
        m = self.manifest()
        rc, _, err = self.run_cli(["gen", str(m), "--house", str(self.house(image_model=None))])
        self.assertEqual(rc, 1)
        self.assertIn("no model", err)

    def test_only_flag(self):
        m = self.manifest()
        rc, out, _ = self.run_cli(["gen", str(m), "--house", str(self.house()), "--only", "2"])
        self.assertEqual(out.strip(), "02 OK")


if __name__ == "__main__":
    unittest.main()
