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


def _sharp_corners(cnt, rough):
    """Refine a rough quad (TL, TR, BR, BL) to the sharp corners of a slot whose corners the
    model drew rounded (a phone screen), maybe with a notch, seen in perspective.

    For each side, points along the convex hull (which bridges a notch) near the side's middle
    70 percent (the rounded corners are left out) get a fitted line; adjacent lines meet at the
    corner. Falls back
    to the rough corner when a side has too few points (2026-11-01: minAreaRect is a rotated
    rectangle, not a perspective quad, so a tilted phone screen ran off its frame)."""
    import cv2
    # points every pixel along the convex hull: the hull bridges a notch with the true edge line
    h = cv2.convexHull(cnt).reshape(-1, 2).astype(float)
    segs = []
    for a, b in zip(h, np.roll(h, -1, axis=0)):
        n_pts = max(2, int(np.linalg.norm(b - a)))
        segs.append(a + (b - a) * np.linspace(0, 1, n_pts, endpoint=False)[:, None])
    p = np.vstack(segs)
    q = np.array(rough, float)
    lines = []
    for k in range(4):
        a, b = q[k], q[(k + 1) % 4]
        d = b - a
        L = np.linalg.norm(d)
        if L < 1:
            return rough
        u = d / L
        n = np.array([-u[1], u[0]])
        t = (p - a) @ u / L
        dist = np.abs((p - a) @ n)
        sel = p[(t > 0.15) & (t < 0.85) & (dist < max(3.0, 0.04 * L))]
        if len(sel) < 5:
            return rough
        vx, vy, x0, y0 = cv2.fitLine(sel.astype(np.float32), cv2.DIST_HUBER, 0, 0.01, 0.01).ravel()
        lines.append((np.array([x0, y0]), np.array([vx, vy])))
    out = []
    for k in range(4):
        (p1, d1), (p2, d2) = lines[k - 1], lines[k]
        m = np.array([d1, -d2]).T
        if abs(np.linalg.det(m)) < 1e-6:
            return rough
        s1, _ = np.linalg.solve(m, p2 - p1)
        c = p1 + s1 * d1
        if np.linalg.norm(c - q[k]) > 0.25 * np.linalg.norm(q[(k + 1) % 4] - q[k]):
            return rough
        out.append((float(c[0]), float(c[1])))
    return out


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
            cnts, _ = cv2.findContours((labels == i).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            cnt = max(cnts, key=cv2.contourArea)
            hull = cv2.convexHull(cnt)
            approx = cv2.approxPolyDP(hull, 0.02 * cv2.arcLength(hull, True), True)
            pts = approx.reshape(-1, 2) if len(approx) == 4 else cv2.boxPoints(cv2.minAreaRect(hull))
            rough = _order_quad(pts)
            quads.append([(int(round(x)), int(round(y))) for x, y in _sharp_corners(cnt, rough)])
    return sorted(quads, key=lambda q: (min(p[0] for p in q), min(p[1] for p in q)))


def paste_quad(img, logo, quad, plate=None, fit=0.8, mode="quad", multiply=False, shade=False):
    """Warp ``logo`` (RGBA image) onto ``quad`` (TL, TR, BR, BL), centred and scaled to ``fit`` of
    the quad's width and height. ``plate`` (RGB) is drawn over the quad first. Leftover magenta
    pixels in the quad's bounding box are filled from their neighbours. Returns a new image.

    ``mode="quad"`` covers the whole quad. ``mode="pixel"`` pastes (and draws ``plate``) only onto
    pixels inside the quad that were magenta, so an object the model drew in front of the slot
    stays in front of the logo; use it with magenta slots only.

    For a logo printed on a vehicle body (a sticker, not a sign): ``multiply=True`` multiplies the
    logo colours into the body, so the logo's white ground vanishes and the body texture shows
    through; ``shade=True`` carries the render's own light and shadow over the pasted area
    (original luminance over its bright reference inside the quad)."""
    import cv2
    if mode not in ("quad", "pixel"):
        raise ValueError(f"mode must be 'quad' or 'pixel', got {mode!r}")
    base = np.ascontiguousarray(np.asarray(img.convert("RGB")).copy())
    orig = base.astype(float)
    h, w = base.shape[:2]
    q = np.array(quad, dtype=np.float32)
    x0, y0 = np.maximum(q.min(0).astype(int) - 3, 0)
    x1, y1 = np.minimum(q.max(0).astype(int) + 4, [w, h])
    visible = None
    if mode == "pixel":
        inside = np.zeros((h, w), np.uint8)
        cv2.fillConvexPoly(inside, np.round(q).astype(np.int32), 1)
        visible = (inside > 0) & (_magenta_dist(base) < 120)
    if plate is not None:
        before = base.copy()
        cv2.fillConvexPoly(base, np.round(q).astype(np.int32), tuple(int(c) for c in plate[:3]))
        if visible is not None:
            base = np.where(visible[..., None], base, before)
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
    if visible is not None:
        alpha = alpha * visible[..., None]
    top = warped[..., :3].astype(float)
    if multiply:
        top = base * top / 255.0
    out = base * (1 - alpha) + top * alpha
    if mode == "pixel":
        # The model tints the bezel next to a magenta screen (about 60,30,60): too far from
        # magenta to be inpainted, it reads as a purple rim (seen 2026-11-01).
        # Within a band around the quad, neutralise pink-tinted pixels to their own luminance.
        band = np.zeros((h, w), np.uint8)
        cv2.fillConvexPoly(band, np.round(q).astype(np.int32), 1)
        r_px = max(18, int(0.08 * min(qw, qh)))
        band = cv2.dilate(band, np.ones((3, 3), np.uint8), iterations=r_px) > 0
        r, g, b = out[..., 0], out[..., 1], out[..., 2]
        tint = band & (r - g > 12) & (b - g > 12) & (alpha[..., 0] < 0.5)
        lum = out @ np.array([0.299, 0.587, 0.114])
        out[tint] = lum[tint][:, None]
    if shade:
        lum = orig @ np.array([0.299, 0.587, 0.114])
        area = np.zeros((h, w), np.uint8)
        cv2.fillConvexPoly(area, np.round(q).astype(np.int32), 1)
        inside = area > 0
        ref = np.percentile(lum[inside], 95) if inside.any() else 255.0
        light = np.clip(lum / max(ref, 1.0), 0.55, 1.05)
        touched = inside if plate is not None else (alpha[..., 0] > 0)
        out = np.where(touched[..., None], out * light[..., None], out)
    return Image.fromarray(out.round().clip(0, 255).astype(np.uint8))


def _ground(a, x, y, w, h, gap):
    """Median colour of a 4 px ring ``gap`` px outside the box (the page ground behind a slot)."""
    H, W = a.shape[:2]
    g0, g1 = gap, gap + 4
    ring = np.concatenate([
        a[max(y - g1, 0):max(y - g0, 0), max(x - g1, 0):min(x + w + g1, W)].reshape(-1, 3),
        a[min(y + h + g0, H):min(y + h + g1, H), max(x - g1, 0):min(x + w + g1, W)].reshape(-1, 3),
        a[max(y - g0, 0):min(y + h + g0, H), max(x - g1, 0):max(x - g0, 0)].reshape(-1, 3),
        a[max(y - g0, 0):min(y + h + g0, H), min(x + w + g0, W):min(x + w + g1, W)].reshape(-1, 3)])
    return tuple(int(v) for v in np.median(ring, axis=0)) if len(ring) else (255, 255, 255)


def fill_slots(img, logo_paths, min_area=0.01, fit=(0.78, 0.7), key="white", mode="flat", pad=0):
    """Paste ``logo_paths`` into the slots (left to right), centred, scaled to fit. ``mode="flat"``
    pastes axis-aligned and returns ``(new_image, boxes)``; ``mode="quad"`` warps each logo onto
    its slot quad (:func:`paste_quad`) and returns ``(new_image, quads)``; ``mode="pixel"`` is
    ``quad`` but only over pixels that were magenta (objects in front of the slot stay in front)
    and needs ``key="magenta"``, else ValueError. Raises if the slot
    count differs from the logo count. The input image is not modified.

    ``pad`` (flat + magenta only) paints the slot plus ``pad`` px around it with the ground colour
    sampled just outside, covering the soft pink glow some image models draw around a slot."""
    if mode not in ("flat", "quad", "pixel"):
        raise ValueError(f"mode must be 'flat', 'quad' or 'pixel', got {mode!r}")
    if mode == "pixel" and key != "magenta":
        raise ValueError("mode='pixel' needs key='magenta'")
    img = img.convert("RGB")
    quads = find_slots(img, key, min_area)
    if len(quads) != len(logo_paths):
        raise ValueError(f"found {len(quads)} slots, got {len(logo_paths)} logos")
    if mode in ("quad", "pixel"):
        for quad, p in zip(quads, logo_paths):
            img = paste_quad(img, trim_logo(p), quad, fit=min(fit), mode=mode)
        return img, quads
    boxes = []
    for quad, p in zip(quads, logo_paths):
        xs, ys = [pt[0] for pt in quad], [pt[1] for pt in quad]
        x, y, w, h = min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
        boxes.append((x, y, w, h))
        if key == "magenta" and pad > 0:
            ground = _ground(np.asarray(img), x, y, w, h, pad + 2)
            img = img.copy()
            img.paste(Image.new("RGB", (w + 2 * pad, h + 2 * pad), ground), (x - pad, y - pad))
        elif key == "magenta":
            img = paste_quad(img, Image.new("RGBA", (1, 1)), quad)
        lg = trim_logo(p)
        s = min(w * fit[0] / lg.width, h * fit[1] / lg.height)
        lg = lg.resize((max(1, int(lg.width * s)), max(1, int(lg.height * s))), Image.LANCZOS)
        img.paste(lg, (x + (w - lg.width) // 2, y + (h - lg.height) // 2), lg)
    return img, boxes


def paste_quads(spec, base_dir="."):
    """Paste one logo onto hand-measured panels of a render that has no slot (a truck side, a bus
    body). Spec: ``{"src", "dst", "logo", "plate": [r, g, b] or null, "fit": 0.8,
    "quads": [[[x, y] TL, TR, BR, BL], ...], "note": "why"}``; paths relative to ``base_dir``.
    ``plate`` draws a flat panel first (white behind a logo on a coloured body); ``multiply`` and
    ``shade`` make it read as a sticker on the body (see :func:`paste_quad`). A quad may also be
    ``{"quad": [...], "plate": ..., "multiply": ..., "shade": ..., "fit": ...}`` to override the
    spec-level options for that panel (white backing on a yellow truck only). Each quad is
    checked (4 points, inside the image) before anything is pasted. Returns the written path.

    An app screen onto a magenta phone screen: ``"mode": "pixel"`` paints only the pixels that
    were magenta (rounded corners, a notch and an object in front stay), ``"trim": false`` keeps
    the screenshot's light margins, and ``"fit": 1.0`` fills the quad. Hand-measured quads are
    for screens :func:`find_slots` misreads, such as one half hidden behind a forklift."""
    import os
    for k in ("src", "dst", "logo", "quads"):
        if k not in spec:
            raise ValueError(f"spec missing {k!r}")
    img = Image.open(os.path.join(base_dir, spec["src"])).convert("RGB")
    w, h = img.size
    quads = spec["quads"]
    if not quads:
        raise ValueError("no quads")
    keys = ("plate", "fit", "multiply", "shade", "mode")
    mode = spec.get("mode", "quad")
    if mode not in ("quad", "pixel"):
        raise ValueError(f"mode must be 'quad' or 'pixel', got {mode!r}")
    items = []
    for i, q in enumerate(quads):
        opt = {k: spec.get(k) for k in keys}
        if isinstance(q, dict):
            extra = q.keys() - set(keys) - {"quad", "note"}
            if extra:
                raise ValueError(f"quad {i}: unknown keys {sorted(extra)}")
            opt.update({k: q[k] for k in keys if k in q})
            q = q.get("quad", [])
        items.append((q, opt))
    for i, (q, _) in enumerate(items):
        if len(q) != 4 or any(len(p) != 2 for p in q):
            raise ValueError(f"quad {i}: needs 4 [x, y] points")
        if any(not (0 <= x < w and 0 <= y < h) for x, y in q):
            raise ValueError(f"quad {i}: point outside the {w}x{h} image")
    logo_path = os.path.join(base_dir, spec["logo"])
    logo = trim_logo(logo_path) if spec.get("trim", True) else Image.open(logo_path).convert("RGBA")
    for q, o in items:
        img = paste_quad(img, logo, [tuple(p) for p in q], plate=tuple(o["plate"]) if o["plate"] else None,
                         fit=o["fit"] or 0.8, mode=o["mode"] or "quad", multiply=bool(o["multiply"]),
                         shade=bool(o["shade"]))
    out = os.path.join(base_dir, spec["dst"])
    img.save(out)
    return out
