"""Apply the Rev B schematic changes to project/pcb/redesign in place.

1. Re-labels the pins whose nets change (PWM/RUN/RESET buffering, ADC path,
   power-good inversion in spare U3 gates).
2. Updates the parts fixed by the plan (L1/L2, Q1, D2, J1/J2, J3).
3. Adds sheet buck_5.kicad_sch "Power-domain interface" with the new parts.

Run once on the Rev A files (a second run is refused).
    python3 -I sch_revb.py ..
"""
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sch_analyze import groups, key, sheet_model  # noqa: E402
from sexpr import parse, q, replace_spans  # noqa: E402

NS = uuid.UUID("5b0b7f0e-2f53-4f0d-8a8e-7d0f9c1e2b10")
ROOT_UUID = "94b2b377-c0d1-5fce-91fa-ae8f86f36484"
SHEET5_UUID = str(uuid.uuid5(NS, "sheet5"))
SHEET5_FILE_UUID = str(uuid.uuid5(NS, "sheet5-file"))
PROJECT = "buck"
APPROVAL = "PENDING - PROTOTYPE BRING-UP; NOT ELECTRICALLY VALIDATED"


def uid(*parts) -> str:
    return str(uuid.uuid5(NS, "/".join(str(p) for p in parts)))


# ---------------------------------------------------------------- net changes
RELABEL = {  # sheet -> {(ref, pin): new global label}
    "buck_2.kicad_sch": {("R4", "2"): "PWM_IN", ("U3", "3"): "NUC_PG", ("U3", "5"): "BUF_OE_N"},
    "buck_3.kicad_sch": {("U4", "1"): "RESET_5V", ("U4", "4"): "RUN_5V"},
    "buck_4.kicad_sch": {("R14", "2"): "VSENSE_DIV", ("R15", "1"): "VSENSE_DIV"},
}
NC_TO_LABEL = {"buck_2.kicad_sch": {("U3", "4"): "BUF_OE_N", ("U3", "6"): "ADC_EN"}}

# ------------------------------------------------------------- part updates
LCSC_URL = "https://jlcpcb.com/partdetail/{}"
PART_UPDATES = {
    "buck_1.kicad_sch": {
        "L1": dict(Value="330uH 60B334C", Footprint="Buck_RevB:L_Murata_6000B_27.0x23.5mm", MPN="60B334C",
                   Manufacturer="Murata Power Solutions", LCSC="C6823957", Assembly="JLC_SMT_TOP_SUPPLY_BLOCKED",
                   Datasheet="https://www.murata.com/products/power/power-magnetics (KMP_6000B_B01)"),
        "L2": dict(Value="330uH 60B334C", Footprint="Buck_RevB:L_Murata_6000B_27.0x23.5mm", MPN="60B334C",
                   Manufacturer="Murata Power Solutions", LCSC="C6823957", Assembly="JLC_SMT_TOP_SUPPLY_BLOCKED",
                   Datasheet="https://www.murata.com/products/power/power-magnetics (KMP_6000B_B01)"),
        "Q1": dict(Value="IRFZ44NPBF", Footprint="Buck_RevB:TO-220-3_Vertical_Drill1.4", MPN="IRFZ44NPBF",
                   Manufacturer="Infineon", LCSC="C2586", Assembly="MANUAL_THT",
                   Datasheet="https://www.infineon.com/assets/row/public/documents/24/49/infineon-irfz44n-datasheet-en.pdf"),
        "J1": dict(Value="12V IN TB002-500-02BE", Footprint="Buck_RevB:TerminalBlock_SameSky_TB002-500-02_1x02_P5.00mm",
                   MPN="TB002-500-02BE", Manufacturer="Same Sky", LCSC="C2757858", Assembly="MANUAL_THT",
                   Datasheet="https://www.sameskydevices.com/product/resource/tb002-500.pdf"),
        "J2": dict(Value="LOAD TB002-500-02BE", Footprint="Buck_RevB:TerminalBlock_SameSky_TB002-500-02_1x02_P5.00mm",
                   MPN="TB002-500-02BE", Manufacturer="Same Sky", LCSC="C2757858", Assembly="MANUAL_THT",
                   Datasheet="https://www.sameskydevices.com/product/resource/tb002-500.pdf"),
    },
    "buck_2.kicad_sch": {
        "D2": dict(Value="UF4004-E3/54", MPN="UF4004-E3/54", Manufacturer="Vishay", LCSC="C5137033",
                   Assembly="MANUAL_THT", Datasheet="https://www.vishay.com/docs/88755/uf4001.pdf"),
    },
    "buck_4.kicad_sch": {
        "J3": dict(Value="NUCLEO IF 61201021621", Footprint="Buck_RevB:Wurth_WR-BHD_61201021621_2x05_P2.54mm_Vertical",
                   MPN="61201021621", Manufacturer="Wurth Elektronik", LCSC="C4355000", Assembly="MANUAL_THT",
                   Datasheet="https://www.we-online.com/components/products/datasheet/61201021621.pdf"),
    },
}
COMMON_UPDATE = dict(Electrical_Approval=APPROVAL, Migration_Status="REV B - PART FIXED BY RELEASE PLAN")


