"""Headless Chrome: HTML page -> PNG at an exact size, or -> PDF."""
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

NAMES = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"]
MAC_APP = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
NOT_FOUND = "Chrome not found: set CHROME_BIN"


def find_chrome(env=None):
    """Chrome binary path: $CHROME_BIN, else a known name on PATH, else the macOS app bundle."""
    env = os.environ if env is None else env
    given = env.get("CHROME_BIN")
    if given:
        # an explicit choice that is wrong is an error, never a silent switch to another browser
        if not os.path.isfile(given):
            raise RuntimeError(f"CHROME_BIN is set but not a file: {given}")
        return given
    for name in NAMES:
        found = shutil.which(name, path=env.get("PATH", ""))
        if found:
            return found
    if os.path.isfile(MAC_APP):
        return MAC_APP
    raise RuntimeError(NOT_FOUND)


def _run(args, timeout):
    with tempfile.TemporaryDirectory() as profile:
        cmd = [find_chrome(), "--user-data-dir=" + profile, "--no-first-run",
               "--disable-gpu", *args]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Chrome timed out after {timeout}s") from None
    if res.returncode != 0:
        tail = "\n".join((res.stderr or "").strip().splitlines()[-10:])
        raise RuntimeError(f"Chrome exited {res.returncode}: {tail}")


def _url(html_path):
    return Path(html_path).resolve().as_uri()


def shot(html_path, out_png, size=(2752, 1536), timeout=120):
    """Screenshot ``html_path`` at exactly ``size`` pixels. Larger output is cropped, smaller raises."""
    w, h = size
    out = Path(out_png)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    _run(["--headless=new", "--hide-scrollbars", "--force-device-scale-factor=1",
          f"--window-size={w},{h}", f"--screenshot={out}", _url(html_path)], timeout)
    if not out.is_file():
        raise RuntimeError(f"Chrome wrote no screenshot to {out}")
    with Image.open(out) as im:
        im.load()
        got = im.size
        if got == (w, h):
            return str(out)
        if got[0] < w or got[1] < h:
            raise RuntimeError(f"screenshot is smaller than requested: {got[0]}x{got[1]} < {w}x{h}")
        im.crop((0, 0, w, h)).save(out)
    return str(out)


def print_pdf(html_path, out_pdf, timeout=120):
    """Print ``html_path`` to a PDF, no header or footer."""
    out = Path(out_pdf)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    _run(["--headless=new", "--no-pdf-header-footer", f"--print-to-pdf={out}", _url(html_path)], timeout)
    if not out.is_file():
        raise RuntimeError(f"Chrome wrote no PDF to {out}")
    return str(out)
