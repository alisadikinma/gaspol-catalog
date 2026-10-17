"""Slide spec (slides.json) + style preset + house standard -> prompts/slide-NN.md + manifest.json."""
import datetime
import hashlib
import json
import re
from pathlib import Path

from . import house as house_mod

NO_SELLER = "no seller: pass --house or set GASPOL_CATALOG_HOUSE"
LOG_HEADING = "REVISION LOG"
_LOG_RE = re.compile(r"^REVISION LOG[ \t]*$", re.M)


def prompt_body(text):
    """A prompt file's text without its REVISION LOG section: what the image model is sent.

    The log names old defect text (a dropped number, a duplicated line); sent to the model it
    could be printed, so it never leaves the file."""
    m = _LOG_RE.search(text)
    return (text[:m.start()] if m else text).rstrip("\n")


def prompt_sha(text):
    """sha256 of ``prompt_body(text)`` (a log edit is not a prompt change)."""
    return hashlib.sha256(prompt_body(text).encode("utf-8")).hexdigest()


def _log_lines(text):
    """Lines under the REVISION LOG heading of an existing prompt file (blank tail dropped)."""
    m = _LOG_RE.search(text)
    if not m:
        return []
    lines = text[m.end():].splitlines()
    while lines and not lines[-1].strip():
        lines.pop()
    return [ln for ln in lines if ln.strip()]


def _label(slide, index):
    n = slide.get("n") if isinstance(slide, dict) else None
    return f"slide {n}" if n is not None else f"slide at index {index}"


def _check_slide(slide, index):
    """Required keys and types; ValueError names the slide and the field."""
    if not isinstance(slide, dict):
        raise ValueError(f"slide at index {index}: must be an object")
    label = _label(slide, index)
    if "n" not in slide:
        raise ValueError(f"{label}: field 'n' is missing")
    if not isinstance(slide["n"], int) or isinstance(slide["n"], bool):
        raise ValueError(f"{label}: field 'n' must be an integer")
    for key in ("layout", "visual"):
        if key not in slide:
            raise ValueError(f"{label}: field '{key}' is missing")
        if not isinstance(slide[key], str):
            raise ValueError(f"{label}: field '{key}' must be a string")
    if "text" not in slide:
        raise ValueError(f"{label}: field 'text' is missing")
    log = slide.get("log")
    if log is not None and not isinstance(log, str):
        raise ValueError(f"{label}: field 'log' must be a string")


def _text_lines(slide, preset):
    """[(role, text)] with preset role keys expanded; validates quotes and emptiness."""
    n = slide.get("n")
    text = slide.get("text")
    if not isinstance(text, (list, tuple)) and text:
        raise ValueError(f"slide {n}: field 'text' must be a list of [role, text]")
    if not text:
        raise ValueError(f"slide {n}: field 'text' is empty")
    roles = preset.get("roles", {})
    out = []
    for item in text:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise ValueError(f"slide {n}: field 'text' entries must be [role, text]")
        role, value = item
        if not isinstance(role, str):
            raise ValueError(f"slide {n}: field 'text' role must be a string, got {role!r}")
        if not isinstance(value, str):
            raise ValueError(f'slide {n}, role "{role}": field \'text\' value must be a string, got {value!r}')
        role = roles.get(role, role)
        if '"' in value:
            raise ValueError(f'slide {n}, role "{role}": text contains a straight double quote')
        if "\n" in value or "\r" in value:
            raise ValueError(f'slide {n}, role "{role}": text contains a newline')
        out.append((role, value))
    return out


def render_prompt(slide, preset, ctx):
    """One prompt string in the fixed block order. ctx keys: seller, language, audience."""
    def fill(s):
        for key in ("language", "audience"):
            if "{" + key + "}" in s and not str(ctx.get(key) or "").strip():
                raise ValueError(f"slide {slide.get('n')}: preset uses {{{key}}} but {key} is empty or missing")
        return (s.replace("{seller}", ctx["seller"]).replace("{language}", ctx["language"])
                .replace("{audience}", ctx["audience"]))

    if "{ai}" not in preset["guard"]:
        raise ValueError("preset guard has no {ai} placeholder: the AI clause could never apply")
    guard = preset["guard"].replace("{ai}", preset["ai_clause"] if slide.get("ai") else "")
    if slide.get("people"):
        if preset["people_clause_from"] not in guard:
            raise ValueError(f"slide {slide.get('n')}: people is set but people_clause_from is not in the preset guard")
        guard = guard.replace(preset["people_clause_from"], preset["people_clause_to"])
    style = fill(preset["style"])
    if slide.get("extra"):
        style += " " + slide["extra"]
    lines = "\n".join(f'- {role}: "{value}"' for role, value in _text_lines(slide, preset))
    blocks = [
        fill(preset["intro"]),
        f"LAYOUT: {slide['layout']}",
        f"VISUAL: {slide['visual']}",
        style,
        f"{preset['text_header']}\n{lines}",
        fill(guard),
    ]
    prompt = "\n\n".join(blocks)
    left = re.search(r"\{[a-z_]+\}", prompt)
    if left:
        raise ValueError(f"slide {slide.get('n')}: unfilled placeholder {left.group(0)} in the prompt")
    return prompt + f"\n\n{LOG_HEADING}"