# --------------------------------------------------------- symbol libraries
def font(size=1.27):
    return f"(effects (font (size {size} {size})))"


def prop(name, value, x=0.0, y=0.0, hide=True, size=1.27):
    h = " (hide yes)" if hide else ""
    return f'(property {q(name)} {q(value)} (at {x:g} {y:g} 0){h} {font(size)})'


def pin(etype, num, name, x, y, angle, length=2.54):
    return (f'(pin {etype} line (at {x:g} {y:g} {angle}) (length {length:g}) '
            f'(name {q(name)} {font(1.0)}) (number {q(num)} {font(1.0)}))')


def rect_body(x0, y0, x1, y1):
    return (f"(rectangle (start {x0:g} {y0:g}) (end {x1:g} {y1:g}) "
            "(stroke (width 0.254) (type default)) (fill (type background)))")


def polyline(points, fill="none"):
    pts = " ".join(f"(xy {x:g} {y:g})" for x, y in points)
    return f"(polyline (pts {pts}) (stroke (width 0.254) (type default)) (fill (type {fill})))"


def ic(left, right, half_w=7.62, ref="U"):
    """left/right: [(type, number, name)] from top. Pins 2.54 mm apart."""
    rows = max(len(left), len(right))
    top = (rows - 1) * 1.27
    pins = [pin(t, n, nm, -half_w - 2.54, top - i * 2.54, 0) for i, (t, n, nm) in enumerate(left)]
    pins += [pin(t, n, nm, half_w + 2.54, top - i * 2.54, 180) for i, (t, n, nm) in enumerate(right)]
    body = rect_body(-half_w, top + 2.54, half_w, -top - 2.54)
    return ref, [body], pins, top + 3.81, -top - 3.81


SYMBOLS = {
    "SN74LV4T125PW": ic(
        [("input", "1", "1~{OE}"), ("input", "2", "1A"), ("input", "4", "2~{OE}"), ("input", "5", "2A"),
         ("input", "10", "3~{OE}"), ("input", "9", "3A"), ("input", "13", "4~{OE}"), ("input", "12", "4A")],
        [("tri_state", "3", "1Y"), ("tri_state", "6", "2Y"), ("tri_state", "8", "3Y"), ("tri_state", "11", "4Y"),
         ("power_in", "14", "VCC"), ("power_in", "7", "GND")]),
    "TMUX1511PW": ic(
        [("input", "1", "SEL1"), ("passive", "2", "S1"), ("input", "4", "SEL2"), ("passive", "5", "S2"),
         ("input", "10", "SEL3"), ("passive", "9", "S3"), ("input", "13", "SEL4"), ("passive", "12", "S4")],
        [("passive", "3", "D1"), ("passive", "6", "D2"), ("passive", "8", "D3"), ("passive", "11", "D4"),
         ("power_in", "14", "VDD"), ("power_in", "7", "GND")]),
    "TPS3808G33DBV": ic(
        [("power_in", "6", "VDD"), ("input", "5", "SENSE"), ("input", "3", "~{MR}"), ("passive", "4", "CT")],
        [("open_collector", "1", "~{RESET}"), ("power_in", "2", "GND")]),
    "LM4040AIM3X-2.5": ("U", [polyline([(-1.27, 1.27), (-1.27, -1.27), (1.27, 0), (-1.27, 1.27)]),
                              polyline([(1.27, 1.27), (1.27, -1.27), (0.635, -1.27)])],
                        [pin("passive", "1", "K", 5.08, 0, 180, 3.81), pin("passive", "2", "A", -5.08, 0, 0, 3.81),
                         pin("passive", "3", "A_NC", -5.08, -2.54, 0, 3.81)], 3.81, -4.445),
    "BAT54WS": ("D", [polyline([(-1.27, 1.27), (-1.27, -1.27), (1.27, 0), (-1.27, 1.27)]),
                      polyline([(1.27, 1.27), (1.27, -1.27), (1.905, -1.27)])],
                [pin("passive", "1", "K", 5.08, 0, 180, 3.81), pin("passive", "2", "A", -5.08, 0, 0, 3.81)],
                3.81, -3.81),
    "R_RevB": ("R", [polyline([(-10.16, 0), (-3.81, 0)]), rect_body(-3.81, 1.27, 3.81, -1.27).replace("background", "none"),
                     polyline([(3.81, 0), (10.16, 0)])],
               [pin("passive", "1", "", -12.7, 0, 0), pin("passive", "2", "", 12.7, 0, 180)], 5.54, -5.54),
    "C_RevB": ("C", [polyline([(-10.16, 0), (-1.27, 0)]), polyline([(-1.27, -3.81), (-1.27, 3.81)]),
                     polyline([(1.27, 0), (10.16, 0)]), polyline([(1.27, -3.81), (1.27, 3.81)])],
               [pin("passive", "1", "", -12.7, 0, 0), pin("passive", "2", "", 12.7, 0, 180)], 5.54, -5.54),
}


