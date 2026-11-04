# ONE-SHOT placement generator used for the first placement draft (2026-11-03).
# WARNING: re-running it overwrites every footprint position in pcb_revC.kicad_pcb,
# including any manual moves made in KiCad afterwards. KiCad must be closed.
# Keep it as the record of the placement rationale (comments per part).
# Placement script for Buck Rev C. Run with KiCad's python:
#   "C:\Program Files\KiCad\10.0\bin\python.exe" place.py <board.kicad_pcb>
import sys, pcbnew
from pcbnew import VECTOR2I, FromMM as mm

board_path = sys.argv[1]
b = pcbnew.LoadBoard(board_path)

# Board outline (mm). Origin chosen so the board sits at (100,100).
X0, Y0, X1, Y1 = 100.0, 100.0, 178.5, 157.0

# ref: (x, y, rotation_deg)
P = {
    # ---- POWER: input -> hot loop -> inductors -> output, left to right
    "J1": (105.0, 107.0, 270),   # 12 V IN, wire entry faces left edge; pin1 VIN top, pin2 GND
    "C5": (104.0, 119.0, 0),     # DNP bulk electrolytic, right next to the input connector
    "C3": (112.8, 106.0, 90),    # input caps: VIN pad bottom (towards Q1 tab), GND pad top
    "C2": (115.4, 106.0, 90),
    "C1": (118.0, 106.0, 90),
    "C4": (121.0, 105.4, 90),    # 100 nF HF cap, closest to Q1 drain + D1 anode
    "Q1": (124.2, 110.5, 180),   # tab (VIN) faces the caps, leads (G,S) face L1
    "D1": (126.5, 105.15, 180),  # lies across Q1: K next to Q1 source, A next to cap GND
    "L1": (137.6, 108.0, 180),   # pad2 (SW) left, next to Q1 source
    "L2": (151.5, 108.0, 0),     # pad1 (VMID) faces L1 pad1, pad2 (VOUT) right
    "C6": (161.5, 104.5, 0),     # output caps: VOUT pad left, GND right
    "C7": (161.5, 107.5, 0),
    "C8": (161.5, 110.5, 0),     # DNP spare
    "J2": (173.0, 109.0, 90),    # base load 7.2R; wire entry faces right edge
    "J3": (173.0, 121.5, 90),    # 36R switched load
    "J4": (173.0, 134.0, 90),    # 24R switched load
    "TP4": (161.0, 114.5, 0),    # VOUT
    "TP8": (164.0, 114.5, 0),    # GND next to VOUT (ripple measurement)
    # ---- LOAD switches, next to their terminal blocks
    "Q6": (164.0, 119.0, 0), "R11": (159.3, 118.05, 0), "R13": (159.3, 120.0, 180),
    "Q7": (164.0, 131.5, 0), "R12": (159.3, 130.55, 180), "R14": (159.3, 132.5, 180),
    # ---- DRIVER: chain PWM -> Q2 -> Q3 -> totem -> R5 -> gate, under Q1
    "R6": (131.0, 115.6, 0),     # gate-source pulldown, between gate and SW
    "R5": (128.6, 117.0, 90),    # gate resistor, straight below Q1 gate lead
    "Q5": (131.4, 119.4, 0),     # PNP sink, collector to SW
    "Q4": (125.8, 119.3, 180),   # NPN source, collector to BOOT
    "C9": (129.4, 123.0, 90),    # bootstrap cap BOOT-SW, BOOT pad on the short BOOT line
    "R4": (126.4, 123.0, 90),    # BOOT -> DRV_B pull-up, top pad right under Q4 base
    "D2": (122.0, 123.8, 180),   # bootstrap diode VIN -> BOOT
    "Q3": (121.5, 119.5, 0),
    "R3": (117.8, 117.4, 0),
    "Q2": (117.3, 121.0, 90),
    "R1": (115.1, 126.0, 90),
    "R2": (113.3, 123.0, 270),
    "TP5": (111.5, 126.0, 0),    # PWM
    "TP3": (125.5, 115.8, 0),    # GATE
    "TP2": (135.5, 117.5, 0),    # SW
    "TP7": (138.5, 117.5, 0),    # GND next to SW/GATE
    "TP1": (102.5, 125.5, 0),    # VIN
    "TP6": (105.5, 125.5, 0),    # GND next to VIN
    # ---- NUCLEO-L432KC: CN3 (J5) top row, CN4 (J6) bottom row, 15.24 mm apart,
    #      pin 15 end at the left board edge (USB end per Arduino-Nano convention - verify)
    "J5": (143.06, 134.0, 270),
    "J6": (143.06, 149.24, 270),
    # ---- SENSE dividers + RC filters, right below the ADC pins J6.10 / J6.11
    "R7": (112.3, 152.5, 0), "R8": (115.66, 153.3, 270), "C10": (117.66, 153.3, 270),
    "C11": (120.2, 153.3, 270), "R10": (122.2, 153.3, 270), "R9": (125.6, 152.5, 180),
}

fps = {f.GetReference(): f for f in b.GetFootprints()}

# Mounting holes dropped by owner decision (also excluded from board in the schematic)
for r in ("H1", "H2", "H3", "H4"):
    if r in fps:
        b.Remove(fps.pop(r))

missing = set(fps) - set(P)
if missing:
    sys.exit(f"unplaced footprints: {sorted(missing)}")
for r, (x, y, rot) in P.items():
    f = fps[r]
    if f.IsFlipped():
        f.Flip(f.GetPosition(), False)
    f.SetOrientationDegrees(rot)
    f.SetPosition(VECTOR2I(mm(x), mm(y)))

# Remove any previous outline / helper drawings we own, then redraw
try:
    drawings = list(b.GetDrawings())
except TypeError:          # KiCad 10 SWIG quirk when the board has no drawings yet
    drawings = []
for d in drawings:
    if d.GetLayer() in (pcbnew.Edge_Cuts, pcbnew.Dwgs_User):
        b.Remove(d)

def rect(layer, x0, y0, x1, y1, w=0.1):
    s = pcbnew.PCB_SHAPE(b)
    s.SetShape(pcbnew.SHAPE_T_RECT)
    s.SetStart(VECTOR2I(mm(x0), mm(y0)))
    s.SetEnd(VECTOR2I(mm(x1), mm(y1)))
    s.SetLayer(layer)
    s.SetWidth(mm(w))
    b.Add(s)

def text(layer, x, y, msg, size=1.0):
    t = pcbnew.PCB_TEXT(b)
    t.SetText(msg)
    t.SetPosition(VECTOR2I(mm(x), mm(y)))
    t.SetLayer(layer)
    t.SetTextSize(VECTOR2I(mm(size), mm(size)))
    b.Add(t)

rect(pcbnew.Edge_Cuts, X0, Y0, X1, Y1, 0.1)

# NUCLEO-32 outline (approx 50.3 x 18.0 mm, centred on the header field) - reference only
cx = (143.06 + (143.06 - 14 * 2.54)) / 2
cy = (134.0 + 149.24) / 2
rect(pcbnew.Dwgs_User, cx - 25.15, cy - 9.0, cx + 25.15, cy + 9.0, 0.15)
text(pcbnew.Dwgs_User, cx, cy - 2.0, "NUCLEO-L432KC (approx. outline)", 1.0)
text(pcbnew.Dwgs_User, cx, cy + 1.0, "<- USB end assumed (pin 15) - VERIFY", 1.0)
text(pcbnew.Dwgs_User, cx, cy + 4.0, "keep both ends clear of tall parts", 0.8)

b.BuildConnectivity()
pcbnew.SaveBoard(board_path, b)

print("saved", board_path)
