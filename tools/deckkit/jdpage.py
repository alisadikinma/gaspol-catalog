"""JD page: JSON data -> one A4 "How I would build your system" PDF (headless Chrome).

The template has no slot for contact info, links or handles, and any string that looks
like one is rejected before anything is rendered.
"""
import base64
import html
import mimetypes
import re
import string
import tempfile
from pathlib import Path

TEMPLATE = Path(__file__).parent / "templates" / "jdpage.html"
NO_LINKS = "no links on the JD page"
HEX = re.compile(r"#[0-9a-fA-F]{6}\Z")
_TLDS = "com|net|org|io|ai|id|co|me|app|dev|info|biz|xyz|tech|site|online|link|ly|gg|tv|us|uk|de|sg|my"
LINK = re.compile(
    r"[a-z][a-z0-9+.-]*://"                    # any scheme://
    r"|\bwww\."
    r"|[\w.+-]+@[\w-]+\.[\w.-]+"               # email
    r"|(?<![\w@])@\w{2,}"                      # handle
    rf"|\b[\w-]+(?:\.[\w-]+)*\.(?:{_TLDS})\b", # bare domain
    re.I)

MAX = {"title": 90, "problem": 280, "flow": 90, "phase.name": 40, "phase.deliverable": 140,
       "phase.days": 20, "risk": 120, "mitigation": 160, "proof.label": 40, "proof.number": 20,
       "proof.source": 60, "cta": 160, "brand.name": 60}


def _str(v, field, limit):
    if not isinstance(v, str) or not v.strip():
        raise ValueError(f"{field}: must be a non-empty string")
    if LINK.search(v):
        raise ValueError(f"{field}: {NO_LINKS}")
    if len(v) > limit:
        raise ValueError(f"{field}: at most {limit} characters, got {len(v)}")
    return v


def _list(d, key, lo, hi):
    v = d.get(key) if isinstance(d, dict) else None
    if v is None:
        raise ValueError(f"{key}: required")
    if not isinstance(v, list):
        raise ValueError(f"{key}: must be a list")
    if not lo <= len(v) <= hi:
        want = f"exactly {lo}" if lo == hi else f"{lo} to {hi}"
        raise ValueError(f"{key}: needs {want} items, got {len(v)}")
    return v


def _item(obj, field, keys):
    if not isinstance(obj, dict):
        raise ValueError(f"{field}: must be an object")
    for k, limit in keys.items():
        if k not in obj:
            raise ValueError(f"{field}.{k}: required")
        v = obj[k]
        if k == "days" and isinstance(v, int) and not isinstance(v, bool):
            v = str(v)
        _str(v, f"{field}.{k}", limit)


def validate(data):
    """Raise ValueError('field: reason') on the first problem."""
    if not isinstance(data, dict):
        raise ValueError("data: must be a JSON object")
    for k in ("title", "problem", "cta"):
        if k not in data:
            raise ValueError(f"{k}: required")
        _str(data[k], k, MAX[k])
    for i, s in enumerate(_list(data, "flow", 3, 6)):
        _str(s, f"flow[{i}]", MAX["flow"])
    for i, p in enumerate(_list(data, "phases", 3, 3)):
        _item(p, f"phases[{i}]", {"name": MAX["phase.name"], "deliverable": MAX["phase.deliverable"],
                                  "days": MAX["phase.days"]})
    for i, r in enumerate(_list(data, "risks", 2, 4)):
        _item(r, f"risks[{i}]", {"risk": MAX["risk"], "mitigation": MAX["mitigation"]})
    for i, p in enumerate(_list(data, "proof", 1, 3)):
        _item(p, f"proof[{i}]", {"label": MAX["proof.label"], "number": MAX["proof.number"],
                                 "source": MAX["proof.source"]})
    b = data.get("brand")
    if b is None:
        raise ValueError("brand: required")
    if not isinstance(b, dict):
        raise ValueError("brand: must be an object")
    _item(b, "brand", {"name": MAX["brand.name"]})
    if "color" not in b:
        raise ValueError("brand.color: required")
    if not isinstance(b["color"], str) or not HEX.match(b["color"]):
        raise ValueError("brand.color: must be a #RRGGBB hex colour")
    if "logo_path" in b:
        _str(b["logo_path"], "brand.logo_path", 500)
        if not Path(b["logo_path"]).is_file():
            raise ValueError("brand.logo_path: file not found")


def _e(v):
    return html.escape(str(v), quote=True)


def _tint(color):
    r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))
    return "#{:02x}{:02x}{:02x}".format(*(round(c + (255 - c) * 0.9) for c in (r, g, b)))


def _logo(path):
    if not path:
        return ""
    mime = mimetypes.guess_type(path)[0] or "image/png"
    raw = base64.b64encode(Path(path).read_bytes()).decode("ascii")
    return f'<img alt="" src="data:{_e(mime)};base64,{raw}">'


def build_html(data):
    """Validated data -> the page HTML. Every dynamic string is escaped."""
    validate(data)
    b = data["brand"]
    flow = '<span class="arrow">&#8594;</span>'.join(
        f'<span class="step"><b>{i}.</b>{_e(s)}</span>' for i, s in enumerate(data["flow"], 1))
    phases = "".join(
        f'<div class="phase"><div class="pn">{i}. {_e(p["name"])}</div>'
        f'<div class="pd">{_e(p["days"])} days</div><div>{_e(p["deliverable"])}</div></div>'
        for i, p in enumerate(data["phases"], 1))
    risks = "".join(f'<tr><td>{_e(r["risk"])}</td><td>{_e(r["mitigation"])}</td></tr>' for r in data["risks"])
    proof = "".join(
        f'<div class="chip"><div class="num">{_e(p["number"])}</div><div class="lab">{_e(p["label"])}</div>'
        f'<div class="src">{_e(p["source"])}</div></div>' for p in data["proof"])
    return string.Template(TEMPLATE.read_text(encoding="utf-8")).substitute(
        title=_e(data["title"]), problem=_e(data["problem"]), cta=_e(data["cta"]),
        brand_name=_e(b["name"]), color=b["color"], tint=_tint(b["color"]),
        logo=_logo(b.get("logo_path")), flow=flow, phases=phases, risks=risks, proof=proof)


def render(data, out_pdf):
    """Validate, fill the template, print one A4 page to ``out_pdf``. Returns the path."""
    from . import chrome
    page = build_html(data)
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "jdpage.html"
        src.write_text(page, encoding="utf-8")
        return chrome.print_pdf(src, out_pdf)