def lib_symbol(name, qualified):
    ref, graphics, pins, ytop, ybot = SYMBOLS[name]
    full = f"Buck_Redesign:{name}" if qualified else name
    return (f'(symbol {q(full)} (pin_names (offset 0.5)) (exclude_from_sim no) (in_bom yes) (on_board yes) '
            f'{prop("Reference", ref, 0, ytop, False)} {prop("Value", name, 0, ybot, False)} '
            f'{prop("Footprint", "")} {prop("Datasheet", "")} {prop("Description", "")} '
            f'(symbol {q(name + "_0_1")} {" ".join(graphics)}) (symbol {q(name + "_1_1")} {" ".join(pins)}) '
            '(embedded_fonts no))')


def symbol_pins(name):
    """[(number, x, y, side)] in library coordinates (Y up)."""
    out = []
    for p in parse(lib_symbol(name, True)).walk("pin"):
        x, y, angle = (float(v) for v in p.first("at")[1:4])
        out.append((str(p.first("number")[1]), x, y, "left" if angle == 0 else "right"))
    return out


# ------------------------------------------------------------- new sheet 5
NEW_PARTS = [
    # ref, symbol, value, footprint, x, y, {pin: net}, fields
    ("U7", "SN74LV4T125PW", "SN74LV4T125PWR", "Buck_RevB:TI_PW0014A_TSSOP-14", 71.12, 71.12,
     {"1": "BUF_OE_N", "2": "PWM_IN", "4": "BUF_OE_N", "5": "RUN", "10": "BUF_OE_N", "9": "RESET", "13": "+5V",
      "12": "GND", "3": "DPRIME", "6": "RUN_5V", "8": "RESET_5V", "11": None, "14": "+5V", "7": "GND"},
     dict(MPN="SN74LV4T125PWR", Manufacturer="Texas Instruments", LCSC="C90755",
          Datasheet="https://www.ti.com/lit/ds/symlink/sn74lv4t125.pdf")),
    ("U8", "TMUX1511PW", "TMUX1511PWR", "Buck_RevB:TI_PW0014A_TSSOP-14", 71.12, 149.86,
     {"1": "ADC_EN", "2": "VSENSE_PROT", "4": "GND", "5": "GND", "10": "GND", "9": "GND", "13": "GND", "12": "GND",
      "3": "VSENSE", "6": "GND", "8": "GND", "11": "GND", "14": "NUC_3V3", "7": "GND"},
     dict(MPN="TMUX1511PWR", Manufacturer="Texas Instruments", LCSC="C2866750",
          Datasheet="https://www.ti.com/lit/ds/symlink/tmux1511.pdf")),
    ("U9", "TPS3808G33DBV", "TPS3808G33DBVR", "Buck_RevB:TI_DBV0006A_SOT-23-6", 231.14, 71.12,
     {"6": "+5V", "5": "NUC_SENSE", "3": None, "4": None, "1": "NUC_PG", "2": "GND"},
     dict(MPN="TPS3808G33DBVR", Manufacturer="Texas Instruments", LCSC="C43698",
          Datasheet="https://www.ti.com/lit/ds/symlink/tps3808.pdf")),
    ("U10", "LM4040AIM3X-2.5", "LM4040AIM3X-2.5/NOPB", "Buck_RevB:TI_DBZ0003A_SOT-23-3", 231.14, 149.86,
     {"1": "VSENSE_DIV", "2": "GND", "3": "GND"},
     dict(MPN="LM4040AIM3X-2.5/NOPB", Manufacturer="Texas Instruments", LCSC="C111866",
          Datasheet="https://www.ti.com/lit/ds/symlink/lm4040-n.pdf",
          Substitution_Note="Plan named LM4040AIM3-2.5/NOPB (0 stock, not buyable at JLC/LCSC). TI SNOS633N s.11: "
                            "X suffix has the same electrical properties; only reel differs (both marking R2A).")),
    ("D3", "BAT54WS", "BAT54WS-7-F", "Buck_RevB:Diodes_SOD323", 231.14, 175.26,
     {"1": "VSENSE_DIV", "2": "GND"},
     dict(MPN="BAT54WS-7-F", Manufacturer="Diodes Incorporated", LCSC="C124205",
          Datasheet="https://www.diodes.com/datasheet/download/BAT54WS.pdf")),
]
PASSIVES = [
    # ref, R/C, value, footprint, mpn, lcsc, manufacturer, net1, net2, purpose
    ("R16", "R", "10k", "Resistor_SMD:R_0603_1608Metric", "0603WAF1002T5E", "C25804", "UNI-ROYAL", "RUN_5V", "GND",
     "RUN_5V low while U7 is high-impedance"),
    ("R17", "R", "10k", "Resistor_SMD:R_0603_1608Metric", "0603WAF1002T5E", "C25804", "UNI-ROYAL", "RESET_5V", "GND",
     "RESET_5V low while U7 is high-impedance"),
    ("R18", "R", "100k", "Resistor_SMD:R_0603_1608Metric", "0603WAF1003T5E", "C25803", "UNI-ROYAL", "PWM_IN", "NUC_3V3",
     "Default d'=1 (switch off) while PA8 floats; 3.3 V domain only"),
    ("R19", "R", "10k", "Resistor_SMD:R_0603_1608Metric", "0603WAF1002T5E", "C25804", "UNI-ROYAL", "NUC_PG", "+5V",
     "TPS3808 open-drain pull-up"),
    ("R20", "R", "1k 1%", "Resistor_SMD:R_0603_1608Metric", "0603WAF1001T5E", "C21190", "UNI-ROYAL", "VSENSE_DIV",
     "VSENSE_PROT", "Series limit between clamp node and TMUX1511 S1"),
    ("R21", "R", "100k 1%", "Resistor_SMD:R_0603_1608Metric", "0603WAF1003T5E", "C25803", "UNI-ROYAL", "VSENSE", "GND",
     "MCU-side discharge while TMUX1511 is off"),
    ("R22", "R", "10k", "Resistor_SMD:R_0603_1608Metric", "0603WAF1002T5E", "C25804", "UNI-ROYAL", "NUC_3V3", "NUC_SENSE",
     "Limits any SENSE current while U9 is unpowered"),
    ("C18", "C", "100nF", "Capacitor_SMD:C_0603_1608Metric", "CC0603KRX7R9BB104", "C14663", "YAGEO", "+5V", "GND",
     "U7 VCC bypass"),
    ("C19", "C", "100nF", "Capacitor_SMD:C_0603_1608Metric", "CC0603KRX7R9BB104", "C14663", "YAGEO", "NUC_3V3", "GND",
     "U8 VDD bypass"),
    ("C20", "C", "100nF", "Capacitor_SMD:C_0603_1608Metric", "CC0603KRX7R9BB104", "C14663", "YAGEO", "+5V", "GND",
     "U9 VDD bypass"),
    ("C21", "C", "1nF", "Capacitor_SMD:C_0603_1608Metric", "0603CG102J500NT", "C1636", "FH", "NUC_SENSE", "GND",
     "U9 SENSE bypass (TI recommends 1-10 nF)"),
]


