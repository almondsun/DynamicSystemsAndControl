"""Replace L1+L2 (2 x Murata 60B334C in series) with a single Murata 60B684C in the L1 position.

L1 becomes 680 uH (same 6000B land), L2 and its labels/wires are deleted and L1 pin 2 joins IP,
so the LMID net disappears. Refuses to run twice.
    python3 -I sch_single_inductor.py ..
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sch_analyze import groups, key, sheet_model  # noqa: E402
from sch_review_fixes import field_edits  # noqa: E402
from sexpr import parse, q, replace_spans  # noqa: E402

L1_FIELDS = {
    "Value": "680uH 60B684C", "MPN": "60B684C", "LCSC": "C6095796", "Assembly": "JLC_SMT_TOP",
    "Commercial_URL": "https://jlcpcb.com/partdetail/C6095796",
    "Supply_Note": "Replaces 2 x 60B334C (no JLC/LCSC stock); JLC stock 17 on 2026-10-27; 680 uH = +3 % vs 660 uH",
    "Migration_Status": "REV B - SINGLE 680uH INDUCTOR",
}


def main() -> None:
    sheet = Path(sys.argv[1]).resolve() / "buck_1.kicad_sch"
    text = sheet.read_text(encoding="utf-8")
    root = parse(text)
    if not any(str(s.prop("Reference")[2]) == "L2" for s in root.children("symbol")):
        raise SystemExit("L2 already removed")
    _, pins, wires, labels, _, _ = sheet_model(sheet)
    grp = groups(pins, wires, labels)
    edits = field_edits(text, root, {"L1": L1_FIELDS})
    by_pin = {(p[0], p[1]): p for p in pins}
    l1_mid = next(g for g in grp.values() if by_pin[("L1", "2")] in g["pins"])
    node = l1_mid["labels"][0][4]
    seg = text[node.start:node.end]
    edits.append((node.start, node.end, seg.replace(q("LMID"), q("IP"), 1)))
    l2_keys = {key(p[3], p[4]) for p in pins if p[0] == "L2"}
    for g in grp.values():
        if any(p[0] == "L2" for p in g["pins"]):
            if any(p[0] != "L2" for p in g["pins"]):
                raise SystemExit("L2 pin shares a wire group with another pin; refusing blind edit")
            for lab in g["labels"]:
                edits.append((lab[4].start, lab[4].end, ""))
    for w in root.children("wire"):
        pts = [key(float(p[1]), float(p[2])) for p in w.first("pts").children("xy")]
        if any(pt in l2_keys for pt in pts):
            edits.append((w.start, w.end, ""))
    l2 = next(s for s in root.children("symbol") if str(s.prop("Reference")[2]) == "L2")
    edits.append((l2.start, l2.end, ""))
    sheet.write_text(replace_spans(text, edits), encoding="utf-8")
    print("L1 -> 60B684C, L2 removed, L1.2 on IP; edits:", len(edits))


if __name__ == "__main__":
    main()
