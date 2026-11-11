"""Run a gaspol-video ``vidkit`` photo tool from deckkit, without copying it.

The photo tools (paste, erase, retint, inpaint) live in gaspol-video with their own tests. A copy
here would drift from the original, so deckkit runs the original in a child process instead.

Both plugins name their package ``tools``, so ``python -m tools.vidkit`` from the catalog root
would import deckkit's ``tools``. The child puts the gaspol-video root first on ``sys.path``
before anything is imported, which keeps file paths relative to the caller's cwd.
"""
import os
import re
import subprocess
import sys
from pathlib import Path

ENV_ROOT = "GASPOL_VIDEO_ROOT"
COMMANDS = ("paste", "erase", "retint", "inpaint")

_CHILD = ("import runpy, sys; sys.path.insert(0, sys.argv.pop(1)); "
          "runpy.run_module('tools.vidkit', run_name='__main__', alter_sys=True)")


def _has_vidkit(p):
    return (p / "tools" / "vidkit" / "__main__.py").is_file()


def _version_key(name):
    return tuple(int(x) for x in name.split("."))


def find_root(env=os.environ, here=Path(__file__)):
    """gaspol-video root: ``$GASPOL_VIDEO_ROOT``, else the sibling checkout (dev layout
    ``<dir>/gaspol-video``), else the highest installed version (plugin cache layout
    ``<marketplace>/gaspol-video/<version>``). FileNotFoundError names the env var to set."""
    if env.get(ENV_ROOT):
        p = Path(os.path.expanduser(env[ENV_ROOT])).resolve()
        if not _has_vidkit(p):
            raise FileNotFoundError(f"{ENV_ROOT}={p} has no tools/vidkit/__main__.py")
        return p
    plugin = Path(here).resolve().parents[2]  # .../gaspol-catalog[/<version>]
    sibling = plugin.parent / "gaspol-video"
    if _has_vidkit(sibling):
        return sibling
    cached = plugin.parent.parent / "gaspol-video"
    if cached.is_dir():
        versions = [d for d in cached.iterdir() if re.fullmatch(r"\d+(\.\d+)*", d.name) and _has_vidkit(d)]
        if versions:
            return max(versions, key=lambda d: _version_key(d.name))
    raise FileNotFoundError(f"gaspol-video not found next to {plugin}: install it, or set {ENV_ROOT} "
                            "to its plugin root")


def find_root_or_none():
    try:
        return find_root()
    except FileNotFoundError:
        return None


def command(root, tool, args, python=None):
    """argv that runs ``vidkit <tool> <args>`` from ``root``. Only the photo tools are allowed."""
    if tool not in COMMANDS:
        raise ValueError(f"vidkit {tool!r} is not a deckkit photo tool; allowed: {', '.join(COMMANDS)}")
    return [python or sys.executable, "-c", _CHILD, str(root), tool, *args]


def run(tool, args, env=os.environ):
    """Run the tool; returns its exit code (vidkit prints its own errors)."""
    argv = command(find_root(env), tool, args)
    return subprocess.call(argv)
