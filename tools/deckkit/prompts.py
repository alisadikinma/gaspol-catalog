"""Slide spec (slides.json) + style preset + house standard -> prompts/slide-NN.md + manifest.json."""
import json
import os
from pathlib import Path

from . import house as house_mod

NO_SELLER = "no seller: pass --house or set GASPOL_CATALOG_HOUSE"


def _text_lines(slide, preset):
    """[(role, text)] with preset role keys expanded; validates quotes and emptiness."""
    n = slide.get("n")
    text = slide.get("text")
    if not text:
        raise ValueError(f"slide {n}: field 'text' is empty")
    roles = preset.get("roles", {})
    out = []
    for item in text:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise ValueError(f"slide {n}: field 'text' entries must be [role, text]")
        role, value = item
        role = roles.get(role, role)
        if '"' in value:
            raise ValueError(f'slide {n}, role "{role}": text contains a straight double quote')
        out.append((role, value))
    return out


def render_prompt(slide, preset, ctx):
    """One prompt string in the fixed block order. ctx keys: seller, language, audience."""
    def fill(s):
        return (s.replace("{seller}", ctx["seller"]).replace("{language}", ctx["language"])
                .replace("{audience}", ctx["audience"]))

    guard = preset["guard"].replace("{ai}", preset["ai_clause"] if slide.get("ai") else "")
    if slide.get("people"):
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
    return "\n\n".join(blocks)


def _check_spec(slides, preset):
    seen = {}
    footers = {}
    for i, s in enumerate(slides):
        n = s.get("n")
        if n in seen:
            raise ValueError(f"slide {n}: duplicate n (entries {seen[n] + 1} and {i + 1})")
        seen[n] = i
        for role, value in _text_lines(s, preset):
            if "footer" in role.lower() or "band" in role.lower():
                if value in footers and footers[value] != n:
                    raise ValueError(
                        f'slide {footers[value]} and slide {n}: same footer/band text "{value}"')
                footers.setdefault(value, n)


def _refs(slide, style_refs, spec_dir, ref_dir):
    paths = [Path(r) for r in style_refs] + [Path(ref_dir) / r for r in slide.get("refs", [])]
    out = []
    for p in paths:
        p = p if p.is_absolute() else spec_dir / p
        if not p.is_file():
            raise ValueError(f"slide {slide['n']}: field 'refs': file not found: {p}")
        out.append(str(p.resolve()))
    return out


def build(spec_path, house=None, preset=None, out_dir=None, only=None):
    """Write prompt files and manifest; returns the number of prompt files written."""
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
    rel = Path(os.path.relpath(out, spec_dir)).as_posix()
    style_refs = house.get("style_refs", [])
    ref_dir = spec.get("ref_dir", "")
    manifest, rendered = [], {}
    for s in slides:
        manifest.append({"n": s["n"], "sid": s.get("sid", ""),
                         "prompt_file": f"{rel}/slide-{s['n']:02d}.md",
                         "refs": _refs(s, style_refs, spec_dir, ref_dir)})
        if not only or s["n"] in only:
            rendered[s["n"]] = render_prompt(s, pre, ctx)
    out.mkdir(parents=True, exist_ok=True)
    for n, text in rendered.items():
        (out / f"slide-{n:02d}.md").write_text(text + "\n", encoding="utf-8")
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    return len(rendered)
