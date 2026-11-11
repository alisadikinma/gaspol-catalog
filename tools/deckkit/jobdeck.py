"""Job deck: swap the text of marked slots in an HTML deck, render every slide to one PDF.

A deck marks its swappable text with ``data-job="<slot>"`` (and optionally ``data-job-max="<n>"``,
the most visible characters allowed, default 120). ``fill`` changes only the inner HTML of those
elements; every other byte of the deck stays as it was. ``render`` prints one page per
``div.slide[id]`` through headless Chrome and joins the pages into a 1920x1080 PDF.
"""
import html
import os
import re
import subprocess
import tempfile
import time
from html.parser import HTMLParser
from pathlib import Path

from PIL import Image

SLOTS = (["cover-eye", "cover-head", "cover-sub", "cta-eye", "cta-head"]
         + [f"cta-tile-{n}-title" for n in range(1, 5)]
         + [f"cta-tile-{n}-text" for n in range(1, 5)]
         + ["cta-sub"])
DEFAULT_MAX = 120
SIZE = (1920, 1080)
VOID = frozenset("area base br col embed hr img input link meta param source track wbr".split())
EMPHASIS = re.compile(r"\*([^*\n]+)\*")


def _line_starts(text):
    starts, pos = [0], 0
    for line in text.split("\n")[:-1]:
        pos += len(line) + 1
        starts.append(pos)
    return starts


class _Scan(HTMLParser):
    """Locate the inner span of every data-job element."""

    def __init__(self, text):
        super().__init__(convert_charrefs=False)
        self.text = text
        self.starts = _line_starts(text)
        self.found = []        # dicts: slot, max, tag, inner_start, inner_end
        self.open = None       # slot currently being read
        self.depth = 0

    def _pos(self):
        line, col = self.getpos()
        return self.starts[line - 1] + col

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        slot = attrs.get("data-job")
        if self.open is not None:
            if slot is not None:
                raise ValueError(f"{slot}: nested inside slot {self.open['slot']}")
            if tag == self.open["tag"]:
                self.depth += 1
            return
        if slot is None:
            return
        if tag in VOID:
            raise ValueError(f"{slot}: slot element <{tag}> has no inner text")
        raw = attrs.get("data-job-max")
        try:
            limit = DEFAULT_MAX if raw is None else int(raw)
            if limit < 1:
                raise ValueError
        except ValueError:
            raise ValueError(f"{slot}: data-job-max must be a positive integer, got {raw!r}") from None
        self.open = {"slot": slot, "max": limit, "tag": tag,
                     "inner_start": self._pos() + len(self.get_starttag_text())}
        self.depth = 1

    def handle_startendtag(self, tag, attrs):
        slot = dict(attrs).get("data-job")
        if slot is not None:
            raise ValueError(f"{slot}: slot element <{tag}/> has no inner text")

    def handle_endtag(self, tag):
        if self.open is None or tag != self.open["tag"]:
            return
        self.depth -= 1
        if self.depth == 0:
            self.open["inner_end"] = self._pos()
            self.found.append(self.open)
            self.open = None


def _scan(text):
    s = _Scan(text)
    s.feed(text)
    s.close()
    if s.open is not None:
        raise ValueError(f"{s.open['slot']}: slot element is never closed")
    return s.found


def fill(html_text, slots):
    """Return ``html_text`` with the inner HTML of each named slot replaced.

    Text is plain; ``*word*`` becomes ``<em>word</em>``. ValueError names the slot when it is not
    in the fixed vocabulary, not in the deck, over its ``data-job-max`` (emphasis markers do not
    count), not a string, or contains ``<`` or ``>``.
    """
    if not slots:
        return html_text
    for name, value in slots.items():
        if name not in SLOTS:
            raise ValueError(f"{name}: unknown slot")
        if not isinstance(value, str):
            raise ValueError(f"{name}: must be a string")
        if "<" in value or ">" in value:
            raise ValueError(f"{name}: must not contain < or >")
    found = _scan(html_text)
    by_name = {}
    for f in found:
        by_name.setdefault(f["slot"], []).append(f)
    edits = []
    for name, value in slots.items():
        if name not in by_name:
            raise ValueError(f"{name}: slot not present in the deck")
        visible = EMPHASIS.sub(r"\1", value)
        for f in by_name[name]:
            if len(visible) > f["max"]:
                raise ValueError(f"{name}: at most {f['max']} characters, got {len(visible)}")
            body = EMPHASIS.sub(r"<em>\1</em>", html.escape(value, quote=True))
            edits.append((f["inner_start"], f["inner_end"], body))
    out = html_text
    for start, end, body in sorted(edits, reverse=True):
        out = out[:start] + body + out[end:]
    return out


