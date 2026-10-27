"""Rev B fabrication/assembly export with native kicad-cli and CSV conversion.

    python3 -I export_revb.py <redesign dir> <output dir>
Writes gerbers (+zip), Excellon drills, JLC BOM/CPL for top SMT parts, manual-assembly
list, assembly/schematic PDFs, ERC/DRC JSON and SHA256SUMS. Never uploads anything.
"""
import csv
import hashlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from collections import defaultdict
from pathlib import Path

LAYERS = ["F.Cu", "B.Cu", "F.Mask", "B.Mask", "F.Paste", "B.Paste", "F.Silkscreen", "B.Silkscreen", "Edge.Cuts"]
JLC_ASSEMBLY = {"JLC_SMT_TOP", "JLC_SMT_TOP_SUPPLY_BLOCKED"}
# CPL offsets (Gerber frame, Y up) where the KiCad origin is not the package centre.
# TO-252-2: pad extents -6.14..+4.46 mm along the lead axis -> centre 0.84 mm from the origin.
CENTROID_OFFSET = {"U2": (0.0, -0.84)}


def run(log, *args):
    p = subprocess.run(["kicad-cli", *map(str, args)], capture_output=True, text=True)
    log.append({"command": ["kicad-cli", *map(str, args)], "returncode": p.returncode,
                "stdout": p.stdout[-4000:], "stderr": p.stderr[-4000:]})
    if p.returncode not in (0, 5):  # 5 = ERC/DRC found violations; judged from the JSON
        raise SystemExit(f"kicad-cli failed: {args}\n{p.stderr}")
    return p


def components(netlist):
    root = ET.parse(netlist).getroot()
    out = {}
    for c in root.find("components"):
        fields = {f.get("name"): (f.text or "") for f in c.iter("field")}
        out[c.get("ref")] = {"value": c.findtext("value"), "footprint": c.findtext("footprint"), **fields}
    return out


