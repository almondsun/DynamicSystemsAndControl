"""Rev B corrections from the independent power-domain review (third schematic step).

H1  LM4040-N conducts 5-35 uA below breakdown (SNOS633N Fig. 5-4), inside the 0.6-1.1 V
    measurement range. U10 becomes a biased 2.5 V reference (R23 from +5V, C22); the
    divider node is clamped by Schottky D4 to REF_2V5 and D3 to GND.
M2/M3  D5 pulls NTRIP low while ADC_EN is low (NUC_3V3 not good, or +5V power-up), so the
    HCT00 latch is set and an explicit RESET is needed after every brownout or power-up.
    U9 CT to VDD through R24 gives tD = 180/300/420 ms.
L3  R19 22k (TPS3808 pull-up minimum is 10k; 1 % parts can fall below it).
L9  Stale J3 note.
    python3 -I sch_review_fixes.py ..
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sch_analyze import groups, key, sheet_model  # noqa: E402
from sch_revb import connect, instance, label, lib_symbol, wire  # noqa: E402
from sexpr import parse, q, replace_spans  # noqa: E402

NEW = [
    # ref, symbol, value, footprint, x, y, nets, fields
    ("R23", "R_RevB", "2.2k", "Resistor_SMD:R_0603_1608Metric", 289.56, 149.86, {"1": "+5V", "2": "REF_2V5"},
     dict(MPN="0603WAF2201T5E", LCSC="C4190", Manufacturer="UNI-ROYAL",
          Purpose="Biases U10 at (5-2.5)/2.2k ~ 1.1 mA, above IRMIN 65 uA")),
    ("C22", "C_RevB", "100nF", "Capacitor_SMD:C_0603_1608Metric", 289.56, 172.72, {"1": "REF_2V5", "2": "GND"},
     dict(MPN="CC0603KRX7R9BB104", LCSC="C14663", Manufacturer="YAGEO", Purpose="REF_2V5 bypass")),
    ("D4", "BAT54WS", "BAT54WS-7-F", "Buck_RevB:Diodes_SOD323", 231.14, 195.58, {"1": "REF_2V5", "2": "VSENSE_DIV"},
     dict(MPN="BAT54WS-7-F", Manufacturer="Diodes Incorporated", LCSC="C124205",
          Datasheet="https://www.diodes.com/datasheet/download/BAT54WS.pdf",
          Purpose="Clamps VSENSE_DIV to REF_2V5 + VF")),
    ("D5", "BAT54WS", "BAT54WS-7-F", "Buck_RevB:Diodes_SOD323", 231.14, 213.36, {"1": "ADC_EN", "2": "NTRIP"},
     dict(MPN="BAT54WS-7-F", Manufacturer="Diodes Incorporated", LCSC="C124205",
          Datasheet="https://www.diodes.com/datasheet/download/BAT54WS.pdf",
          Purpose="Sets the fault latch while the interface is disabled")),
    ("R24", "R_RevB", "100k", "Resistor_SMD:R_0603_1608Metric", 289.56, 71.12, {"1": "PG_DELAY", "2": "+5V"},
     dict(MPN="0603WAF1003T5E", LCSC="C25803", Manufacturer="UNI-ROYAL",
          Purpose="U9 CT to VDD: reset delay 180-420 ms (SBVS050N 6.6)")),
]
RELABEL_SHEET5 = {("U10", "1"): "REF_2V5"}
NC_TO_LABEL_SHEET5 = {("U9", "4"): "PG_DELAY"}
FIELD_EDITS = {
    "buck_5.kicad_sch": {"R19": {"Value": "22k", "MPN": "0603WAF2202T5E", "LCSC": "C31850",
                                 "Commercial_URL": "https://jlcpcb.com/partdetail/C31850",
                                 "Purpose": "TPS3808 open-drain pull-up (datasheet 10k-1M)"},
                         "U10": {"Purpose": "Biased 2.5 V reference for the D4 clamp; never on the measurement node"}},
    "buck_4.kicad_sch": {"J3": {"Migration_Notes": "Rev B: J3 signals pass through U7/U8; NUC_3V3 powers U8 and "
                                                   "R13/R18/R22 and is supervised by U9. Harness per assembly doc."}},
}


def field_edits(text, root, edits):
    out = []
    for sym in root.children("symbol"):
        ref = str(sym.prop("Reference")[2])
        for field, value in edits.get(ref, {}).items():
            node = sym.prop(field)
            if node is None:
                x, y = sym.at()[:2]
                inst = sym.first("instances")
                out.append((inst.start, inst.start,
                            f'(property {q(field)} {q(value)} (at {x:g} {y:g} 0) (hide yes) '
                            '(effects (font (size 1.27 1.27))))\n    '))
                continue
            seg = text[node.start:node.end]
            new = seg.replace(q(str(node[2])), q(value), 1)
            if new == seg and str(node[2]) != value:
                raise SystemExit(f"{ref}.{field}: token not found")
            out.append((node.start, node.end, new))
    return out


def main() -> None:
    base = Path(sys.argv[1]).resolve()
    sheet5 = base / "buck_5.kicad_sch"
    text = sheet5.read_text(encoding="utf-8")
    if '"R23"' in text:
        raise SystemExit("review fixes already applied")
    root = parse(text)
    _, pins, wires, labels, _, _ = sheet_model(sheet5)
    grp = groups(pins, wires, labels)
    by_pin = {(p[0], p[1]): p for p in pins}
    edits = field_edits(text, root, FIELD_EDITS["buck_5.kicad_sch"])
    for (ref, num), new in RELABEL_SHEET5.items():
        g = next(v for v in grp.values() if by_pin[(ref, num)] in v["pins"])
        node = g["labels"][0][4]
        seg = text[node.start:node.end]
        edits.append((node.start, node.end, seg.replace(q(str(node[1])), q(new), 1)))
    for (ref, num), new in NC_TO_LABEL_SHEET5.items():
        p = by_pin[(ref, num)]
        nc = next(n for n in root.children("no_connect") if key(*n.at()[:2]) == key(p[3], p[4]))
        edits.append((nc.start, nc.end, wire(p[3], p[4], p[3] - 5.08, p[4]) + "\n  " +
                      label(new, p[3] - 5.08, p[4], "left")))
    body = []
    have_libs = {str(s[1]) for s in root.first("lib_symbols").children("symbol")}
    for ref, sym, value, fp, x, y, nets, fields in NEW:
        body.append(instance(ref, sym, value, fp, x, y, fields))
        body += connect(sym, x, y, nets)
        if f"Buck_Redesign:{sym}" not in have_libs:
            libs = root.first("lib_symbols")
            edits.append((libs.end - 1, libs.end - 1, " " + lib_symbol(sym, True)))
            have_libs.add(f"Buck_Redesign:{sym}")
    end = root.end - 1
    edits.append((end, end, "  " + "\n  ".join(body) + "\n"))
    sheet5.write_text(replace_spans(text, edits), encoding="utf-8")
    sheet4 = base / "buck_4.kicad_sch"
    t4 = sheet4.read_text(encoding="utf-8")
    sheet4.write_text(replace_spans(t4, field_edits(t4, parse(t4), FIELD_EDITS["buck_4.kicad_sch"])),
                      encoding="utf-8")
    print("review fixes applied:", ", ".join(r[0] for r in NEW))


if __name__ == "__main__":
    main()
