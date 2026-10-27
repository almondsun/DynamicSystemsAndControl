"""Rev B land corrections: point existing symbols at manufacturer-land footprints.

Second, separate step after sch_revb.py, driven by the footprint audit
(Panasonic AAB8000COL10, TA-I RLP p.3, TI D0008A/D0014A/DBV0005A).
Idempotent: values already set are left as they are.
    python3 -I sch_lands.py ..
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sch_revb import prop  # noqa: E402
from sexpr import parse, q, replace_spans  # noqa: E402

LAND = "REV B - LAND CORRECTED TO MANUFACTURER DRAWING"
UPDATES = {
    "buck_1.kicad_sch": {
        "C1": {"Footprint": "Buck_RevB:CP_Panasonic_SVPF_E7_Land"},
        "C2": {"Footprint": "Buck_RevB:CP_Panasonic_SVPF_E7_Land"},
        "C4": {"Footprint": "Buck_RevB:CP_Panasonic_SVF_C6_Land", "Value": "10uF 50V 50SVF10M"},
        "C5": {"Footprint": "Buck_RevB:CP_Panasonic_SVF_C6_Land", "Value": "10uF 50V 50SVF10M"},
        "RS1": {"Footprint": "Buck_RevB:R_TAI_RLP25_2512_Kelvin", "Value": "0.050R 1% 2W RLP25FEER050"},
    },
    "buck_2.kicad_sch": {"U3": {"Footprint": "Buck_RevB:TI_D0014A_SOIC-14"}},
    "buck_3.kicad_sch": {
        "U4": {"Footprint": "Buck_RevB:TI_D0014A_SOIC-14"},
        "U5": {"Footprint": "Buck_RevB:TI_D0008A_SOIC-8"},
        "U6": {"Footprint": "Buck_RevB:TI_DBV0005A_SOT-23-5"},
    },
}


def main() -> None:
    base = Path(sys.argv[1]).resolve()
    for name, refs in UPDATES.items():
        path = base / name
        text = path.read_text(encoding="utf-8")
        root = parse(text)
        edits = []
        for sym in root.children("symbol"):
            ref = str(sym.prop("Reference")[2])
            if ref not in refs:
                continue
            wanted = dict(refs[ref], Migration_Status=LAND)
            for field, value in wanted.items():
                node = sym.prop(field)
                if node is None:
                    x, y = sym.at()[:2]
                    inst = sym.first("instances")
                    edits.append((inst.start, inst.start, prop(field, value, x, y) + "\n    "))
                    continue
                seg = text[node.start:node.end]
                new = seg.replace(q(str(node[2])), q(value), 1)
                if new == seg and str(node[2]) != value:
                    raise SystemExit(f"{ref}.{field}: token not found")
                edits.append((node.start, node.end, new))
        path.write_text(replace_spans(text, edits), encoding="utf-8")
        print(name, "edits:", len(edits))


if __name__ == "__main__":
    main()