class _Slides(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.ids = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "div" and a.get("id") and "slide" in (a.get("class") or "").split():
            self.ids.append(a["id"])


def slide_ids(html_text):
    """Ids of ``div.slide[id]`` in document order."""
    p = _Slides()
    p.feed(html_text)
    p.close()
    return p.ids


def _run_chrome(binary, argv, timeout):
    with tempfile.TemporaryDirectory() as profile:
        cmd = [binary, "--user-data-dir=" + profile, "--no-first-run", *argv]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Chrome timed out after {timeout}s") from None
    if res.returncode != 0:
        tail = "\n".join((res.stderr or "").strip().splitlines()[-10:])
        raise RuntimeError(f"Chrome exited {res.returncode}: {tail}")


def _runner(chrome):
    """``chrome``: None (find it), a binary path, or a callable ``run(argv, timeout)``."""
    if callable(chrome):
        return chrome
    binary = chrome
    if binary is None:
        from . import chrome as chrome_mod
        try:
            binary = chrome_mod.find_chrome()
        except RuntimeError as exc:
            if str(exc) == chrome_mod.NOT_FOUND:
                raise RuntimeError("chrome not found") from None
            raise
    return lambda argv, timeout: _run_chrome(binary, argv, timeout)


def _hide_others(page, sid):
    # attribute selector: an id like "1st" or "a.b" is not a valid #id selector
    if '"' in sid or "\\" in sid:
        raise ValueError(f"{sid}: slide id must not contain a quote or backslash")
    rule = f'.slide:not([id="{sid}"]){{display:none !important}}'
    i = page.rfind("</style>")
    if i < 0:
        raise ValueError("deck: no </style> to hold the slide rule")
    return page[:i] + rule + page[i:]


def render(deck_path, slots, out_pdf, chrome=None, timeout=50):
    """Fill ``slots`` into the deck and write one PDF page per slide. Returns ``out_pdf``.

    ``timeout`` is ONE deadline for the whole render: each Chrome run gets the time left.
    Temporary pages are written inside the deck folder (relative images must resolve) and are
    always deleted. The PDF is written to a temp file and moved into place. ``chrome``: see
    ``_runner``.
    """
    deck = Path(deck_path)
    if not deck.is_file():
        raise FileNotFoundError(f"deck not found: {deck_path}")
    filled = fill(deck.read_text(encoding="utf-8"), slots)
    ids = slide_ids(filled)
    if not ids:
        raise ValueError("deck: no div.slide[id] found")
    pages = [_hide_others(filled, sid) for sid in ids]
    run = _runner(chrome)
    deadline = time.monotonic() + timeout
    folder = deck.resolve().parent
    temp = []
    tmp_pdf = None
    try:
        with tempfile.TemporaryDirectory() as shots:
            images = []
            for n, page in enumerate(pages, 1):
                left = deadline - time.monotonic()
                if left <= 0:
                    raise RuntimeError(f"render ran out of time ({timeout}s) before slide {ids[n - 1]}")
                fd, name = tempfile.mkstemp(dir=folder, prefix="_jobdeck_", suffix=".html")
                src = Path(name)
                temp.append(src)
                with os.fdopen(fd, "w", encoding="utf-8") as fh:
                    fh.write(page)
                png = Path(shots) / f"{n}.png"
                run(["--headless=new", "--disable-gpu", "--hide-scrollbars",
                     f"--window-size={SIZE[0]},{SIZE[1]}", "--virtual-time-budget=8000",
                     f"--screenshot={png}", src.as_uri()], left)
                if not png.is_file():
                    raise RuntimeError(f"Chrome wrote no screenshot for slide {ids[n - 1]}")
                with Image.open(png) as im:
                    im.load()
                    if im.width < SIZE[0] or im.height < SIZE[1]:
                        raise RuntimeError(f"screenshot is smaller than {SIZE[0]}x{SIZE[1]}: "
                                           f"{im.width}x{im.height}")
                    images.append(im.convert("RGB").crop((0, 0, *SIZE)))
            out = Path(out_pdf)
            out.parent.mkdir(parents=True, exist_ok=True)
            fd, name = tempfile.mkstemp(dir=out.parent, prefix=".jobdeck_", suffix=".pdf.tmp")
            os.close(fd)
            tmp_pdf = Path(name)
            images[0].save(tmp_pdf, "PDF", save_all=True, append_images=images[1:], resolution=96.0)
            os.replace(tmp_pdf, out)
            tmp_pdf = None
    finally:
        for p in temp + ([tmp_pdf] if tmp_pdf else []):
            try:
                p.unlink()
            except FileNotFoundError:
                pass
    return str(out_pdf)
