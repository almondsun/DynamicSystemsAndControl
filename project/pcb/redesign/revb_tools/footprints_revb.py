"""Write the Rev B footprint library from manufacturer land patterns only.

Every pad dimension below is copied from the cited drawing; courtyards add the
IPC-7351 nominal 0.25 mm excess around the larger of body or pads (0.5 mm for
the 37 g Murata inductor). Nothing here is estimated from photos or generic
families.

    python3 -I footprints_revb.py ../libraries/footprints/Buck_RevB.pretty
"""
import math
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path

NAMESPACE = uuid.UUID("1b6d2c1e-5f0a-4f55-9a43-9b0d6a2f7e01")


@dataclass(frozen=True)
class Pad:
    number: str
    x: float
    y: float
    w: float
    h: float
    kind: str = "smd"          # smd | thru_hole
    shape: str = "roundrect"   # roundrect | rect | circle | oval
    drill: float = 0.0


@dataclass(frozen=True)
class Footprint:
    name: str
    descr: str
    source: str
    pads: tuple
    body: tuple                 # (xmin, ymin, xmax, ymax) maximum body incl. leads
    courtyard_margin: float
    pin1_mark: tuple            # (x, y) silk dot
    attr: str = "smd"
    model: str = ""
    height: float = 0.0
    silk_lines: tuple = ()      # ((x0, y0, x1, y1), ...) extra orientation marks


def uid(*parts: str) -> str:
    return str(uuid.uuid5(NAMESPACE, "/".join(parts)))


def fmt(v: float) -> str:
    return f"{v:.4f}".rstrip("0").rstrip(".") if v != 0 else "0"


def courtyard(fp: Footprint) -> tuple:
    xs = [fp.body[0], fp.body[2]] + [p.x - p.w / 2 for p in fp.pads] + [p.x + p.w / 2 for p in fp.pads]
    ys = [fp.body[1], fp.body[3]] + [p.y - p.h / 2 for p in fp.pads] + [p.y + p.h / 2 for p in fp.pads]
    m = fp.courtyard_margin

    def out(v, sign):
        # Round outward to 0.05 mm, as KiCad library convention.
        return round((math.floor if sign < 0 else math.ceil)(round((v + sign * m) / 0.05, 6)) * 0.05, 3)
    return (out(min(xs), -1), out(min(ys), -1), out(max(xs), 1), out(max(ys), 1))


def line(layer: str, seg: tuple, width: float, key: str, name: str) -> str:
    x0, y0, x1, y1 = seg
    return (f'\t(fp_line\n\t\t(start {fmt(x0)} {fmt(y0)})\n\t\t(end {fmt(x1)} {fmt(y1)})\n'
            f'\t\t(stroke\n\t\t\t(width {fmt(width)})\n\t\t\t(type solid)\n\t\t)\n'
            f'\t\t(layer "{layer}")\n\t\t(uuid "{uid(name, key)}")\n\t)\n')


def rect(layer: str, box: tuple, width: float, key: str, name: str) -> str:
    x0, y0, x1, y1 = box
    return (f'\t(fp_rect\n\t\t(start {fmt(x0)} {fmt(y0)})\n\t\t(end {fmt(x1)} {fmt(y1)})\n'
            f'\t\t(stroke\n\t\t\t(width {fmt(width)})\n\t\t\t(type solid)\n\t\t)\n\t\t(fill no)\n'
            f'\t\t(layer "{layer}")\n\t\t(uuid "{uid(name, key)}")\n\t)\n')


def pad_text(fp: Footprint, p: Pad) -> str:
    layers = '"F.Cu" "F.Mask" "F.Paste"' if p.kind == "smd" else '"*.Cu" "*.Mask"'
    drill = f"\t\t(drill {fmt(p.drill)})\n" if p.kind == "thru_hole" else ""
    rr = "\t\t(roundrect_rratio 0.25)\n" if p.shape == "roundrect" else ""
    return (f'\t(pad "{p.number}" {p.kind} {p.shape}\n\t\t(at {fmt(p.x)} {fmt(p.y)})\n'
            f'\t\t(size {fmt(p.w)} {fmt(p.h)})\n{drill}\t\t(layers {layers})\n{rr}'
            f'\t\t(uuid "{uid(fp.name, "pad", p.number, fmt(p.x), fmt(p.y))}")\n\t)\n')


def text(fp: Footprint, kind: str, value: str, y: float, layer: str, hide: bool = False) -> str:
    hidden = "\t\t(hide yes)\n" if hide else ""
    return (f'\t(property "{kind}" "{value}"\n\t\t(at 0 {fmt(y)} 0)\n\t\t(layer "{layer}")\n{hidden}'
            f'\t\t(uuid "{uid(fp.name, kind)}")\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1 1)\n'
            f'\t\t\t\t(thickness 0.15)\n\t\t\t)\n\t\t)\n\t)\n')


