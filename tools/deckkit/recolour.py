"""Recolour the thin vertical accent bars beside text points, top to bottom."""
import cv2
import numpy as np
from PIL import Image

PAD = 4
MIN_CONTRAST = 1200   # |core - background|^2 below this: the bar cannot be told from the page
VERIFY_TOL = 16       # max per-channel gap allowed between a recoloured bar core and its target


def _rgb(hexstr):
    s = str(hexstr).strip()
    if len(s) != 7 or s[0] != "#":
        raise ValueError(f"bad colour {hexstr!r}, expected #rrggbb")
    try:
        return tuple(int(s[i:i + 2], 16) for i in (1, 3, 5))
    except ValueError:
        raise ValueError(f"bad colour {hexstr!r}, expected #rrggbb") from None


def find_bars(arr, x_from=0.55, source="#23857f", tol=60):
    """Bar boxes (x, y, w, h) in page coordinates, sorted top to bottom."""
    h, w, _ = arr.shape
    x0 = int(w * x_from)
    reg = arr[:, x0:].astype(int)
    dist = np.sqrt(((reg - np.array(_rgb(source))) ** 2).sum(2))
    mask = (dist <= tol).astype(np.uint8)
    k, _, st, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    bars = [(int(st[i, 0]) + x0, int(st[i, 1]), int(st[i, 2]), int(st[i, 3])) for i in range(1, k)
            if st[i, 3] > h * 0.05 and st[i, 2] < w * 0.012 and st[i, 3] / max(st[i, 2], 1) > 4]
    return sorted(bars, key=lambda b: b[1])


def bars(img, colours, x_from=0.55, source="#23857f", tol=60):
    """Recolour the bars found right of ``x_from`` (page fraction) to ``colours`` top to bottom.

    Each pixel moves along the line from the local background to the bar core, so
    antialiased edges keep their blend. Wrong bar count -> ValueError, nothing changed."""
    targets = [_rgb(c) for c in colours]
    arr = np.array(img.convert("RGB"))
    found = find_bars(arr, x_from, source, tol)
    if len(found) != len(targets):
        raise ValueError(f"found {len(found)} bars, expected {len(targets)}")
    ph, pw, _ = arr.shape
    out = arr.copy()
    for i, ((x, y, w, h), tgt) in enumerate(zip(found, targets)):
        y1, y2 = max(y - PAD, 0), min(y + h + PAD, ph)
        x1, x2 = max(x - PAD, 0), min(x + w + PAD, pw)
        blk = arr[y1:y2, x1:x2].astype(float)
        bg = np.median(arr[y1:y2, min(x2 + 2, pw - 1):min(x2 + 10, pw)].reshape(-1, 3), 0)
        core = np.median(arr[y + h // 4:y + 3 * h // 4, x + 1:max(x + w - 1, x + 2)].reshape(-1, 3), 0)
        d = core - bg
        if d @ d < MIN_CONTRAST:
            raise ValueError(f"bar {i} is too close to the background colour to recolour safely")
        t = np.clip(((blk - bg) @ d) / max(d @ d, 1), 0, 1)[..., None]
        out[y1:y2, x1:x2] = np.clip(blk + t * (np.array(tgt, float) - core), 0, 255).round().astype(np.uint8)
    for i, ((x, y, w, h), tgt) in enumerate(zip(found, targets)):
        got = np.median(out[y + h // 4:y + 3 * h // 4, x + 1:max(x + w - 1, x + 2)].reshape(-1, 3), 0)
        if np.abs(got - np.array(tgt, float)).max() > VERIFY_TOL:
            raise ValueError(f"bar {i} did not take the target colour {colours[i]} (got {got.round().astype(int).tolist()})")
    return Image.fromarray(out)
