"""Read-only connectivity view of one KiCad schematic sheet.

Lists, for every label, the symbol pins reached through wires and junctions,
plus each pin's absolute position. Used to plan surgical Rev B edits.

    python3 -I sch_analyze.py ../buck_2.kicad_sch [--pins R4,U3]
"""
import argparse
import math
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sexpr import parse  # noqa: E402

GRID = 1e-3


def key(x: float, y: float) -> tuple[int, int]:
    return (round(x / GRID), round(y / GRID))


def lib_pins(lib_symbol, unit: int) -> list[tuple[str, str, float, float]]:
    pins = []
    for sub in lib_symbol.children("symbol"):
        parts = str(sub[1]).rsplit("_", 2)
        sub_unit = int(parts[-2]) if len(parts) == 3 and parts[-2].isdigit() else 0
        if sub_unit not in (0, unit):
            continue
        for pin in sub.children("pin"):
            px, py = (float(v) for v in pin.first("at")[1:3])
            pins.append((str(pin.first("number")[1]), str(pin.first("name")[1]), px, py))
    return pins


def transform(px: float, py: float, rot: float, mirror: str | None) -> tuple[float, float]:
    x, y = px, -py
    if mirror == "x":
        y = -y
    elif mirror == "y":
        x = -x
    a = math.radians(rot)
    # KiCad rotates counter-clockwise on screen (Y axis points down).
    return (x * math.cos(a) + y * math.sin(a), -x * math.sin(a) + y * math.cos(a))


def sheet_model(path: Path):
    root = parse(path.read_text(encoding="utf-8"))
    libs = {str(s[1]): s for s in root.first("lib_symbols").children("symbol")}
    pins = []  # (ref, number, name, x, y)
    for sym in root.children("symbol"):
        ref = str(sym.prop("Reference")[2])
        x0, y0, rot = sym.at()
        mirror = sym.first("mirror")[1] if sym.first("mirror") else None
        unit = int(sym.first("unit")[1]) if sym.first("unit") else 1
        for num, name, px, py in lib_pins(libs[str(sym.first("lib_id")[1])], unit):
            dx, dy = transform(px, py, rot, mirror)
            pins.append((ref, num, name, round(x0 + dx, 4), round(y0 + dy, 4)))
    wires = [tuple(float(v) for p in w.first("pts").children("xy") for v in p[1:3])
             for w in root.children("wire")]
    labels = [(str(n[0]), str(n[1]), *n.at()[:2], n)
              for kind in ("global_label", "label", "hierarchical_label")
              for n in root.children(kind)]
    no_connects = [n.at()[:2] for n in root.children("no_connect")]
    junctions = [n.at()[:2] for n in root.children("junction")]
    return root, pins, wires, labels, no_connects, junctions


def groups(pins, wires, labels):
    parent: dict = {}

    def find(a):
        parent.setdefault(a, a)
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        parent[find(a)] = find(b)

    points = {key(p[3], p[4]) for p in pins} | {key(l[2], l[3]) for l in labels}
    for x1, y1, x2, y2 in wires:
        a, b = key(x1, y1), key(x2, y2)
        union(a, b)
        # Points lying on a wire body connect only if they are pin/label anchors.
        for pt in points:
            px, py = pt
            if (min(a[0], b[0]) <= px <= max(a[0], b[0]) and min(a[1], b[1]) <= py <= max(a[1], b[1])
                    and (b[0] - a[0]) * (py - a[1]) == (b[1] - a[1]) * (px - a[0])):
                union(pt, a)
    out = defaultdict(lambda: {"pins": [], "labels": []})
    for p in pins:
        out[find(key(p[3], p[4]))]["pins"].append(p)
    for l in labels:
        out[find(key(l[2], l[3]))]["labels"].append(l)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("sheet", type=Path)
    ap.add_argument("--pins", default="", help="comma separated references to list")
    args = ap.parse_args()
    _, pins, wires, labels, ncs, _ = sheet_model(args.sheet)
    refs = set(filter(None, args.pins.split(",")))
    for grp in groups(pins, wires, labels).values():
        names = sorted({f"{l[0][:1]}:{l[1]}" for l in grp["labels"]})
        members = [f"{p[0]}.{p[1]}({p[2]})@{p[3]},{p[4]}" for p in grp["pins"]]
        if refs and not any(p[0] in refs for p in grp["pins"]):
            continue
        print(" ".join(names) or "<no label>", "->", ", ".join(members))
    nc_keys = {key(*n) for n in ncs}
    for p in pins:
        if key(p[3], p[4]) in nc_keys and (not refs or p[0] in refs):
            print("no_connect:", f"{p[0]}.{p[1]}({p[2]})@{p[3]},{p[4]}")


if __name__ == "__main__":
    main()