def render(fp: Footprint) -> str:
    crt = courtyard(fp)
    out = [f'(footprint "{fp.name}"\n\t(version 20260206)\n\t(generator "revb_tools")\n'
           f'\t(generator_version "10.0")\n\t(layer "F.Cu")\n'
           f'\t(descr "{fp.descr} Source: {fp.source}")\n\t(tags "RevB manufacturer land")\n']
    out.append(text(fp, "Reference", "REF**", crt[1] - 1.0, "F.SilkS"))
    out.append(text(fp, "Value", fp.name, crt[3] + 1.0, "F.Fab"))
    out.append(text(fp, "Datasheet", "", 0, "F.Fab", hide=True))
    out.append(text(fp, "Description", fp.descr, 0, "F.Fab", hide=True))
    out.append(f'\t(attr {fp.attr})\n')
    out.append(rect("F.CrtYd", crt, 0.05, "crt", fp.name))
    out.append(rect("F.Fab", fp.body, 0.1, "fab", fp.name))
    # Silk: body outline clipped away from pads is unnecessary for review; use a pin-1 dot.
    px, py = fp.pin1_mark
    out.append(f'\t(fp_circle\n\t\t(center {fmt(px)} {fmt(py)})\n\t\t(end {fmt(px + 0.15)} {fmt(py)})\n'
               f'\t\t(stroke\n\t\t\t(width 0.3)\n\t\t\t(type solid)\n\t\t)\n\t\t(fill yes)\n'
               f'\t\t(layer "F.SilkS")\n\t\t(uuid "{uid(fp.name, "pin1")}")\n\t)\n')
    for i, seg in enumerate(fp.silk_lines):
        out.append(line("F.SilkS", seg, 0.15, f"silk{i}", fp.name))
        out.append(line("F.Fab", seg, 0.1, f"fab{i}", fp.name))
    for p in fp.pads:
        out.append(pad_text(fp, p))
    if fp.model:
        out.append(f'\t(model "{fp.model}"\n\t\t(offset\n\t\t\t(xyz 0 0 0)\n\t\t)\n'
                   f'\t\t(scale\n\t\t\t(xyz 1 1 1)\n\t\t)\n\t\t(rotate\n\t\t\t(xyz 0 0 0)\n\t\t)\n\t)\n')
    out.append('\t(embedded_fonts no)\n)\n')
    return "".join(out)


def dual_row(n_per_side: int, pitch: float, x: float, w: float, h: float) -> tuple:
    """Pins 1..n down the left column, n+1..2n up the right column (TI numbering)."""
    y0 = -(n_per_side - 1) * pitch / 2
    left = [Pad(str(i + 1), -x, y0 + i * pitch, w, h) for i in range(n_per_side)]
    right = [Pad(str(2 * n_per_side - i), x, y0 + i * pitch, w, h) for i in range(n_per_side)]
    return tuple(left + right)