def label(net, x, y, side):
    angle, just = (180, "right") if side == "left" else (0, "left")
    return (f'(global_label {q(net)} (shape passive) (at {x:g} {y:g} {angle}) '
            f'(effects (font (size 0.85 0.85)) (justify {just})) (uuid "{uid("label", net, x, y)}") '
            f'(property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at {x:g} {y:g} 0) (hide yes) {font()}))')


def wire(x0, y0, x1, y1):
    return (f'(wire (pts (xy {x0:g} {y0:g}) (xy {x1:g} {y1:g})) (stroke (width 0) (type default)) '
            f'(uuid "{uid("wire", x0, y0, x1, y1)}"))')


def no_connect(x, y):
    return f'(no_connect (at {x:g} {y:g}) (uuid "{uid("nc", x, y)}"))'


def instance(ref, sym, value, footprint, x, y, fields):
    pins_txt = " ".join(f'(pin {q(n)} (uuid "{uid(ref, "pin", n)}"))' for n, *_ in symbol_pins(sym))
    extra = dict(fields)
    extra.setdefault("Assembly", "JLC_SMT_TOP")
    extra.update(Electrical_Approval=APPROVAL, Migration_Status="REV B - NEW POWER-DOMAIN INTERFACE")
    datasheet = extra.pop("Datasheet", "")
    props = [prop("Reference", ref, x, y - 12, False), prop("Value", value, x, y + 12, False, 1.0),
             prop("Footprint", footprint, x, y), prop("Datasheet", datasheet, x, y), prop("Description", "", x, y)]
    props += [prop(k, v, x, y) for k, v in extra.items()]
    if "LCSC" in extra:
        props.append(prop("Commercial_URL", LCSC_URL.format(extra["LCSC"]), x, y))
    return (f'(symbol (lib_id {q("Buck_Redesign:" + sym)}) (at {x:g} {y:g} 0) (unit 1) (body_style 1) '
            f'(exclude_from_sim no) (in_bom yes) (on_board yes) (in_pos_files yes) (dnp no) '
            f'(uuid "{uid(ref, "symbol")}") {" ".join(props)} {pins_txt} '
            f'(instances (project {q(PROJECT)} (path "/{ROOT_UUID}/{SHEET5_UUID}" (reference {q(ref)}) (unit 1)))))')


