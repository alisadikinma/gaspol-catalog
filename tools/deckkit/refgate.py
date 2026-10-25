"""A slide that names a registered real place or object must carry its photo ref.

The registry lives with the decks, never in this library: ``ref/real-refs.json`` in the manifest's
folder or any parent folder (the nearest ones are read first, all are merged)::

    {"entities": [{"names": ["HarbourBay", "Harbour Bay"], "ref": ["harbourbay"]}]}

A slide whose prompt body (revision log excluded) names an entity as a whole word, case-insensitive,
needs at least one of its refs whose file name contains one of ``ref`` (case-insensitive).

Why: a deck slide (2026-10-21) named a real waterfront with no photo of it and came back as a
generic big-city skyline. A rule in prose did not stop it; ``gen`` runs this check first.
Limit: it only knows places that are named in the prompt and registered.
"""
import json
import re
from pathlib import Path

from .prompts import prompt_body

REGISTRY = Path("ref") / "real-refs.json"


class Refused(ValueError):
    """Bad registry or manifest."""


def registry_files(start):
    out, d = [], Path(start).resolve()
    for p in (d, *d.parents):
        f = p / REGISTRY
        if f.is_file():
            out.append(f)
    return out


def load_registry(start):
    ents = []
    for f in registry_files(start):
        try:
            doc = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise Refused(f"{f}: {exc}") from None
        for i, e in enumerate(doc.get("entities", []) if isinstance(doc, dict) else [None]):
            ok = (isinstance(e, dict) and isinstance(e.get("names"), list) and e["names"]
                  and all(isinstance(n, str) and n.strip() for n in e["names"])
                  and isinstance(e.get("ref"), list) and e["ref"]
                  and all(isinstance(r, str) and r.strip() for r in e["ref"]))
            if not ok:
                raise Refused(f'{f}: entities[{i}] needs "names" and "ref", both non-empty lists of text')
            ents.append({"names": e["names"], "ref": [r.lower() for r in e["ref"]], "source": str(f)})
    return ents


# Quoted strings are lettering the model prints ("PROBLEM · WHY SPI AND AOI MACHINES ..."), not a
# depiction of the place or object, so they are cut out before matching.
_QUOTED = re.compile(r'"[^"\n]*"|“[^”\n]*”')


def _named(text, names):
    text = _QUOTED.sub(" ", text)
    for n in names:
        if re.search(r"(?<![A-Za-z0-9])" + re.escape(n) + r"(?![A-Za-z0-9])", text, re.IGNORECASE):
            return n
    return None


def check(manifest_path):
    """[{n, entity, need, source}] for every slide that names an entity without its photo."""
    mp = Path(manifest_path).resolve()
    ents = load_registry(mp.parent)
    if not ents:
        return []
    try:
        items = json.loads(mp.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise Refused(f"{mp}: {exc}") from None
    rows = []
    for it in items:
        pf = it.get("prompt_file")
        text = prompt_body((mp.parent / pf).read_text(encoding="utf-8")) if pf else str(it.get("prompt", ""))
        refs = [Path(r).name.lower() for r in it.get("refs") or []]
        for e in ents:
            hit = _named(text, e["names"])
            if hit and not any(k in r for k in e["ref"] for r in refs):
                rows.append({"n": it.get("n"), "entity": hit, "need": e["ref"], "source": e["source"]})
    return rows


def format_rows(rows):
    return "\n".join(f"{r['n']:02d}  {r['entity']}: no ref whose name contains {' / '.join(r['need'])}"
                     for r in rows)
