"""deck.md -> standalone HTML review page; prompts/slide-NN.md -> deck.md text."""
import html
import re
from pathlib import Path

CSS = """
:root{--bg:#f3f5f8;--card:#fff;--ink:#14213a;--mute:#5b677d;--line:#d9dfe8;--acc:#d9631e;--soft:#eef2f8}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--ink);font:16px/1.5 "Segoe UI",system-ui,Helvetica,Arial,sans-serif;margin:0;padding:24px 16px 56px}
.wrap{max-width:820px;margin:0 auto;display:flex;flex-direction:column;gap:16px}
h1{font-size:clamp(1.4rem,4vw,2rem);line-height:1.2;margin:0}
.intro{color:var(--mute);margin:0}
nav{display:flex;flex-wrap:wrap;gap:6px}
nav a{font-size:.85rem;color:var(--ink);text-decoration:none;border:1px solid var(--line);background:var(--card);border-radius:4px;padding:3px 8px}
.card{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:14px 16px;scroll-margin-top:12px;overflow-wrap:anywhere}
.card h2{margin:0 0 8px;font-size:1.2rem;line-height:1.25}
.card h3{margin:10px 0 4px;font-size:1rem;color:var(--acc)}
.card p{margin:6px 0}
.card ul{margin:6px 0;padding-left:20px}
.card li{margin:3px 0}
.tw{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:.92rem}
th,td{text-align:left;vertical-align:top;padding:6px 8px;border-bottom:1px solid var(--line)}
th{background:var(--soft)}
"""

_e = html.escape
_COMMENT = re.compile(r"<!--.*?-->", re.S)
_FRONT = re.compile(r"\A---\n.*?\n---\n", re.S)
_ROLE = re.compile(r"^([^:]{1,80}): (.+)$")
_SLIDE = re.compile(r"slide-(\d+)\.md\Z")
_TEXT_LINE = re.compile(r'^- (.+?): "(.*)"\s*$')


def _inline(s):
    out = _e(s)
    out = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", out)
    return out


def _item(s):
    m = _ROLE.match(s)
    if m:
        return f"<li><b>{_e(m.group(1))}:</b> {_e(m.group(2))}</li>"
    return f"<li>{_inline(s)}</li>"


def _table(rows):
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    cells = [r for r in cells if not all(re.fullmatch(r":?-{2,}:?", c) for c in r)]
    if not cells:
        return ""
    out = ['<div class="tw"><table><thead><tr>']
    out += [f"<th>{_e(c)}</th>" for c in cells[0]]
    out.append("</tr></thead><tbody>")
    for r in cells[1:]:
        out.append("<tr>" + "".join(f"<td>{_e(c)}</td>" for c in r) + "</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def _body(lines):
    out, items, rows = [], [], []

    def flush():
        nonlocal items, rows
        if items:
            out.append("<ul>" + "".join(items) + "</ul>")
            items = []
        if rows:
            out.append(_table(rows))
            rows = []

    for raw in lines:
        line = raw.rstrip()
        if not line.strip() or line.strip() == "---":
            flush()
        elif line.startswith("|"):
            if items:
                flush()
            rows.append(line)
        elif re.match(r"^\s*[-*] ", line):
            if rows:
                flush()
            items.append(_item(re.sub(r"^\s*[-*] ", "", line)))
        elif line.startswith("###"):
            flush()
            out.append(f"<h3>{_e(line.lstrip('# ').strip())}</h3>")
        else:
            flush()
            out.append(f"<p>{_inline(line.strip())}</p>")
    flush()
    return "".join(out)


def review_html(md_text, title):
    """Standalone phone-readable page: one card per `#`/`##` section, all text escaped."""
    text = _COMMENT.sub("", md_text or "")
    text = _FRONT.sub("", text.replace("\r\n", "\n"))
    intro, sections, cur = [], [], None
    for line in text.split("\n"):
        m = re.match(r"^(#{1,2}) (.+)$", line)
        if m:
            if m.group(1) == "#" and cur is None and not sections:
                intro.append(("title", m.group(2)))
                continue
            cur = (m.group(2).strip(), [])
            sections.append(cur)
        elif cur is not None:
            cur[1].append(line)
        else:
            intro.append(("line", line))
    nav = "".join(f'<a href="#s{i}">{_e(h)}</a>' for i, (h, _) in enumerate(sections, 1))
    cards = "".join(
        f'<section class="card" id="s{i}"><h2>{_e(h)}</h2>{_body(b)}</section>'
        for i, (h, b) in enumerate(sections, 1))
    head = next((v for k, v in intro if k == "title"), title)
    lead = _body([v for k, v in intro if k == "line"])
    return (
        '<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{_e(title)}</title><style>{CSS}</style></head><body><div class=\"wrap\">"
        f"<header><h1>{_e(head)}</h1><div class=\"intro\">{lead}</div></header>"
        f"<nav>{nav}</nav>{cards}</div></body></html>\n"
    )


def from_prompts(prompts_dir):
    """Markdown with one `## Slide NN` section per prompts/slide-NN.md, quoted TEXT lines as bullets."""
    d = Path(prompts_dir)
    found = sorted(((int(m.group(1)), p) for p in d.glob("slide-*.md")
                    if p.is_file() and (m := _SLIDE.match(p.name))), key=lambda t: t[0])
    if not found:
        raise ValueError(f"no slide-NN.md in {prompts_dir}")
    out = ["# Deck text", "", "> Taken from the prompt files, so this text and the rendered text cannot differ.", ""]
    for n, p in found:
        out.append(f"## Slide {n:02d}")
        out.append("")
        for line in p.read_text(encoding="utf-8").splitlines():
            m = _TEXT_LINE.match(line)
            if m:
                out.append(f"- {m.group(1)}: {m.group(2)}")
        out.append("")
    return "\n".join(out)
