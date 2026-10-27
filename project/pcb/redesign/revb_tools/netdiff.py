"""Compare two KiCad XML netlists terminal by terminal.

    python3 -I netdiff.py before.net.xml after.net.xml
Prints added/removed components, changed fields of interest and every
terminal whose net name changed. Exit status 0; the caller judges the diff.
"""
import sys
import xml.etree.ElementTree as ET

FIELDS = ("value", "footprint")


def load(path: str):
    root = ET.parse(path).getroot()
    comps = {}
    for c in root.find("components"):
        comps[c.get("ref")] = {"value": c.findtext("value"), "footprint": c.findtext("footprint"),
                               "fields": {f.get("name"): f.text for f in c.iter("field")}}
    pins = {}
    for net in root.find("nets"):
        for node in net:
            pins[(node.get("ref"), node.get("pin"))] = net.get("name")
    return comps, pins


def main() -> None:
    (ca, pa), (cb, pb) = load(sys.argv[1]), load(sys.argv[2])
    print("removed components:", sorted(set(ca) - set(cb)))
    print("added components:", sorted(set(cb) - set(ca)))
    for ref in sorted(set(ca) & set(cb)):
        for f in FIELDS:
            if ca[ref][f] != cb[ref][f]:
                print(f"changed {ref}.{f}: {ca[ref][f]!r} -> {cb[ref][f]!r}")
    for key in sorted(set(pa) | set(pb)):
        if key[0] not in ca or key[0] not in cb:
            continue
        if pa.get(key) != pb.get(key):
            print(f"net {key[0]}.{key[1]}: {pa.get(key)} -> {pb.get(key)}")
    added = sorted({k for k in pb if k[0] not in ca})
    for key in added:
        print(f"new pin {key[0]}.{key[1]}: {pb[key]}")


if __name__ == "__main__":
    main()
