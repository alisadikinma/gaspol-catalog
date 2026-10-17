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


def _order_quad(pts):
    """Four points as TL, TR, BR, BL: two highest are the top pair, left one of each pair first."""
    pts = sorted(((float(x), float(y)) for x, y in pts), key=lambda p: p[1])
    top = sorted(pts[:2], key=lambda p: p[0])
    bot = sorted(pts[2:], key=lambda p: p[0])
    return [top[0], top[1], bot[1], bot[0]]


def _magenta_dist(a):
    return np.sqrt(((a.astype(int) - np.array([255, 0, 255])) ** 2).sum(2))


def find_slots(img, key="white", min_area=0.002):
    """Slots as quads of four ``(x, y)`` corners (TL, TR, BR, BL), sorted left to right then top
    to bottom. ``key="white"`` finds near-white boxes (as :func:`find_white_slots`);
    ``key="magenta"`` finds #ff00ff regions of any tilt. Needs OpenCV."""
    if key not in ("white", "magenta"):
        raise ValueError(f"key must be 'white' or 'magenta', got {key!r}")
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("find_slots needs opencv (cv2)") from exc
    a = np.asarray(img.convert("RGB"))
    h, w = a.shape[:2]
    if key == "white":
        boxes = find_white_slots(img, min_area)
        quads = [[(x, y), (x + bw - 1, y), (x + bw - 1, y + bh - 1), (x, y + bh - 1)] for x, y, bw, bh in boxes]
    else:
        mask = (_magenta_dist(a) < 120).astype(np.uint8)
        n, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
        quads = []
        for i in range(1, n):
            if stats[i][4] <= w * h * min_area:
                continue
            cnts, _ = cv2.findContours((labels == i).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            hull = cv2.convexHull(max(cnts, key=cv2.contourArea))
            approx = cv2.approxPolyDP(hull, 0.02 * cv2.arcLength(hull, True), True)
            pts = approx.reshape(-1, 2) if len(approx) == 4 else cv2.boxPoints(cv2.minAreaRect(hull))
            quads.append([(int(round(x)), int(round(y))) for x, y in _order_quad(pts)])
    return sorted(quads, key=lambda q: (min(p[0] for p in q), min(p[1] for p in q)))


def paste_quad(img, logo, quad, plate=None, fit=0.8):
    """Warp ``logo`` (RGBA image) onto ``quad`` (TL, TR, BR, BL), centred and scaled to ``fit`` of
    the quad's width and height. ``plate`` (RGB) is drawn over the quad first. Leftover magenta
    pixels in the quad's bounding box are filled from their neighbours. Returns a new image."""
    import cv2
    base = np.ascontiguousarray(np.asarray(img.convert("RGB")).copy())
    h, w = base.shape[:2]
    q = np.array(quad, dtype=np.float32)
    x0, y0 = np.maximum(q.min(0).astype(int) - 3, 0)
    x1, y1 = np.minimum(q.max(0).astype(int) + 4, [w, h])
    if plate is not None:
        cv2.fillConvexPoly(base, np.round(q).astype(np.int32), tuple(int(c) for c in plate[:3]))
    region = base[y0:y1, x0:x1]
    left = (_magenta_dist(region) < 120).astype(np.uint8)
    if left.any():
        left = cv2.dilate(left, np.ones((3, 3), np.uint8), iterations=2)
        base[y0:y1, x0:x1] = cv2.inpaint(np.ascontiguousarray(region), left, 3, cv2.INPAINT_TELEA)
    qw = int(round((np.linalg.norm(q[1] - q[0]) + np.linalg.norm(q[2] - q[3])) / 2))
    qh = int(round((np.linalg.norm(q[3] - q[0]) + np.linalg.norm(q[2] - q[1])) / 2))
    lg = logo.convert("RGBA")
    s = min(qw * fit / lg.width, qh * fit / lg.height)
    lg = lg.resize((max(1, int(lg.width * s)), max(1, int(lg.height * s))), Image.LANCZOS)
    canvas = Image.new("RGBA", (qw, qh), (0, 0, 0, 0))
    canvas.paste(lg, ((qw - lg.width) // 2, (qh - lg.height) // 2))
    src = np.array([[0, 0], [qw, 0], [qw, qh], [0, qh]], dtype=np.float32)
    m = cv2.getPerspectiveTransform(src, q)
    warped = cv2.warpPerspective(np.asarray(canvas), m, (w, h), flags=cv2.INTER_LINEAR,
                                 borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    alpha = warped[..., 3:4].astype(float) / 255
    out = base * (1 - alpha) + warped[..., :3] * alpha
    return Image.fromarray(out.round().clip(0, 255).astype(np.uint8))


def fill_slots(img, logo_paths, min_area=0.01, fit=(0.78, 0.7), key="white", mode="flat"):
    """Paste ``logo_paths`` into the slots (left to right), centred, scaled to fit. ``mode="flat"``
    pastes axis-aligned and returns ``(new_image, boxes)``; ``mode="quad"`` warps each logo onto
    its slot quad (:func:`paste_quad`) and returns ``(new_image, quads)``. Raises if the slot
    count differs from the logo count. The input image is not modified."""
    if mode not in ("flat", "quad"):
        raise ValueError(f"mode must be 'flat' or 'quad', got {mode!r}")
    img = img.convert("RGB")
    quads = find_slots(img, key, min_area)
    if len(quads) != len(logo_paths):
        raise ValueError(f"found {len(quads)} slots, got {len(logo_paths)} logos")
    if mode == "quad":
        for quad, p in zip(quads, logo_paths):
            img = paste_quad(img, trim_logo(p), quad, fit=min(fit))
        return img, quads
    boxes = []
    for quad, p in zip(quads, logo_paths):
        xs, ys = [pt[0] for pt in quad], [pt[1] for pt in quad]
        x, y, w, h = min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
        boxes.append((x, y, w, h))
        if key == "magenta":
            img = paste_quad(img, Image.new("RGBA", (1, 1)), quad)
        lg = trim_logo(p)
        s = min(w * fit[0] / lg.width, h * fit[1] / lg.height)
        lg = lg.resize((max(1, int(lg.width * s)), max(1, int(lg.height * s))), Image.LANCZOS)
        img.paste(lg, (x + (w - lg.width) // 2, y + (h - lg.height) // 2), lg)
    return img, boxes
