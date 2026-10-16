"""Erase a small piece of baked-in footer text (a page number, a stale brand tag).

Locates the text with tesseract OCR, builds a mask from the ink around it, and inpaints with
OpenCV. Needs ``tesseract`` on PATH, ``cv2`` and ``numpy``. Use when the number/brand belongs
in a post-step (see :mod:`stamp`) but the model printed it into the render.
"""
import csv
import io
import subprocess
import tempfile

import numpy as np


def _cv2():
    try:
        import cv2
        return cv2
    except ImportError as exc:
        raise RuntimeError("erase needs opencv (cv2)") from exc


def _groups(cols, gap):
    out, s, last = [], None, None
    for x in cols:
        if s is None:
            s = last = x
        elif x - last > gap:
            out.append((s, last))
            s = last = x
        else:
            last = x
    if s is not None:
        out.append((s, last))
    return out


def find_word(bgr, needle, region_top=0.86):
    """OCR the bottom of the page; return the last word containing ``needle`` as
    ``(left, top, width, height)`` in full-page pixels, or None."""
    cv2 = _cv2()
    h = bgr.shape[0]
    y0 = int(h * region_top)
    with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
        cv2.imwrite(tmp.name, bgr[y0:])
        for psm in ("6", "11"):
            out = subprocess.run(["tesseract", tmp.name, "-", "--psm", psm, "tsv"], capture_output=True, text=True).stdout
            rows = [r for r in csv.DictReader(io.StringIO(out), delimiter="\t", quoting=csv.QUOTE_NONE)
                    if (r.get("text") or "").strip()]
            hit = [r for r in rows if needle.upper() in r["text"].upper()]
            if hit:
                r = hit[-1]
                return int(r["left"]), y0 + int(r["top"]), int(r["width"]), int(r["height"])
    return None


def erase_footer(path, needle, region_top=0.86, ink_delta=35, out=None):
    """Remove the footer run that starts at the word containing ``needle`` and extends right over
    the following ink (dot separators, trailing page number), stopping at the first wide gap.
    Rewrites ``path`` (or ``out``). Returns the erased x-range, or None when not found."""
    cv2 = _cv2()
    a = cv2.imread(str(path))
    if a is None:
        raise FileNotFoundError(path)
    h, w = a.shape[:2]
    hit = find_word(a, needle, region_top)
    if hit is None:
        return None
    L, T, W, H = hit
    ya, yb = T - int(H * 0.35), T + int(H * 1.35)
    g = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY).astype(int)[ya:yb]
    bg = np.median(g[:, max(0, L - 8 * H):L - 2 * H])
    ink = np.abs(g - bg) > ink_delta
    start = L - 3
    lc = np.where(ink[:, max(0, L - 2 * H):L - 2].any(0))[0] + max(0, L - 2 * H)
    if len(lc):
        g0 = _groups(lc, 3)[-1]
        if g0[1] - g0[0] < H * 0.6:      # a narrow mark just left of the word = the separator dot
            start = g0[0] - 3
    rc = np.where(ink[:, L:min(w, L + W + 5 * H)].any(0))[0] + L
    end = L + W
    for s_, e_ in _groups(rc, int(H * 1.2)):
        if s_ <= end + int(H * 1.2):
            end = max(end, e_)
        else:
            break
    mask = np.zeros((h, w), np.uint8)
    sub = ink[:, start:end + 1].astype(np.uint8) * 255
    mask[ya:yb, start:end + 1] = cv2.dilate(sub, np.ones((5, 5), np.uint8), iterations=2)
    cv2.imwrite(str(out or path), cv2.inpaint(a, mask, 7, cv2.INPAINT_TELEA))
    return start, end