def positions(pos_csv):
    rows = {}
    with open(pos_csv, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            rows[r["Ref"]] = r
    return rows


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main() -> None:
    base, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    pcb, sch = base / "buck.kicad_pcb", base / "buck.kicad_sch"
    ev, gerb = out / "evidence", out / "gerbers"
    for d in (ev, gerb):
        d.mkdir(parents=True, exist_ok=True)
    log = []
    run(log, "version")
    run(log, "sch", "erc", "--severity-all", "--format", "json", "--output", ev / "erc.json", sch)
    run(log, "sch", "erc", "--severity-all", "--format", "report", "--output", ev / "erc.rpt", sch)
    run(log, "pcb", "drc", "--schematic-parity", "--refill-zones", "--severity-all", "--all-track-errors",
        "--format", "json", "--output", ev / "drc.json", pcb)
    run(log, "pcb", "drc", "--schematic-parity", "--refill-zones", "--severity-all", "--all-track-errors",
        "--format", "report", "--output", ev / "drc.rpt", pcb)
    run(log, "sch", "export", "netlist", "--format", "kicadxml", "--output", ev / "netlist.xml", sch)
    run(log, "sch", "export", "pdf", "--output", out / "schematic_revB.pdf", sch)
    run(log, "pcb", "export", "gerbers", "--check-zones", "--layers", ",".join(LAYERS), "--output", f"{gerb}/", pcb)
    run(log, "pcb", "export", "drill", "--format", "excellon", "--drill-origin", "absolute", "--excellon-units", "mm",
        "--excellon-zeros-format", "decimal", "--excellon-separate-th", "--generate-map", "--map-format", "pdf",
        "--generate-report", "--report-path", ev / "drill-report.txt", "--output", f"{gerb}/", pcb)
    run(log, "pcb", "export", "pos", "--format", "csv", "--units", "mm", "--side", "both",
        "--output", ev / "positions-native.csv", pcb)
    run(log, "pcb", "export", "pos", "--format", "csv", "--units", "mm", "--side", "both", "--smd-only",
        "--output", ev / "positions-smd.csv", pcb)
    run(log, "pcb", "export", "pdf", "--layers", "F.Fab,F.Silkscreen,F.Courtyard,Edge.Cuts", "--mode-single",
        "--include-border-title", "--output", out / "assembly_top_revB.pdf", pcb)
    run(log, "pcb", "export", "svg", "--layers", "F.Cu,F.Silkscreen,F.Mask,Edge.Cuts", "--mode-single",
        "--fit-page-to-board", "--exclude-drawing-sheet", "--output", ev / "front.svg", pcb)
    run(log, "pcb", "export", "svg", "--layers", "B.Cu,B.Silkscreen,Edge.Cuts", "--mode-single",
        "--fit-page-to-board", "--exclude-drawing-sheet", "--mirror", "--output", ev / "back.svg", pcb)

    comps = components(ev / "netlist.xml")
    pos = positions(ev / "positions-native.csv")
    smd = set(positions(ev / "positions-smd.csv"))
    bom, cpl, manual, problems = defaultdict(list), [], [], []
    for ref in sorted(comps, key=lambda r: (r.rstrip("0123456789"), int("".join(c for c in r if c.isdigit()) or 0))):
        c = comps[ref]
        assembly = c.get("Assembly", "")
        if not assembly:
            # Rev A parts carry no Assembly field: SMD footprint with an LCSC code -> top SMT.
            assembly = "JLC_SMT_TOP" if ref in smd and c.get("LCSC") else "MANUAL_THT"
        if ref.startswith("TP"):
            assembly = "BARE_TEST_PAD"
        if assembly in JLC_ASSEMBLY:
            if not c.get("LCSC"):
                problems.append(f"{ref}: JLC assembly without LCSC code")
            if ref not in pos:
                problems.append(f"{ref}: missing from position file")
                continue
            p = pos[ref]
            if p["Side"] != "top":
                problems.append(f"{ref}: not on top side")
            bom[(c.get("LCSC", ""), c["footprint"].split(":")[-1])].append((ref, c["value"], c.get("MPN", "")))
            dx, dy = CENTROID_OFFSET.get(ref, (0.0, 0.0))
            cpl.append({"Designator": ref, "Mid X": f"{float(p['PosX']) + dx:.4f}mm",
                        "Mid Y": f"{float(p['PosY']) + dy:.4f}mm",
                        "Layer": "Top", "Rotation": f"{float(p['Rot']) % 360:.1f}"})
        else:
            manual.append({"Ref": ref, "Value": c["value"], "MPN": c.get("MPN", ""), "Manufacturer":
                           c.get("Manufacturer", ""), "Footprint": c["footprint"], "Assembly": assembly or "UNSPECIFIED",
                           "LCSC_or_supplier": c.get("LCSC", "")})
        if assembly == "JLC_SMT_TOP_SUPPLY_BLOCKED":
            manual.append({"Ref": ref, "Value": c["value"], "MPN": c.get("MPN", ""), "Manufacturer":
                           c.get("Manufacturer", ""), "Footprint": c["footprint"],
                           "Assembly": "FALLBACK_MANUAL_IF_JLC_CANNOT_SOURCE", "LCSC_or_supplier": c.get("LCSC", "")})
    with open(out / "bom_jlcpcb_revB.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #", "MPN"])
        for (lcsc, fp), parts in sorted(bom.items(), key=lambda kv: kv[1][0][0]):
            values = sorted({v for _, v, _ in parts})
            # "UNI-ROYAL 0603WAF1002T5E" and "0603WAF1002T5E" are the same orderable part.
            mpns = sorted({m.split()[-1] for _, _, m in parts if m})
            if len(mpns) > 1:
                problems.append(f"{lcsc}: several MPNs {mpns}")
            w.writerow([values[0], ",".join(r for r, _, _ in parts), fp, lcsc, mpns[0] if mpns else ""])
    with open(out / "cpl_jlcpcb_revB.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, ["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        w.writeheader()
        w.writerows(cpl)
    with open(out / "manual_assembly_revB.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, list(manual[0].keys()))
        w.writeheader()
        w.writerows(manual)

    files = sorted(p for p in gerb.iterdir() if p.suffix.lower() in (".gtl", ".gbl", ".gts", ".gbs", ".gtp", ".gbp",
                                                                     ".gto", ".gbo", ".gm1", ".drl", ".gbrjob"))
    with zipfile.ZipFile(out / "gerbers_revB.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(f, f.name)
    drc = json.loads((ev / "drc.json").read_text())
    erc = json.loads((ev / "erc.json").read_text())
    summary = {
        "drc_errors": sum(v["severity"] == "error" for v in drc["violations"]),
        "drc_warnings": sum(v["severity"] == "warning" for v in drc["violations"]),
        "drc_unconnected": len(drc["unconnected_items"]), "drc_parity": len(drc["schematic_parity"]),
        "erc_errors": sum(v["severity"] == "error" for s in erc["sheets"] for v in s["violations"]),
        "erc_warnings": sum(v["severity"] == "warning" for s in erc["sheets"] for v in s["violations"]),
        "bom_lines": len(bom), "cpl_parts": len(cpl), "manual_rows": len(manual), "gerber_zip_files": len(files),
        "problems": problems, "board_sha256": sha(pcb), "kicad": log[0]["stdout"].strip(),
    }
    (ev / "commands.json").write_text(json.dumps(log, indent=1), encoding="utf-8")
    (ev / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    hashes = [f"{sha(p)}  {p.relative_to(out)}" for p in sorted(out.rglob("*")) if p.is_file()
              and p.name != "SHA256SUMS.txt"]
    (out / "SHA256SUMS.txt").write_text("\n".join(hashes) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
