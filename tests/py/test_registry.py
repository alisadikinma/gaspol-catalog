"""Registry rules for docs/tool-routing.md against tools/deckkit/*.py."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROUTING = ROOT / "docs" / "tool-routing.md"
KIT = ROOT / "tools" / "deckkit"
MAIN = KIT / "__main__.py"
EXEMPT = {"__init__", "__main__", "fonts", "house"}


def rows():
    """Parsed routing rows as (want, use, module) triples."""
    if not ROUTING.is_file():
        raise AssertionError(f"routing file missing: {ROUTING}")
    out = []
    for line in ROUTING.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells[0] in ("I want to...", "") or set(cells[0]) <= {"-"}:
            continue
        out.append((cells[0], cells[1] if len(cells) > 1 else "",
                    cells[2] if len(cells) > 2 else ""))
    return out


def modules_in_cell(cell):
    return [m.strip().strip("`") for m in cell.split(",") if m.strip()]


class RegistryTest(unittest.TestCase):
    def test_every_module_has_a_row(self):
        listed = {m for _, _, cell in rows() for m in modules_in_cell(cell)}
        present = {p.stem for p in KIT.glob("*.py")} - EXEMPT
        missing = sorted(present - listed)
        self.assertFalse(missing, f"modules with no routing row: {missing}")

    def test_every_row_names_an_existing_module(self):
        bad = []
        for want, _, cell in rows():
            names = modules_in_cell(cell)
            if not names:
                bad.append(f"{want!r}: empty Module cell")
            bad += [f"{want!r}: no such module {m!r}" for m in names
                    if not (KIT / f"{m}.py").is_file()]
        self.assertFalse(bad, f"bad Module cells: {bad}")

    def test_no_duplicate_rows(self):
        seen, dup = set(), []
        for want, _, _ in rows():
            if want in seen:
                dup.append(want)
            seen.add(want)
        self.assertFalse(dup, f"duplicate 'I want to...' text: {dup}")

    def test_every_cli_command_is_registered(self):
        registered = set(re.findall(r'sub\.add_parser\("([^"]+)"', MAIN.read_text(encoding="utf-8")))
        bad = []
        for want, use, _ in rows():
            for cmd in re.findall(r"`deckkit ([a-z][a-z0-9-]*)", use):
                if cmd not in registered:
                    bad.append(f"{want!r}: deckkit {cmd} has no parser")
        self.assertFalse(bad, f"unregistered commands: {bad}")


if __name__ == "__main__":
    unittest.main()
