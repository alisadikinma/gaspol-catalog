"""Prompt manifest -> slide images through an external image generator (image MCP client)."""
import inspect
import json
import os
import re
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

from .prompts import prompt_sha

ENV_CLIENT = "DECKKIT_IMAGE_CLIENT"
NO_CLIENT = "no image client: set image_client in the house standard or DECKKIT_IMAGE_CLIENT"
NO_MODEL = "no model: pass --model or set image_model in the house standard"
_LOCAL = re.compile(r"(?:^|\s)local: (.+?)\s*$", re.M)


ENV_REEXEC = "DECKKIT_REEXEC"


def client_python(client_dir):
    """The image client's own interpreter (``<client>/.venv/bin/python``), or None.

    The client's dependencies (its MCP package) usually live only in its own venv, not in the
    venv that runs deckkit, so ``gen`` re-runs itself there when the import fails.
    """
    if not client_dir:
        return None
    py = os.path.join(str(client_dir), ".venv", "bin", "python")
    return py if os.path.isfile(py) and os.access(py, os.X_OK) else None


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


ASPECT = 16 / 9
ASPECT_TOL = 0.02


def _install(src, dest):
    """Verify ``src`` is a whole, 16:9 image and write it to ``dest`` as PNG (converting if needed).
    Raises ValueError/OSError for anything else, so the caller counts it as a failed attempt."""
    with Image.open(src) as im:
        im.verify()
    with Image.open(src) as im:
        im.load()
        w, h = im.size
        if not h or abs(w / h - ASPECT) > ASPECT * ASPECT_TOL:
            raise ValueError(f"{w}x{h} is not 16:9")
        part = dest.with_name(dest.name + ".part")
        try:
            if im.format == "PNG":
                shutil.copyfile(src, part)
            else:
                im.save(part, "PNG")
            os.replace(part, dest)
        finally:
            part.unlink(missing_ok=True)


STALE = ("stale: prompt changed since render — move the old render to prompts/_rejected/ "
         "(named for the defect) or use a new --ver")


def _sidecar(dest):
    return dest.with_name(dest.name + ".sha")


def _existing_status(dest, item, pf):
    """'exists' or STALE for a render already on disk. Compared with the manifest sha when it has
    one, else (only when a sidecar exists) with the prompt file on disk."""
    side = _sidecar(dest)
    rendered = side.read_text(encoding="utf-8").strip() if side.is_file() else None
    want = item.get("sha")
    if want is None and rendered is not None and pf.is_file():
        want = prompt_sha(pf.read_text(encoding="utf-8"))
    if want is None:
        return "exists"
    return "exists" if rendered == want else STALE


def _one(item, root, generator, out_dir, raw_dir, ver, tries, kw, with_style):
    n = item["n"]
    dest = out_dir / ver / f"{n:02d}.png" if ver else out_dir / f"slide-{n:02d}.png"
    pf = Path(item["prompt_file"])
    pf = pf if pf.is_absolute() else root / pf
    if dest.exists():
        return n, _existing_status(dest, item, pf)
    if not pf.is_file():
        return n, f"FAIL missing prompt {pf}"
    text = pf.read_text(encoding="utf-8")
    prompt = text
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
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                _install(m.group(1), dest)
                _sidecar(dest).write_text(prompt_sha(text) + "\n", encoding="utf-8")
            except Exception as exc:
                last = f"bad image: {type(exc).__name__}: {exc}"
                continue
            return n, "OK"
        last = r
    return n, f"FAIL {last[:200]}"


def run(manifest_path, generator, out_dir=None, raw_dir=None, ver=None, only=None,
        workers=4, tries=3, model=None, mode=None, resolution="2K"):
    """Render every manifest slide; returns [(n, 'OK' | 'exists' | 'FAIL ...')] in manifest order."""
    if not model:
        raise ValueError(NO_MODEL)
    manifest_path = Path(manifest_path).resolve()
    if ver is not None and (not str(ver).strip() or "/" in str(ver) or "\\" in str(ver) or str(ver) in (".", "..")):
        raise ValueError(f"ver {ver!r} must be a plain name, not a path")
    root = manifest_path.parent   # prompt_file entries resolve against the manifest's own directory
    project = root.parent
    out_dir = Path(out_dir) if out_dir else project / "renders"
    raw_dir = Path(raw_dir) if raw_dir else project / ".tmp" / "mentah"
    raw_dir.mkdir(parents=True, exist_ok=True)
    items = json.loads(manifest_path.read_text(encoding="utf-8"))
    if only:
        missing = [n for n in only if n not in {i["n"] for i in items}]
        if missing:
            raise ValueError(f"--only: no such slide n: {', '.join(str(n) for n in missing)}")
        items = [i for i in items if i["n"] in set(only)]
    kw = {"model": model, "mode": mode, "resolution": resolution}
    with_style = _accepts_style(generator)
    with ThreadPoolExecutor(max(1, workers)) as ex:
        return list(ex.map(lambda i: _one(i, root, generator, out_dir, raw_dir, ver, tries, kw, with_style), items))
