"""Generate the JLCPCB production files for Buck Rev C.

Run with KiCad's Python (KiCad must be closed so the board on disk is current):
    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" -I tools/make_jlc_files.py

Writes to project/pcb/revC/production/:
    gerbers/                       Gerber + Excellon drill files (JLC's KiCad settings)
    pcb_revC_gerbers.zip           the zip to upload as "Gerber file"
    pcb_revC_BOM_JLC.csv           BOM for PCB Assembly (Comment, Designator, Footprint, LCSC Part #)
    pcb_revC_CPL_JLC.csv           pick-and-place (Designator, Mid X, Mid Y, Layer, Rotation)

Only footprints with an LCSC field and without the DNP flag go into the BOM/CPL;
everything else (J1-J6, TP1-TP10, C5, DNP C8) is hand-soldered or not fitted.
"""
import csv, os, shutil, subprocess, sys, zipfile
from collections import OrderedDict

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
REVC = os.path.dirname(HERE)
BOARD = os.path.join(REVC, "pcb_revC", "pcb_revC.kicad_pcb")
OUT = os.path.join(REVC, "production")
GERB = os.path.join(OUT, "gerbers")
CLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
# JLC's part models are not always oriented like KiCad's footprints. Rotation added to
# KiCad's value in the CPL, keyed by footprint-name prefix. SOT-23: JLC's 3D preview on
# 2026-11-06 showed the pin-1 dots of Q2-Q7 exactly 180 deg from KiCad's pin 1 (Q1 TO-252,
# D1 SMA and D2 SOD-123 were correct and need no offset).
JLC_ROT_OFFSET = {"SOT-23": 180}
LAYERS = "F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts"


def run(args):
    r = subprocess.run([CLI] + args, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"kicad-cli failed: {' '.join(args)}\n{r.stdout}\n{r.stderr}")


def main():
    if os.path.isdir(GERB):
        shutil.rmtree(GERB)
    os.makedirs(GERB)
    # Gerbers per JLCPCB's KiCad guide: Protel extensions, no X2, no netlist attrs,
    # subtract soldermask from silkscreen. Zones are already filled and checked.
    run(["pcb", "export", "gerbers", "-o", GERB, "--layers", LAYERS,
         "--no-x2", "--no-netlist", "--subtract-soldermask", BOARD])
    # Excellon, mm, decimal, PTH and NPTH merged, alternate oval mode.
    run(["pcb", "export", "drill", "-o", GERB + os.sep, "--format", "excellon",
         "--excellon-units", "mm", "--excellon-zeros-format", "decimal",
         "--excellon-oval-format", "alternate", BOARD])
    zpath = os.path.join(OUT, "pcb_revC_gerbers.zip")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(os.listdir(GERB)):
            z.write(os.path.join(GERB, f), f)

    board = pcbnew.LoadBoard(BOARD)
    parts = []
    for fp in board.GetFootprints():
        lcsc = fp.GetFieldText("LCSC").strip() if fp.HasField("LCSC") else ""
        if not lcsc or fp.IsDNP():
            continue
        parts.append((fp.GetReference(), fp.GetValue(), fp.GetFPID().GetLibItemName().wx_str(), lcsc,
                      "Top" if fp.GetLayer() == pcbnew.F_Cu else "Bottom"))

    def refkey(r):
        p = "".join(c for c in r if not c.isdigit())
        return (p, int("".join(c for c in r if c.isdigit()) or 0))

    groups = OrderedDict()
    for ref, val, fpn, lcsc, _ in sorted(parts, key=lambda x: refkey(x[0])):
        groups.setdefault((val, fpn, lcsc), []).append(ref)
    with open(os.path.join(OUT, "pcb_revC_BOM_JLC.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
        for (val, fpn, lcsc), refs in groups.items():
            w.writerow([val, ",".join(refs), fpn, lcsc])

    # Positions exactly as KiCad writes them for pick-and-place (mm, KiCad pos convention),
    # renamed to JLC's column names and limited to the assembled parts.
    pos_csv = os.path.join(OUT, "_kicad_pos.csv")
    run(["pcb", "export", "pos", "-o", pos_csv, "--format", "csv", "--units", "mm",
         "--side", "both", "--exclude-dnp", BOARD])
    wanted = {p[0] for p in parts}
    fp_of = {p[0]: p[2] for p in parts}
    rows = []
    with open(pos_csv, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["Ref"] in wanted:
                off = next((v for k, v in JLC_ROT_OFFSET.items() if fp_of[r["Ref"]].startswith(k)), 0)
                rot = (float(r["Rot"]) + off) % 360
                rows.append([r["Ref"], f"{float(r['PosX']):.4f}mm", f"{float(r['PosY']):.4f}mm",
                             "Top" if r["Side"].lower() == "top" else "Bottom", f"{rot:.1f}"])
    os.remove(pos_csv)
    missing = wanted - {r[0] for r in rows}
    if missing:
        sys.exit(f"parts missing from the position export: {sorted(missing)}")
    rows.sort(key=lambda r: refkey(r[0]))
    with open(os.path.join(OUT, "pcb_revC_CPL_JLC.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        w.writerows(rows)
    print(f"{len(parts)} assembled parts in {len(groups)} BOM lines; files in {OUT}")


if __name__ == "__main__":
    main()