FOOTPRINTS = (
    Footprint(
        "L_Murata_6000B_27.0x23.5mm",
        "Murata Power Solutions 6000B SMD power inductor (60B334C). Pads 3 x 14 mm at 20.8 mm centres; "
        "body 23.5 max across terminals x 27.0 max, 20.0 max height, 37 g.",
        "Murata KMP_6000B_B01 p.1 Mechanical Dimensions and Recommended Pad Layout",
        (Pad("1", -10.4, 0, 3.0, 14.0, shape="rect"), Pad("2", 10.4, 0, 3.0, 14.0, shape="rect")),
        (-11.75, -13.5, 11.75, 13.5), 0.5, (-10.4, -8.3), height=20.0),
    Footprint(
        "TI_PW0014A_TSSOP-14",
        "TI PW0014A TSSOP-14, 0.65 mm pitch. Land 14x 1.5 x 0.45 mm, rows 5.8 mm apart (centre).",
        "TI PW0014A Example Board Layout (SCLS749C p.22; SCDS390B p.43)",
        dual_row(7, 0.65, 2.9, 1.5, 0.45),
        (-3.3, -2.55, 3.3, 2.55), 0.25, (-3.9, -2.6)),
    Footprint(
        "TI_DBV0006A_SOT-23-6",
        "TI DBV0006A SOT-23-6. Land 6x 1.1 x 0.6 mm, pitch 0.95 mm, rows 2.6 mm apart (centre).",
        "TI DBV0006A Example Board Layout (SBVS050N p.37)",
        dual_row(3, 0.95, 1.3, 1.1, 0.6),
        (-1.5, -1.525, 1.5, 1.525), 0.25, (-2.2, -1.5)),
    Footprint(
        "TI_DBZ0003A_SOT-23-3",
        "TI DBZ0003A SOT-23-3. Land 3x 1.3 x 0.6 mm; pins 1/2 at x=-1.05, pin 3 at x=+1.05, pitch 1.9 mm.",
        "TI DBZ0003A Example Board Layout (SNOS633N p.78)",
        (Pad("1", -1.05, -0.95, 1.3, 0.6), Pad("2", -1.05, 0.95, 1.3, 0.6), Pad("3", 1.05, 0, 1.3, 0.6)),
        (-1.32, -1.52, 1.32, 1.52), 0.25, (-2.1, -1.5)),
    Footprint(
        "Diodes_SOD323",
        "Diodes Inc. SOD323 (BAT54WS). Land 0.59 x 0.45 mm, outer extent 2.70 mm. Pad 1 = cathode (band).",
        "Diodes DS30098 Rev.14-2 p.4 Suggested Pad Layout",
        (Pad("1", -1.055, 0, 0.59, 0.45), Pad("2", 1.055, 0, 0.59, 0.45)),
        (-1.35, -0.7, 1.35, 0.7), 0.25, (-1.75, 0)),
    Footprint(
        "TerminalBlock_SameSky_TB002-500-02_1x02_P5.00mm",
        "Same Sky TB002-500-02BE, 2 poles, 5.00 mm. Holes 1.30 mm for 1.00 mm round pins; body 10.00 x 7.60 mm, "
        "pin row 4.10 mm from rear and 3.50 mm from the wire-entry face (+Y); 0.50 mm interlock tab at pin 1 end.",
        "Same Sky TB002-500 datasheet rev 1.04 (2024-09-12) p.2 Mechanical Drawing / PCB Layout",
        (Pad("1", 0, 0, 2.6, 2.6, "thru_hole", "rect", 1.3), Pad("2", 5.0, 0, 2.6, 2.6, "thru_hole", "circle", 1.3)),
        (-3.0, -4.1, 7.5, 3.5), 0.5, (-3.6, 0), attr="through_hole",
        # Wire-entry side marked with arrows pointing out of the board edge.
        silk_lines=((-2.4, 3.75, 6.9, 3.75),)),
    Footprint(
        "Wurth_WR-BHD_61201021621_2x05_P2.54mm_Vertical",
        "Wurth WR-BHD male box header 61201021621, 10 pins. Holes 1.1 mm (pin 0.64 mm square), pitch 2.54 mm; "
        "body 20.36 x 8.75 mm (9.0 with ribs). Odd row (pin 1) on the key-slot wall (+Y); key slot 4.5 mm centred.",
        "Wurth Elektronik 61201021621 datasheet rev 002.001 (2026-08-30) p.1 Dimensions / Recommended Hole Pattern",
        tuple(Pad(str(2 * i + 1), 2.54 * i, 0, 1.8, 1.8, "thru_hole", "rect" if i == 0 else "circle", 1.1)
              for i in range(5)) +
        tuple(Pad(str(2 * i + 2), 2.54 * i, -2.54, 1.8, 1.8, "thru_hole", "circle", 1.1) for i in range(5)),
        (5.08 - 10.18, -1.27 - 4.5, 5.08 + 10.18, -1.27 + 4.5), 0.5, (-1.6, 1.4), attr="through_hole",
        # Key slot drawn on the odd-row wall.
        silk_lines=((5.08 - 2.25, 3.23, 5.08 - 2.25, 2.4), (5.08 - 2.25, 2.4, 5.08 + 2.25, 2.4),
                    (5.08 + 2.25, 2.4, 5.08 + 2.25, 3.23))),
    Footprint(
        "TO-220-3_Vertical_Drill1.4",
        "TO-220-3 vertical for Infineon IRFZ44NPbF (PG-TO220-3-U05). Lead b<=1.01 x c<=0.61 mm (diagonal 1.18 mm); "
        "hole 1.4 mm per IPC-2222 (max lead diagonal + 0.2 mm). Pin 1 G, 2 D (tab), 3 S. Body E<=10.67, A<=4.83 mm.",
        "Infineon IRFZ44NPbF datasheet rev 2.1 (2026-08-11) p.1 pinout, p.8 PG-TO220-3-U05 outline",
        (Pad("1", 0, 0, 1.905, 2.6, "thru_hole", "rect", 1.4), Pad("2", 2.54, 0, 1.905, 2.6, "thru_hole", "oval", 1.4),
         Pad("3", 5.08, 0, 1.905, 2.6, "thru_hole", "oval", 1.4)),
        (2.54 - 5.335, -3.365, 2.54 + 5.335, 1.465), 0.25, (-1.6, 2.0), attr="through_hole",
        model="${KIPRJMOD}/libraries/3dmodels/standard/Package_TO_SOT_THT.3dshapes/TO-220-3_Vertical.step",
        # Tab (drain) side line.
        silk_lines=((2.54 - 5.335, -3.365 + 1.4, 2.54 + 5.335, -3.365 + 1.4),)),

    Footprint(
        "CP_Panasonic_SVPF_E7_Land",
        "Panasonic OS-CON SVPF size E7 (25SVPF100M), 8.3 x 8.3 mm base. Land a=2.8 gap, b=11.1 outer, c=1.9 wide: "
        "pads 4.15 x 1.9 mm at +-3.475 mm. Pad 1 = + (chamfered base-plate side).",
        "Panasonic AAB8000COL10 (31-Oct-25) Land Pattern table, size E7; AAB8000C177 p.1 dimensions",
        (Pad("1", -3.475, 0, 4.15, 1.9, shape="rect"), Pad("2", 3.475, 0, 4.15, 1.9)),
        (-4.25, -4.25, 4.25, 4.25), 0.25, (-5.9, -1.6),
        silk_lines=((-6.4, -1.6, -5.4, -1.6), (-5.9, -2.1, -5.9, -1.1))),
    Footprint(
        "CP_Panasonic_SVF_C6_Land",
        "Panasonic OS-CON SVF size C6 (50SVF10M), 6.6 x 6.6 mm base. Land a=2.1 gap, b=9.1 outer, c=1.6 wide: "
        "pads 3.5 x 1.6 mm at +-2.80 mm. Pad 1 = + (chamfered base-plate side).",
        "Panasonic AAB8000COL10 (31-Oct-25) Land Pattern table, size C6; AAB8000C211 p.1 dimensions",
        (Pad("1", -2.8, 0, 3.5, 1.6, shape="rect"), Pad("2", 2.8, 0, 3.5, 1.6)),
        (-3.4, -3.4, 3.4, 3.4), 0.25, (-4.8, -1.4),
        silk_lines=((-5.3, -1.4, -4.3, -1.4), (-4.8, -1.9, -4.8, -0.9))),
    Footprint(
        "R_TAI_RLP25_2512_Kelvin",
        "TA-I RLP25 2512 current sense resistor (RLP25FEER050), R > 0.004 ohm land: pads b=2.1 x a=4.0 mm, "
        "gap L=4.1 mm. Take the sense traces from the inner pad edges (Kelvin).",
        "TA-I RLP specification TRLP-250S008F p.3 section 6 Recommended Solder Pad Dimension; p.1 section 3.2",
        (Pad("1", -3.1, 0, 2.1, 4.0, shape="rect"), Pad("2", 3.1, 0, 2.1, 4.0, shape="rect")),
        (-3.3, -1.7, 3.3, 1.7), 0.25, (-4.6, -2.3)),
    Footprint(
        "TI_D0008A_SOIC-8",
        "TI D0008A SOIC-8 (LM393BIDR). Land 8x 1.55 x 0.6 mm, rows 5.4 mm apart (centre), pitch 1.27 mm.",
        "TI LM393B (SLCS005AH) D0008A Example Board Layout p.44",
        dual_row(4, 1.27, 2.7, 1.55, 0.6),
        (-3.1, -2.5, 3.1, 2.5), 0.25, (-3.9, -2.5)),
    Footprint(
        "TI_D0014A_SOIC-14",
        "TI D0014A SOIC-14 (SN74HCT00DR, SN74HCT14DR). Land 14x 1.55 x 0.6 mm, rows 5.4 mm apart, pitch 1.27 mm.",
        "TI SN74HCT00 p.16 / SN74HCT14 p.19 D0014A Example Board Layout",
        dual_row(7, 1.27, 2.7, 1.55, 0.6),
        (-3.1, -4.375, 3.1, 4.375), 0.25, (-3.9, -4.4)),
    Footprint(
        "TI_DBV0005A_SOT-23-5",
        "TI DBV0005A SOT-23-5 (INA180A1IDBVR). Land 5x 1.1 x 0.6 mm, rows 2.6 mm apart, pitch 0.95 mm. "
        "Pins 1-3 left (top to bottom), 4 right bottom, 5 right top.",
        "TI INA180 (SBOS631) DBV0005A Example Board Layout p.48",
        (Pad("1", -1.3, -0.95, 1.1, 0.6), Pad("2", -1.3, 0, 1.1, 0.6), Pad("3", -1.3, 0.95, 1.1, 0.6),
         Pad("4", 1.3, 0.95, 1.1, 0.6), Pad("5", 1.3, -0.95, 1.1, 0.6)),
        (-1.5, -1.525, 1.5, 1.525), 0.25, (-2.2, -1.5)),
)


def main() -> None:
    lib = Path(sys.argv[1])
    lib.mkdir(parents=True, exist_ok=True)
    for fp in FOOTPRINTS:
        (lib / f"{fp.name}.kicad_mod").write_text(render(fp), encoding="utf-8")
        print(fp.name, "courtyard", courtyard(fp))


if __name__ == "__main__":
    main()
