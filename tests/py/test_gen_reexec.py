import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.deckkit import __main__ as cli
from tools.deckkit import gen


def _project(root, client):
    """A project whose image client imports a module this interpreter lacks."""
    (client / ".venv" / "bin").mkdir(parents=True)
    py = client / ".venv" / "bin" / "python"
    py.write_text("#!/bin/sh\n")
    py.chmod(0o755)
    (client / "mcp_image_server.py").write_text("import module_only_the_client_has\n")
    (root / "prompts").mkdir()
    (root / "prompts" / "slide-01.md").write_text("p\n")
    (root / "prompts" / "manifest.json").write_text(json.dumps([{"n": 1, "sid": "a", "prompt_file": "prompts/slide-01.md", "refs": []}]))
    house = root / "house.md"
    house.write_text("```json\n" + json.dumps({"seller": "ContohAI", "preset": "isometrik-terang",
                                              "image_client": str(client), "image_model": "m"}) + "\n```\n")
    return root / "prompts" / "manifest.json", house, py


class ClientPythonTest(unittest.TestCase):
    def test_finds_client_venv_python(self):
        with tempfile.TemporaryDirectory() as d:
            _, _, py = _project(Path(d), Path(d) / "client")
            self.assertEqual(gen.client_python(Path(d) / "client"), str(py))

    def test_none_without_venv(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(gen.client_python(d))


class ReexecTest(unittest.TestCase):
    def tearDown(self):
        sys.modules.pop("mcp_image_server", None)

    def test_import_failure_reruns_with_client_python(self):
        with tempfile.TemporaryDirectory() as d:
            man, house, py = _project(Path(d), Path(d) / "client")
            argv = ["gen", str(man), "--house", str(house)]
            with mock.patch.dict(os.environ, {}, clear=False), \
                    mock.patch.object(os, "execve") as ex, \
                    contextlib.redirect_stderr(io.StringIO()):
                os.environ.pop(gen.ENV_REEXEC, None)
                cli.main(argv)
            ex.assert_called_once()
            exe, args, env = ex.call_args.args
            self.assertEqual(exe, str(py))
            self.assertEqual(args[:3], [str(py), "-m", "tools.deckkit"])
            self.assertEqual(args[3:], argv)   # already absolute, passed through unchanged
            self.assertEqual(env[gen.ENV_REEXEC], "1")
            root = str(Path(cli.__file__).resolve().parents[2])
            self.assertIn(root, env["PYTHONPATH"].split(os.pathsep))

    def test_relative_paths_made_absolute_and_no_chdir(self):
        with tempfile.TemporaryDirectory() as d:
            man, house, py = _project(Path(d), Path(d) / "client")
            old = os.getcwd()
            os.chdir(d)
            self.addCleanup(os.chdir, old)
            cwd = os.getcwd()
            argv = ["gen", "prompts/manifest.json", "--house", "house.md", "--out", "r", "--raw=m",
                    "--only", "1"]
            with mock.patch.dict(os.environ, {"PYTHONPATH": "/keep/me"}), \
                    mock.patch.object(os, "execve") as ex, mock.patch.object(os, "chdir") as cd, \
                    contextlib.redirect_stderr(io.StringIO()):
                os.environ.pop(gen.ENV_REEXEC, None)
                cli.main(argv)
            cd.assert_not_called()
            _, args, env = ex.call_args.args
            self.assertEqual(args[3:], ["gen", os.path.join(cwd, "prompts/manifest.json"),
                                        "--house", os.path.join(cwd, "house.md"),
                                        "--out", os.path.join(cwd, "r"),
                                        "--raw=" + os.path.join(cwd, "m"), "--only", "1"])
            parts = env["PYTHONPATH"].split(os.pathsep)
            self.assertEqual(parts[1:], ["/keep/me"])
            self.assertEqual(parts[0], str(Path(cli.__file__).resolve().parents[2]))

    def test_no_second_rerun(self):
        with tempfile.TemporaryDirectory() as d:
            man, house, _ = _project(Path(d), Path(d) / "client")
            err = io.StringIO()
            with mock.patch.dict(os.environ, {gen.ENV_REEXEC: "1"}), \
                    mock.patch.object(os, "execve") as ex, contextlib.redirect_stderr(err):
                rc = cli.main(["gen", str(man), "--house", str(house)])
            ex.assert_not_called()
            self.assertEqual(rc, 1)
            self.assertIn("cannot import mcp_image_server", err.getvalue())