def connect(sym, x, y, nets):
    items = []
    for num, px, py, side in symbol_pins(sym):
        ax, ay = x + px, y - py
        net = nets[num]
        if net is None:
            items.append(no_connect(ax, ay))
            continue
        lx = ax - 5.08 if side == "left" else ax + 5.08
        items += [wire(ax, ay, lx, ay), label(net, lx, ay, side)]
    return items


def build_sheet5():
    body, used = [], set()
    for ref, sym, value, fp, x, y, nets, fields in NEW_PARTS:
        used.add(sym)
        body.append(instance(ref, sym, value, fp, x, y, fields))
        body += connect(sym, x, y, nets)
    for i, (ref, kind, value, fp, mpn, lcsc, mfr, n1, n2, purpose) in enumerate(PASSIVES):
        sym = f"{kind}_RevB"
        used.add(sym)
        x = 330.2 if i < 6 else 391.16
        y = 40.64 + (i % 6) * 22.86
        body.append(instance(ref, sym, value, fp, x, y, dict(MPN=mpn, LCSC=lcsc, Manufacturer=mfr, Purpose=purpose)))
        body += connect(sym, x, y, {"1": n1, "2": n2})
    libs = " ".join(lib_symbol(s, True) for s in sorted(used))
    note = ("(text \"Rev B power-domain interface. U7 buffers PWM/RUN/RESET from the NUCLEO 3.3 V domain into the "
            "Buck 5 V logic; outputs are high-impedance unless U9 sees NUC_3V3 >= 3.07 V (BUF_OE_N via spare U3 gate). "
            "R3 keeps DPRIME high (switch off), R16/R17 keep RUN_5V/RESET_5V low. U8 connects the clamped ADC "
            "divider only while ADC_EN is high. Not electrically validated.\" (exclude_from_sim no) "
            "(at 20 230 0) (effects (font (size 2 2)) (justify left)) (uuid \"" + uid("note") + "\"))")
    return (f'(kicad_sch (version 20260306) (generator "eeschema") (generator_version "10.0") '
            f'(uuid "{SHEET5_FILE_UUID}") (paper "A3") (title_block (title "Power-domain interface - REV B PROTOTYPE") '
            f'(rev "B") (company "UNAL Manizales - Sistemas Dinamicos y Control")) (lib_symbols {libs}) '
            f'{note} {" ".join(body)} (embedded_fonts no))\n')


def root_sheet_block():
    return (f'(sheet (at 30 155) (size 130 18) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) '
            f'(stroke (width 0.1524) (type solid)) (fill (color 0 0 0 0)) (uuid "{SHEET5_UUID}") '
            f'(property "Sheetname" "Power-domain interface" (at 30 154 0) (show_name no) (do_not_autoplace no) {font()}) '
            f'(property "Sheetfile" "buck_5.kicad_sch" (at 30 175 0) (show_name no) (do_not_autoplace no) {font()}) '
            f'(instances (project {q(PROJECT)} (path "/{ROOT_UUID}" (page "6")))))\n  ')


