"""Netlist -> PCB update for Rev B (KiCad 10 pcbnew SWIG, run with python3.14).

KiCad 10 has no CLI "Update PCB from schematic"; this applies the same
operations: footprint swap/add/remove, schematic paths, fields and pad nets.
It also clears all copper routing so the board can be re-laid out.

    python3.14 -I pcb_update.py <redesign dir> <netlist.xml> <src.kicad_pcb> <dst.kicad_pcb>
"""
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pcbnew

sys.path.insert(0, str(Path(__file__).resolve().parent))
from placement import PLACEMENT  # noqa: E402

OFF_BOARD = (230.0, 40.0)


def fp_libs(base: Path) -> dict:
    text = (base / "fp-lib-table").read_text(encoding="utf-8")
    libs = {}
    for name, uri in re.findall(r'\(name "([^"]+)"\)\s*\(type "[^"]+"\)\s*\(uri "([^"]+)"\)', text):
        libs[name] = uri.replace("${KIPRJMOD}", str(base))
    return libs


def read_netlist(path: str):
    root = ET.parse(path).getroot()
    comps = {}
    for c in root.find("components"):
        sp = c.find("sheetpath")
        comps[c.get("ref")] = {
            "value": c.findtext("value"), "footprint": c.findtext("footprint"),
            "path": sp.get("tstamps") + c.findtext("tstamps"), "sheetname": sp.get("names"),
            "sheetfile": next((p.get("value") for p in c.iter("property") if p.get("name") == "Sheetfile"), ""),
            "fields": [(f.get("name"), f.text or "") for f in c.iter("field")],
        }
    pins = {}
    for net in root.find("nets"):
        for node in net:
            pins[(node.get("ref"), node.get("pin"))] = net.get("name")
    return comps, pins


def clear_copper(board) -> None:
    # BOARD.Delete (not Remove): detached SWIG proxies crash the garbage collector.
    for t in list(board.GetTracks()):
        board.Delete(t)
    for z in list(board.Zones()):
        board.Delete(z)
    for d in [d for d in board.GetDrawings() if d.GetLayerName() in ("F.Cu", "B.Cu", "F.Silkscreen", "B.Silkscreen")]:
        board.Delete(d)


def net_item(board, name: str):
    item = board.FindNet(name)
    if item is None:
        item = pcbnew.NETINFO_ITEM(board, name)
        board.Add(item)
    return item


def apply(base: Path, netlist: str, src: str, dst: str) -> None:
    libs = fp_libs(base)
    comps, pins = read_netlist(netlist)
    board = pcbnew.LoadBoard(src)
    clear_copper(board)
    existing = {f.GetReference(): f for f in board.GetFootprints()}
    for ref in set(existing) - set(comps):
        board.Delete(existing.pop(ref))
    missing = [r for r in comps if r not in PLACEMENT]
    if missing:
        print("WARNING: no placement for", ", ".join(sorted(missing)))
    for ref, c in sorted(comps.items()):
        fp = existing.get(ref)
        if fp is None or fp.GetFPIDAsString() != c["footprint"]:
            lib, name = c["footprint"].split(":", 1)
            new = pcbnew.FootprintLoad(libs[lib], name)
            if new is None:
                raise SystemExit(f"{ref}: footprint {c['footprint']} not found")
            new.SetFPIDAsString(c["footprint"])
            if fp is not None:
                board.Delete(fp)
            board.Add(new)
            fp = new
        fp.SetReference(ref)
        fp.SetValue(c["value"])
        fp.SetPath(pcbnew.KIID_PATH(c["path"]))
        fp.SetSheetname(c["sheetname"])
        fp.SetSheetfile(c["sheetfile"])
        for name, value in c["fields"]:
            if name not in ("Reference", "Value", "Footprint"):
                fp.SetField(name, value)
                # Custom fields are created visible on F.SilkS; they belong on the hidden fab layer.
                field = fp.GetField(name)
                field.SetVisible(False)
                field.SetLayer(pcbnew.F_Fab)
        x, y, rot = PLACEMENT.get(ref, (*OFF_BOARD, 0))
        fp.SetOrientationDegrees(rot)
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
        for pad in fp.Pads():
            name = pins.get((ref, pad.GetNumber()))
            pad.SetNet(net_item(board, name) if name else board.FindNet(""))
    board.BuildConnectivity()
    pcbnew.SaveBoard(dst, board)
    print("saved", dst, "footprints:", len(board.GetFootprints()))


if __name__ == "__main__":
    apply(Path(sys.argv[1]).resolve(), sys.argv[2], sys.argv[3], sys.argv[4])