def _check_spec(slides, preset):
    seen = {}
    footers = {}
    for i, s in enumerate(slides):
        _check_slide(s, i)
        n = s["n"]
        if n in seen:
            raise ValueError(f"slide {n}: duplicate n (entries {seen[n] + 1} and {i + 1})")
        seen[n] = i
        for role, value in _text_lines(s, preset):
            if "footer" in role.lower() or "band" in role.lower():
                if value in footers and footers[value] != n:
                    raise ValueError(
                        f'slide {footers[value]} and slide {n}: same footer/band text "{value}"')
                footers.setdefault(value, n)


def _style_ref_paths(style_refs, house_path):
    out = []
    for r in style_refs:
        p = Path(r)
        if not p.is_absolute():
            if house_path is None:
                raise ValueError(f"style_refs entry {r!r} is relative: it resolves against the house "
                                 "standard file, so pass house_path (CLI: --house)")
            p = Path(house_path).resolve().parent / p
        out.append(p)
    return out


def _refs(slide, style_refs, spec_dir, ref_dir):
    paths = list(style_refs) + [spec_dir / Path(ref_dir) / r for r in slide.get("refs", [])]
    out = []
    for p in paths:
        if not p.is_file():
            raise ValueError(f"slide {slide['n']}: field 'refs': file not found: {p}")
        out.append(str(p.resolve()))
    return out


def _with_log(body, old_text, log):
    """``body`` (ends with the REVISION LOG heading) + carried-over log lines + one new dated line."""
    lines = _log_lines(old_text) if old_text else []
    if log and log.strip():
        new = f"- {datetime.date.today().isoformat()} {log.strip()}"
        if new not in lines:
            lines.append(new)
    return body + "\n" + "".join(ln + "\n" for ln in lines)


def build(spec_path, house=None, preset=None, out_dir=None, only=None, house_path=None):
    """Write prompt files and manifest; returns the number of prompt files written.

    Relative house ``style_refs`` resolve against the directory of ``house_path``."""
    spec_path = Path(spec_path).resolve()
    spec_dir = spec_path.parent
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    slides = spec.get("slides")
    if not slides:
        raise ValueError(f"spec {spec_path} has no slides")
    if not house or not house.get("seller"):
        raise ValueError(NO_SELLER)
    name = preset or house.get("preset")
    if not name:
        raise ValueError("no preset: pass --preset or set 'preset' in the house standard")
    pre = house_mod.load_preset(name)
    ctx = {"seller": house["seller"], "language": house.get("language", house_mod.DEFAULT_LANGUAGE),
           "audience": spec.get("audience", "")}
    _check_spec(slides, pre)
    if only:
        missing = [n for n in only if n not in {s["n"] for s in slides}]
        if missing:
            raise ValueError(f"--only: no such slide n: {', '.join(str(n) for n in missing)}")

    out = Path(out_dir).resolve() if out_dir else spec_dir / "prompts"
    style_refs = _style_ref_paths(house.get("style_refs", []), house_path)
    ref_dir = spec.get("ref_dir", "")
    manifest, rendered = [], {}
    for s in slides:
        f = out / f"slide-{s['n']:02d}.md"
        old = f.read_text(encoding="utf-8") if f.is_file() else None
        entry = {"n": s["n"], "sid": s.get("sid", ""), "prompt_file": f.name,
                 "refs": _refs(s, style_refs, spec_dir, ref_dir)}
        if not only or s["n"] in only:
            body = render_prompt(s, pre, ctx)
            rendered[s["n"]] = _with_log(body, old, s.get("log"))
            entry["sha"] = prompt_sha(body)
        elif old is not None:
            entry["sha"] = prompt_sha(old)
        manifest.append(entry)
    out.mkdir(parents=True, exist_ok=True)
    for n, text in rendered.items():
        (out / f"slide-{n:02d}.md").write_text(text, encoding="utf-8")
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    return len(rendered)