# ------------------------------------------------------------ edit helpers
def relabel_edits(text, sheet, changes, nc_changes):
    root, pins, wires, labels, ncs, _ = sheet_model(sheet)
    by_pin = {(p[0], p[1]): p for p in pins}
    grp = groups(pins, wires, labels)
    edits, additions = [], []
    for (ref, num), new in changes.items():
        p = by_pin[(ref, num)]
        g = next(v for v in grp.values() if p in v["pins"])
        if len(g["pins"]) != 1 or len(g["labels"]) != 1:
            raise SystemExit(f"{sheet.name}: {ref}.{num} label is shared; refusing blind edit")
        node = g["labels"][0][4]
        old = text[node.start:node.end]
        name_tok = q(str(node[1]))
        edits.append((node.start, node.end, old.replace(name_tok, q(new), 1)))
    for (ref, num), new in nc_changes.items():
        p = by_pin[(ref, num)]
        nc = next(n for n in root.children("no_connect") if key(*n.at()[:2]) == key(p[3], p[4]))
        side = "left" if p[3] < max(q_[3] for q_ in pins if q_[0] == ref) else "right"
        lx = p[3] - 5.08 if side == "left" else p[3] + 5.08
        edits.append((nc.start, nc.end, wire(p[3], p[4], lx, p[4]) + "\n  " + label(new, lx, p[4], side)))
    return edits


def set_props(text, root, updates):
    edits = []
    for sym in root.children("symbol"):
        ref = str(sym.prop("Reference")[2])
        if ref not in updates:
            continue
        wanted = dict(COMMON_UPDATE)
        wanted.update(updates[ref])
        x, y = sym.at()[:2]
        missing = []
        for name, value in wanted.items():
            node = sym.prop(name)
            if node is None:
                missing.append(prop(name, value, x, y))
                continue
            val_tok = node[2]
            seg = text[node.start:node.end]
            new = seg.replace(q(str(val_tok)), q(value), 1)
            if new == seg and str(val_tok) != value:
                raise SystemExit(f"{ref}.{name}: value token not found for replacement")
            edits.append((node.start, node.end, new))
        if missing:
            inst = sym.first("instances")
            edits.append((inst.start, inst.start, " ".join(missing) + "\n    "))
    return edits


def retitle(text, root):
    tb = root.first("title_block")
    edits = []
    for field in ("title", "rev"):
        node = tb.first(field)
        if node is None:
            continue
        old = str(node[1])
        new = "B" if field == "rev" else old.replace("REV A / HOLD FABRICATION", "REV B PROTOTYPE").replace(
            "REVIEW ONLY", "REV B PROTOTYPE")
        edits.append((node.start, node.end, f"({field} {q(new)})"))
    return edits


def main() -> None:
    base = Path(sys.argv[1]).resolve()
    if (base / "buck_5.kicad_sch").exists():
        raise SystemExit("buck_5.kicad_sch already exists: Rev B already applied")
    for name in ("buck.kicad_sch", "buck_1.kicad_sch", "buck_2.kicad_sch", "buck_3.kicad_sch", "buck_4.kicad_sch"):
        path = base / name
        text = path.read_text(encoding="utf-8")
        root = parse(text)
        edits = retitle(text, root)
        if name in RELABEL or name in NC_TO_LABEL:
            edits += relabel_edits(text, path, RELABEL.get(name, {}), NC_TO_LABEL.get(name, {}))
        if name in PART_UPDATES:
            edits += set_props(text, root, PART_UPDATES[name])
        if name == "buck.kicad_sch":
            si = root.first("sheet_instances")
            edits.append((si.start, si.start, root_sheet_block()))
        path.write_text(replace_spans(text, edits), encoding="utf-8")
        print(name, "edits:", len(edits))
    (base / "buck_5.kicad_sch").write_text(build_sheet5(), encoding="utf-8")
    lib = base / "libraries/symbols/Buck_Redesign.kicad_sym"
    text = lib.read_text(encoding="utf-8")
    end = text.rstrip().rfind(")")
    block = "\n  ".join(lib_symbol(s, False) for s in SYMBOLS)
    lib.write_text(text[:end] + "  " + block + "\n" + text[end:], encoding="utf-8")
    print("buck_5.kicad_sch written; library symbols added:", ", ".join(SYMBOLS))


if __name__ == "__main__":
    main()
