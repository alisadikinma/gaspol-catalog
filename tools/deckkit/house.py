"""Load the house standard (seller identity, outside the plugin) and style presets (inside it)."""
import json
import os
import re
from pathlib import Path

ENV_VAR = "GASPOL_CATALOG_HOUSE"
STYLES_DIR = Path(__file__).resolve().parents[2] / "references" / "b2b" / "styles"
REQUIRED = ("seller", "preset")
DEFAULT_LANGUAGE = "Indonesian"

_BLOCK = re.compile(r"^```json[ \t]*\n(.*?)^```[ \t]*$", re.S | re.M)
_KEY_LINE = re.compile(r"^\s*house-standard:\s*(.+?)\s*$", re.M)


def load_json_block(path):
    """Dict from the first fenced json block of a markdown file."""
    path = Path(path)
    m = _BLOCK.search(path.read_text(encoding="utf-8"))
    if not m:
        raise ValueError(f"no json block in {path}")
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        raise ValueError(f"bad json in {path}: {e}")
    if not isinstance(data, dict):
        raise ValueError(f"bad json in {path}: top level must be an object")
    return data


def _expand(raw, env):
    raw = str(raw)
    if raw == "~" or raw.startswith("~/"):
        home = env.get("HOME") or str(Path.home())
        raw = home + raw[1:]
    return Path(raw)


def _must_exist(path, label):
    if not path.is_file():
        raise FileNotFoundError(f"house standard from {label} not found: {path}")
    return path


def resolve(explicit=None, start=None, env=None):
    """Find the house standard file: explicit, then $GASPOL_CATALOG_HOUSE, then
    ``house-standard:`` in the nearest ancestor's .gaspol/context-sources.md. None when absent."""
    env = os.environ if env is None else env
    if explicit:
        return _must_exist(_expand(explicit, env), "--house")
    if env.get(ENV_VAR):
        return _must_exist(_expand(env[ENV_VAR], env), f"${ENV_VAR}")
    here = Path(start if start is not None else Path.cwd()).resolve()
    for d in (here, *here.parents):
        src = d / ".gaspol" / "context-sources.md"
        if src.is_file():
            m = _KEY_LINE.search(src.read_text(encoding="utf-8"))
            if m:
                return _must_exist(_expand(m.group(1), env), str(src))
    return None


def load(path):
    """House standard dict; ``seller`` and ``preset`` required, ``language`` defaults."""
    data = load_json_block(path)
    for key in REQUIRED:
        if key not in data:
            raise ValueError(f"house standard {path} missing key: {key}")
    data.setdefault("language", DEFAULT_LANGUAGE)
    return data


def load_preset(name, styles_dir=None):
    """Preset dict from references/b2b/styles/<name>.md; unknown name lists what exists."""
    if not re.fullmatch(r"[A-Za-z0-9._-]+", str(name)) or ".." in str(name):
        raise ValueError(f"bad preset name: {name!r}")
    d = Path(styles_dir) if styles_dir is not None else STYLES_DIR
    f = d / f"{name}.md"
    if not f.is_file():
        avail = sorted(p.stem for p in d.glob("*.md")) if d.is_dir() else []
        raise FileNotFoundError(f"preset {name!r} not found in {d}; available: {', '.join(avail) or 'none'}")
    return load_json_block(f)
