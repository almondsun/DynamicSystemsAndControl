"""Take the single 60B684C (L1) out of JLC SMT assembly: hand-soldered after delivery.

Murata 6000B peak reflow is 245 C (KMP_6000B_B01 p.1) while JLC Economic PCBA reflows at 255 +/- 5 C,
and the L1 body sits 0.48 mm from the bottom board edge. Only schematic fields change; the PCB keeps
L1's land and paste. Refuses to run twice.
    python3 -I sch_l1_hand_solder.py ..
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sch_review_fixes import field_edits  # noqa: E402
from sexpr import parse, replace_spans  # noqa: E402

L1_FIELDS = {
    "Assembly": "MANUAL_SMD_DNP_AT_JLC",
    "Supply_Note": "Not placed by JLC: 6000B peak reflow 245 C < Economic PCBA 255+/-5 C and body 0.48 mm from "
                   "board edge; buy 60B684C (LCSC C6095796, stock 17 on 2026-10-27) and hand-solder",
    "Migration_Status": "REV B - SINGLE 680uH INDUCTOR, HAND-SOLDERED",
}


def main() -> None:
    sheet = Path(sys.argv[1]).resolve() / "buck_1.kicad_sch"
    text = sheet.read_text(encoding="utf-8")
    root = parse(text)
    l1 = next(s for s in root.children("symbol") if str(s.prop("Reference")[2]) == "L1")
    if str(l1.prop("Assembly")[2]) != "JLC_SMT_TOP":
        raise SystemExit("L1 is not JLC_SMT_TOP; already changed?")
    sheet.write_text(replace_spans(text, field_edits(text, root, {"L1": L1_FIELDS})), encoding="utf-8")
    print("L1 -> MANUAL_SMD_DNP_AT_JLC")


if __name__ == "__main__":
    main()
