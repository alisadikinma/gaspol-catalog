"""Prompt manifest -> slide images through an external image generator (image MCP client)."""
import inspect
import json
import os
import re
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ENV_CLIENT = "DECKKIT_IMAGE_CLIENT"
NO_CLIENT = "no image client: set image_client in the house standard or DECKKIT_IMAGE_CLIENT"
NO_MODEL = "no model: pass --model or set image_model in the house standard"
_LOCAL = re.compile(r"local: (\S+)")


def load_generator(client_dir=None):
    """The image client's ``generate_image`` callable (FastMCP wrapper unwrapped)."""
    client_dir = client_dir or os.environ.get(ENV_CLIENT)
    if not client_dir:
        raise RuntimeError(NO_CLIENT)
    sys.path.insert(0, str(client_dir))
    try:
        import mcp_image_server as m
    except ImportError as exc:
        raise RuntimeError(f"cannot import mcp_image_server from {client_dir}: {exc}")
    return getattr(m.generate_image, "fn", m.generate_image)


def _accepts_style(generator):
    try:
        return "style" in inspect.signature(generator).parameters
    except (TypeError, ValueError):
        return False


def _one(item, root, generator, out_dir, raw_dir, ver, tries, kw, with_style):
    n = item["n"]
    name = f"{n:02d}-{ver}.png" if ver else f"slide-{n:02d}.png"
    dest = out_dir / name
    if dest.exists():
        return n, "exists"
    pf = Path(item["prompt_file"])
    pf = pf if pf.is_absolute() else root / pf
    if not pf.is_file():
        return n, f"FAIL missing prompt {pf}"
    prompt = pf.read_text(encoding="utf-8")
    extra = {"style": "None"} if with_style else {}
    last = "no attempt"
    for _ in range(max(1, tries)):
        try:
            r = str(generator(prompt=prompt, aspect="16:9", output_format="png",
                              output_dir=str(raw_dir), refs=item.get("refs") or None, **kw, **extra))
        except Exception as exc:
            last = f"{type(exc).__name__}: {exc}"
            continue
        m = _LOCAL.search(r)
        if r.startswith("OK") and m and Path(m.group(1)).is_file():
            out_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy(m.group(1), dest)
            return n, "OK"
        last = r
    return n, f"FAIL {last[:200]}"


def run(manifest_path, generator, out_dir=None, raw_dir=None, ver=None, only=None,
        workers=4, tries=3, model=None, mode=None, resolution="2K"):
    """Render every manifest slide; returns [(n, 'OK' | 'exists' | 'FAIL ...')] in manifest order."""
    if not model:
        raise ValueError(NO_MODEL)
    manifest_path = Path(manifest_path).resolve()
    root = manifest_path.parent.parent
    out_dir = Path(out_dir) if out_dir else root / "renders"
    raw_dir = Path(raw_dir) if raw_dir else root / ".tmp" / "mentah"
    raw_dir.mkdir(parents=True, exist_ok=True)
    items = json.loads(manifest_path.read_text(encoding="utf-8"))
    if only:
        items = [i for i in items if i["n"] in set(only)]
    kw = {"model": model, "mode": mode, "resolution": resolution}
    with_style = _accepts_style(generator)
    with ThreadPoolExecutor(max(1, workers)) as ex:
        return list(ex.map(lambda i: _one(i, root, generator, out_dir, raw_dir, ver, tries, kw, with_style), items))
