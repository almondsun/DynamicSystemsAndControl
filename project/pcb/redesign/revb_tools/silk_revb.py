"""Rev B silkscreen: references go to F.Fab (assembly drawing); silk keeps only labels that
matter on the bench. Positions are explicit and checked afterwards by KiCad DRC.

    python3.14 -I silk_revb.py <in.kicad_pcb> <out.kicad_pcb>
"""
import sys

import pcbnew

LABELS = [
    # text, x, y, size mm, rotation deg
    ("BUCK REV B PROTOTYPE 2026-10-27", 152.0, 34.2, 1.2, 0),
    ("NOT VALIDATED - SEE BRING-UP PROTOCOL", 152.0, 36.2, 0.9, 0),
    ("J1 +12V", 113.6, 41.0, 1.0, 0),
    ("GND", 107.9, 41.0, 1.0, 0),
    ("J2 VOUT+", 195.4, 102.0, 1.0, 0),
    ("GND", 201.9, 102.0, 1.0, 0),
    ("J3 NUCLEO", 205.6, 62.0, 1.0, 0),
    ("1", 200.9, 45.0, 1.0, 0),
    ("VIN", 120.0, 38.9, 0.8, 0),
    ("GND", 114.0, 110.9, 0.8, 0),
    ("SW", 131.0, 106.6, 0.8, 0),
    ("GATE", 126.2, 78.6, 0.8, 0),
    ("VOUT", 189.5, 108.4, 0.8, 0),
    ("ISENSE", 185.5, 84.1, 0.8, 0),
]
KEEP_SILK_REF = {"Q1", "D2", "L1", "L2"}


def main() -> None:
    board = pcbnew.LoadBoard(sys.argv[1])
    for fp in board.GetFootprints():
        ref = fp.Reference()
        ref.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(0.8), pcbnew.FromMM(0.8)))
        ref.SetTextThickness(pcbnew.FromMM(0.12))
        if fp.GetReference() in KEEP_SILK_REF:
            continue
        ref.SetLayer(pcbnew.F_Fab)
        # Plain user texts duplicating the designator (inherited U5/U6 library texts).
        for item in list(fp.GraphicalItems()):
            if isinstance(item, pcbnew.PCB_TEXT) and item.GetText() == fp.GetReference():
                fp.Delete(item)
    # The DO-41 library "K" text lands on U1 pad 8; the square pad and fab band mark the cathode.
    d2 = board.FindFootprintByReference("D2")
    for item in list(d2.GraphicalItems()):
        if isinstance(item, pcbnew.PCB_TEXT) and item.GetText() == "K" and item.GetLayer() == pcbnew.F_SilkS:
            d2.Delete(item)
    for text, x, y, size, rot in LABELS:
        t = pcbnew.PCB_TEXT(board)
        t.SetText(text)
        t.SetLayer(pcbnew.F_SilkS)
        t.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
        t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(size), pcbnew.FromMM(size)))
        t.SetTextThickness(pcbnew.FromMM(max(0.15, size * 0.15)))
        t.SetTextAngleDegrees(rot)
        board.Add(t)
    pcbnew.SaveBoard(sys.argv[2], board)


if __name__ == "__main__":
    main()
