"""Paste real logos into blank white boxes an image model left empty.

Models draw logos badly or invent them, so the render asks for plain white boxes and the real
files are pasted in afterwards. Boxes are found as large near-white connected regions, ordered
left to right.
"""
import numpy as np
from PIL import Image


def find_white_slots(img, min_area=0.01, white=235):
    """Boxes ``(x, y, w, h)`` of near-white regions covering at least ``min_area`` of the page,
    sorted left to right. Needs OpenCV."""
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("find_white_slots needs opencv (cv2)") from exc
    a = np.asarray(img.convert("RGB"))
    h, w = a.shape[:2]
    mask = (a.min(2) > white).astype(np.uint8)
    n, _, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    boxes = [tuple(int(v) for v in stats[i][:4]) for i in range(1, n) if stats[i][4] > w * h * min_area]
    return sorted(boxes, key=lambda b: b[0])


def trim_logo(path, white=240):
    """Open a logo and crop its transparent/white margins."""
    x = Image.open(path).convert("RGBA")
    arr = np.asarray(x)
    vis = (arr[..., 3] > 10) & (arr[..., :3].min(2) < white)
    ys, xs = np.where(vis)
    if not len(xs):
        raise ValueError(f"{path}: logo has no visible pixels")
    return x.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))


def fill_slots(img, logo_paths, min_area=0.01, fit=(0.78, 0.7)):
    """Paste ``logo_paths`` into the white slots (left to right), centred, scaled to fit.
    Raises if the slot count differs from the logo count. Returns ``(new_image, boxes)``; the
    input image is not modified."""
    img = img.convert("RGB")
    slots = find_white_slots(img, min_area)
    if len(slots) != len(logo_paths):
        raise ValueError(f"found {len(slots)} white slots {slots}, got {len(logo_paths)} logos")
    for (x, y, w, h), p in zip(slots, logo_paths):
        lg = trim_logo(p)
        s = min(w * fit[0] / lg.width, h * fit[1] / lg.height)
        lg = lg.resize((max(1, int(lg.width * s)), max(1, int(lg.height * s))), Image.LANCZOS)
        img.paste(lg, (x + (w - lg.width) // 2, y + (h - lg.height) // 2), lg)
    return img, slots
