"""Manual check of the machine-local house standard (not discovered by unittest).

Usage: python tests/py/check_local_house.py <start-dir>
Resolves the house standard from <start-dir>, loads it, and checks that the preset
exists and every path-valued key points at a real file or directory.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.deckkit import house  # noqa: E402


def main(argv):
    if len(argv) != 2:
        raise SystemExit("usage: check_local_house.py <start-dir>")
    found = house.resolve(start=argv[1])
    assert found is not None, "no house standard resolved"
    data = house.load(found)
    assert data["preset"] == "isometrik-terang", f"preset is {data['preset']!r}"
    paths = [("logo", data.get("logo")), ("wordmark", data.get("wordmark")),
             ("image_client", data.get("image_client"))]
    paths += [(f"style_refs[{i}]", p) for i, p in enumerate(data.get("style_refs", []))]
    for key, value in paths:
        if value is None:
            continue
        assert Path(value).exists(), f"{key} does not exist: {value}"
    assert house.load_preset(data["preset"]), "preset did not load"
    print(f"OK {found}")


if __name__ == "__main__":
    main(sys.argv)
