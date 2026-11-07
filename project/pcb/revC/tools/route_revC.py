"""route_revC.py <stage>  --  scripted (non-autorouted) routing of Buck 12 V -> 6 V, PCB Rev C.

Run with KiCad's Python:  "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" route_revC.py S1

Every run:
  1. (S1+) makes sure the project rules are in place (.kicad_pro Drive track width, .kicad_dru);
  2. loads the STAGING board (route_work/pcb_revC/pcb_revC.kicad_pcb, never the real project);
  3. deletes ALL tracks / arcs / vias and ALL zones (footprints, Edge.Cuts and drawings are never touched);
  4. rebuilds everything up to <stage>, fills the zones and saves;
  5. prints a self-check report (zone vertices and areas, outline clearances, fill necks, hot loop).

Coordinates are computed from live pad geometry.  Units: mm; y grows downwards (KiCad convention).
Layer strategy: F.Cu carries all power copper; B.Cu is reserved for the S4 GND pour and short signal jumps.
"""
import sys, os, json, math
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.normpath(os.path.join(HERE, "..", "pcb_revC"))
BOARD = os.path.join(PROJ, "pcb_revC.kicad_pcb")
PRO = os.path.join(PROJ, "pcb_revC.kicad_pro")
DRU = os.path.join(PROJ, "pcb_revC.kicad_dru")
STAGES = ["S1", "S2", "S3", "S4", "S5"]

FMM, TMM = pcbnew.FromMM, pcbnew.ToMM
F_CU = pcbnew.F_Cu

# Zone construction constants (mm)
M = 0.15      # how far a zone outline extends beyond a pad it must cover
G = 0.35      # outline gap to foreign copper (0.3 mm Power clearance + 0.05 margin)
EDGE = 0.5    # zone keep-back from the board edge (spec; project copper-to-edge rule is 0.3)
Z_CLEAR, Z_MIN_THICK = 0.3, 0.25
SPOKE_W, THERMAL_GAP = 0.6, 0.5       # THT thermal reliefs (spec: 4 spokes >= 0.5 mm)

PRIO = {"SW": 5, "VMID": 5, "VIN": 4, "VOUT": 4, "GND_HOT": 3}   # S4 global GND pour = 0


# ----------------------------------------------------------------------------------------------
# Project rules (S1)
# ----------------------------------------------------------------------------------------------
DRU_TEXT = """(version 1)
# Buck Rev C custom design rules (router stage S1, 2026-11-05).
# Netclasses (.kicad_pro): Power = VIN, SW, VOUT, VMID, LOAD_A, LOAD_B ; Drive = GATE, BOOT, DRV_E, DRV_B.

# Power nets keep 0.3 mm from any other net (tracks, pads, zones, vias).
(rule "Power clearance 0.3 mm"
  (condition "(A.hasNetclass('Power') || B.hasNetclass('Power')) && A.Net != B.Net")
  (constraint clearance (min 0.3mm)))

# Power tracks are full width.  VIN, SW and VOUT carry their main current in ZONES; the only tracks
# on those nets are the owner-approved thin branches (VIN -> R3 / D2 anode / R9 at 0.25-0.5 mm,
# SW -> driver at 0.5 mm, VOUT Kelvin tap -> R7 at 0.25 mm), so they get their own minimums below.
(rule "Power track min width 1.5 mm"
  (condition "A.hasNetclass('Power') && A.NetName != 'VIN' && A.NetName != 'SW' && A.NetName != 'VOUT'")
  (constraint track_width (min 1.5mm)))

(rule "VIN / VOUT branch tracks min width 0.25 mm"
  (condition "A.NetName == 'VIN' || A.NetName == 'VOUT'")
  (constraint track_width (min 0.25mm)))

(rule "SW driver branch min width 0.5 mm"
  (condition "A.NetName == 'SW'")
  (constraint track_width (min 0.5mm)))

# Gate-drive loop nets.
(rule "Drive track min width 0.5 mm"
  (condition "A.hasNetclass('Drive')")
  (constraint track_width (min 0.5mm)))
"""


def write_rules():
    """Drive netclass track_width = 0.5 (other fields untouched) and the custom .kicad_dru."""
    with open(PRO, encoding="utf-8") as f:
        pro = json.load(f)
    before = json.dumps(pro, sort_keys=True)
    drive = [c for c in pro["net_settings"]["classes"] if c["name"] == "Drive"]
    assert len(drive) == 1
    drive[0]["track_width"] = 0.5
    power = [c for c in pro["net_settings"]["classes"] if c["name"] == "Power"]
    assert len(power) == 1
    power[0]["clearance"] = 0.3                                   # RUL-1: netclass agrees with the .kicad_dru
    pro["board"]["design_settings"]["rules"]["min_hole_clearance"] = 0.3   # margin over JLC 0.28 mm
    if json.dumps(pro, sort_keys=True) != before:
        with open(PRO, "w", encoding="utf-8", newline="\n") as f:
            json.dump(pro, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print("kicad_pro: Drive.track_width 0.5, Power.clearance 0.3, min_hole_clearance 0.3")
    with open(DRU, "w", encoding="utf-8", newline="\n") as f:
        f.write(DRU_TEXT)
    print("kicad_dru written:", DRU)


# ----------------------------------------------------------------------------------------------
# Geometry helpers
# ----------------------------------------------------------------------------------------------
def V(x, y):
    return pcbnew.VECTOR2I(FMM(x), FMM(y))


def all_zones(board):
    return [board.GetArea(i) for i in range(board.GetAreaCount())]


def board_rect(board):
    """The single Edge.Cuts rectangle (x0, y0, x1, y1) in mm, from its geometry (not the stroked bbox)."""
    r = [d for d in board.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts]
    assert len(r) == 1 and r[0].GetShape() == pcbnew.SHAPE_T_RECT
    s, e = r[0].GetStart(), r[0].GetEnd()
    return (TMM(min(s.x, e.x)), TMM(min(s.y, e.y)), TMM(max(s.x, e.x)), TMM(max(s.y, e.y)))


class PadInfo:
    """Live pad geometry in mm: centre (x, y), bounding box (x0, y0, x1, y1), net name, radius if round."""
    def __init__(self, board, ref, num):
        fp = board.FindFootprintByReference(ref)
        pads = [p for p in fp.Pads() if p.GetNumber() == num]
        assert len(pads) == 1, (ref, num)
        p = self.pad = pads[0]
        self.name = f"{ref}.{num}"
        self.x, self.y = TMM(p.GetPosition().x), TMM(p.GetPosition().y)
        bb = p.GetBoundingBox()
        self.x0, self.y0, self.x1, self.y1 = TMM(bb.GetLeft()), TMM(bb.GetTop()), TMM(bb.GetRight()), TMM(bb.GetBottom())
        self.net = p.GetNetname()
        self.r = TMM(p.GetSize(F_CU).x) / 2 if p.GetShape(F_CU) == pcbnew.PAD_SHAPE_CIRCLE else None


def track(board, netname, width, pts_nm, layer=F_CU, log=None):
    """Straight segments through integer-nm points; every segment must be a multiple of 45 deg and
    every corner a 45 deg turn (interior angle 135 deg), i.e. no 90 deg or acute corners."""
    net = board.FindNet(netname)
    assert net is not None, netname
    dirs = []
    for (x0, y0), (x1, y1) in zip(pts_nm, pts_nm[1:]):
        dx, dy = x1 - x0, y1 - y0
        assert (dx, dy) != (0, 0)
        assert dx == 0 or dy == 0 or abs(dx) == abs(dy), f"{netname}: segment not at 45 deg multiple"
        dirs.append((dx and (1 if dx > 0 else -1), dy and (1 if dy > 0 else -1)))
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(x0, y0)); t.SetEnd(pcbnew.VECTOR2I(x1, y1))
        t.SetWidth(FMM(width)); t.SetLayer(layer); t.SetNet(net)
        board.Add(t)
    for a, b in zip(dirs, dirs[1:]):
        cos = (a[0] * b[0] + a[1] * b[1]) / (math.hypot(*a) * math.hypot(*b))
        assert cos > 0.7, f"{netname}: corner sharper than a 45 deg turn"
    if log is not None:
        log.append((netname, width, pcbnew.LayerName(layer), [(round(TMM(x), 3), round(TMM(y), 3)) for x, y in pts_nm]))


def nm(v):
    return int(round(v * 1e6))


def walk(start, *steps):
    """45-degree path builder in mm.  Steps: ("h", x) / ("v", y) straight moves; ("dx", x, sy) diagonal to x
    going down (sy=+1) or up (sy=-1); ("dy", y, sx) diagonal to y going right (sx=+1) or left (sx=-1).
    Returns integer-nm points for track()."""
    x, y = start
    pts = [(x, y)]
    for s in steps:
        if s[0] == "h":
            x = s[1]
        elif s[0] == "v":
            y = s[1]
        elif s[0] == "dx":
            y, x = y + s[2] * abs(s[1] - x), s[1]
        elif s[0] == "dy":
            x, y = x + s[2] * abs(s[1] - y), s[1]
        pts.append((x, y))
    return [(nm(a), nm(b)) for a, b in pts]


def via(board, netname, x, y, dia=0.6, drill=0.3, log=None):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(nm(x), nm(y)))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetWidth(FMM(dia)); v.SetDrill(FMM(drill))
    v.SetNet(board.FindNet(netname))
    board.Add(v)
    if log is not None:
        log.append((netname, f"via {dia}/{drill}", "F.Cu-B.Cu", [(round(x, 4), round(y, 4))]))


def zone(board, name, netname, priority, pts, log=None):
    """F.Cu copper zone with an explicit polygon outline (editable later in KiCad).
    SMD pads solid, THT pads thermal (ZONE_CONNECTION_THT_THERMAL)."""
    z = pcbnew.ZONE(board)
    z.SetLayer(F_CU)
    net = board.FindNet(netname)
    assert net is not None, netname
    z.SetNet(net)
    z.SetZoneName(name)
    z.SetAssignedPriority(priority)
    z.SetLocalClearance(FMM(Z_CLEAR))
    z.SetMinThickness(FMM(Z_MIN_THICK))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THT_THERMAL)
    z.SetThermalReliefGap(FMM(THERMAL_GAP))
    z.SetThermalReliefSpokeWidth(FMM(SPOKE_W))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    o = z.Outline()
    o.NewOutline()
    for x, y in pts:
        o.Append(FMM(x), FMM(y))
    board.Add(z)
    if log is not None:
        log.append((name, netname, priority, [(round(x, 3), round(y, 3)) for x, y in pts]))
    return z


# ----------------------------------------------------------------------------------------------
# Stage S1: power copper (zones), LOAD tracks, hot-loop GND
# ----------------------------------------------------------------------------------------------
def build_s1(b, zlog, tlog):
    P = lambda ref, num: PadInfo(b, ref, num)
    ex0, ey0, ex1, ey1 = board_rect(b)                                  # Edge.Cuts geometry (no stroke)
    X0, Y0, X1 = ex0 + EDGE, ey0 + EDGE, ex1 - EDGE                     # 100.5, 100.5, 178.0

    # --- pads used below -------------------------------------------------------------------
    J1v, J1g = P("J1", "1"), P("J1", "2")                    # VIN in, GND in (THT)
    C1v, C3v = P("C1", "1"), P("C3", "1")                    # bulk VIN pads (C2 between)
    C1g, C3g = P("C1", "2"), P("C3", "2")                    # bulk GND pads
    C4v, C4g = P("C4", "1"), P("C4", "2")                    # 100 nF hot-loop cap
    C5v, C5g = P("C5", "1"), P("C5", "2")                    # 100 uF electrolytic (THT)
    TP1, TP6 = P("TP1", "1"), P("TP6", "1")                  # VIN / GND test points
    TAB, QS, QG = P("Q1", "2"), P("Q1", "3"), P("Q1", "1")   # drain tab (VIN), source (SW), gate
    D1k, D1a = P("D1", "1"), P("D1", "2")                    # freewheel diode K = SW, A = GND
    L1s, L1m, L2m, L2o = P("L1", "2"), P("L1", "1"), P("L2", "1"), P("L2", "2")
    C6v, C8v, C6g, C8g = P("C6", "1"), P("C8", "1"), P("C6", "2"), P("C8", "2")
    TP4, TP8 = P("TP4", "1"), P("TP8", "1")                  # VOUT / GND test points
    J2o, J2g = P("J2", "1"), P("J2", "2")                    # base load: VOUT / GND
    J3o, J3a = P("J3", "1"), P("J3", "2")                    # 36 ohm: VOUT / LOAD_A
    J4o, J4b = P("J4", "1"), P("J4", "2")                    # 24 ohm: VOUT / LOAD_B
    Q6d, Q7d = P("Q6", "3"), P("Q7", "3")                    # load-switch drains
    R3v, R3d = P("R3", "1"), P("R3", "2")                    # VIN pull-up (branch in S2), DRV_IN
    Q3b = P("Q3", "1")                                       # DRV_IN (driver)
    TP3 = P("TP3", "1")                                      # GATE test point

    # ---------------------------------------------------------------------------------------
    # 1) Hot-loop GND (local, priority 3 > global pour 0): one solid F.Cu plate joining
    #    D1 anode, C4 GND and the C1-C3 GND pads (all solid SMD connections), from the top
    #    board edge down to the VIN boundary.  It also leaves room for S4 stitching vias.
    #    The GND/VIN boundary is a 0.35 mm slot that steps around C4 (0603, 0.64 mm pad gap).
    # ---------------------------------------------------------------------------------------
    gnd_bot = round(C1v.y0 - G - 0.2, 3)                            # 106.35 (1.25 mm below C1-3.2)
    vin_top = round(gnd_bot + G, 3)                                 # 106.70 (covers C1-3.1 by 0.2)
    assert gnd_bot > C1g.y1 + M
    c4_gnd_bot = round(C4g.y1 + M, 3)                               # 105.225 (covers C4.2)
    c4_vin_top = round(C4v.y0 - M, 3)                               # 105.575 (covers C4.1)
    assert abs(c4_vin_top - c4_gnd_bot - G) < 1e-6
    d1_gnd_bot = round(D1a.y1 + M, 3)                               # 106.20 (covers D1.2)
    tab_vin_top = round(d1_gnd_bot + G, 3)                          # 106.55
    fx0, fx1 = round(C4v.x0 - M, 3), round(C4v.x1 + M, 3)           # VIN finger up to C4.1
    d = G * math.sqrt(2)                                            # 45 deg edge offset for a 0.35 gap
    # The finger's top corners start 45 deg shoulders (lines x+y = kL and x-y = kR); the GND outline
    # runs parallel 0.35 mm away (135 deg convex corners, so the offset lines keep >= 0.35 mm).
    kL = fx0 + c4_vin_top
    kR = fx1 - c4_vin_top
    gnd_hot = [
        (C3g.x0 - 2.3, Y0),                         # top-left (x 109.6), room for stitching vias
        (round(D1a.x1 + M, 3), Y0),                 # over D1 anode
        (round(D1a.x1 + M, 3), d1_gnd_bot),
        (round(kR + d + d1_gnd_bot, 3), d1_gnd_bot),            # parallel to the VIN shoulder
        (round(kR + d + c4_gnd_bot, 3), c4_gnd_bot),            # over C4.2
        (round(kL - d - c4_gnd_bot, 3), c4_gnd_bot),
        (round(kL - d - gnd_bot, 3), gnd_bot),
        (C3g.x0 - 2.3, gnd_bot),                    # under C1-C3 GND pads
    ]
    zone(b, "GND_hotloop", "GND", PRIO["GND_HOT"], gnd_hot, zlog)

    # ---------------------------------------------------------------------------------------
    # 2) VIN input zone (priority 4): J1.1 -> C1-C3 VIN pads -> C4.1 finger -> Q1 tab (heatsink),
    #    plus a strip along the left board edge (left of J1.2) to C5.1 and TP1.
    #    Extends below the tab (x <= 124, clear of TP3/GATE) so the S2 branches to R3.1 and to
    #    the D2 anode start close to their pads.  R3.1 is deliberately NOT inside the zone
    #    (0603 with one pad in a pour and one on a track would tombstone): S2 adds a 0.5 mm branch.
    # ---------------------------------------------------------------------------------------
    j1_top = round(J1v.y0 - 0.85, 3)                       # 104.85: J1.1 top spoke has 0.35 mm of fill
    j1_right = round(J1v.x1 + 0.5, 3)                      # 106.80, then a 45 deg chamfer to the band
    band_bot = 109.60                                      # band/strip bottom, 1.1 mm above J1.2
    strip_x = round(J1g.x - J1g.r - G - 0.05, 3)           # 103.30: strip right edge beside J1.2
    c5_x = round(C5g.x - C5g.r - 0.8, 3)                   # 104.90: strip widens to cover C5.1
    tp6_x = round(TP6.x - TP6.r - 0.4, 3)                  # 104.10: strip narrows beside TP6
    tab_r = round(TAB.x1 + M, 3)                           # 126.29
    tab_b = round(TAB.y1 + M, 3)                           # 113.55
    ext_r = round(TP3.x - TP3.r - 0.5, 3)                  # 124.00: 0.5 mm from TP3 (GATE)
    ext_b = round(Q3b.y0 - 0.75, 3)                        # 117.50: 0.75 mm above Q3 base pad
    r3_top = round(R3v.y0 - 1.325, 3)                      # 115.60: ~1.3 mm neck for the R3.1 branch
    vin = [
        (X0, j1_top),
        (j1_right, j1_top),
        (round(j1_right + (vin_top - j1_top), 3), vin_top),        # 45 deg chamfer
        (round(kL - vin_top, 3), vin_top),                          # band top under C1-C3
        (fx0, c4_vin_top), (fx1, c4_vin_top),                       # finger top over C4.1
        (round(kR + tab_vin_top, 3), tab_vin_top),                  # 45 deg back down
        (tab_r, tab_vin_top),                                       # tab top, under D1
        (tab_r, tab_b),
        (round(ext_r + 0.85, 3), tab_b),                            # step in, 45 deg, past TP3
        (ext_r, round(tab_b + 0.85, 3)),
        (ext_r, ext_b),
        (round(R3d.x1 + 1.875, 3), ext_b),                          # 45 deg around R3.2 (DRV_IN)
        (round(R3d.x1 + 1.875 - (ext_b - r3_top), 3), r3_top),
        (116.40, r3_top),
        (116.40, band_bot),
        (strip_x, band_bot),
        (strip_x, 113.00),
        (c5_x, round(113.00 + (c5_x - strip_x), 3)),                # 45 deg out past J1.2
        (c5_x, 122.90),
        (tp6_x, round(122.90 + (c5_x - tp6_x), 3)),                 # 45 deg in past TP6
        (tp6_x, round(TP1.y1 + 1.1, 3)),
        (X0, round(TP1.y1 + 1.1, 3)),
    ]
    zone(b, "VIN_input", "VIN", PRIO["VIN"], vin, zlog)

    # ---------------------------------------------------------------------------------------
    # 3) SW node (priority 5), minimum area: Q1 source <-> D1 cathode <-> L1.2, >= 2.7 mm wide.
    #    The driver branch (C9.2, Q5.3, R6.2, TP2; 0.5 mm, beside GATE) leaves L1.2's bottom in S2.
    # ---------------------------------------------------------------------------------------
    sx0 = round(D1k.x0 - M, 3)          # 127.10
    sy0 = round(D1k.y0 - M, 3)          # 104.10
    lx0, lx1 = round(L1s.x0 - M, 3), round(L1s.x1 + M, 3)    # 131.15, 134.35
    ly0, ly1 = round(L1s.y0 - M, 3), round(L1s.y1 + M, 3)    # 105.15, 110.85
    qx0, qx1, qy1 = round(QS.x0 - M, 3), round(QS.x1 + M, 3), round(QS.y1 + M, 3)   # 127.99, 130.49, 108.97
    dy1 = round(D1k.y1 + M, 3)          # 106.20
    sw = [
        (sx0, sy0),
        (round(lx0 - (ly0 - sy0), 3), sy0),         # 45 deg chamfer to L1.2 top
        (lx0, ly0), (lx1, ly0), (lx1, ly1), (lx0, ly1),
        (lx0, round(qy1 + (lx0 - qx1), 3)),         # 45 deg into Q1.3's lower edge
        (qx1, qy1), (qx0, qy1),
        (qx0, round(dy1 + (qx0 - sx0), 3)),         # 45 deg up to D1.1 (keeps 0.8 mm from the tab)
        (sx0, dy1),
    ]
    zone(b, "SW_node", "SW", PRIO["SW"], sw, zlog)

    # ---------------------------------------------------------------------------------------
    # 4) VMID (priority 5): L1.1 <-> L2.1 at full pad height (5.7 mm), under the inductor bodies.
    # ---------------------------------------------------------------------------------------
    vmid = [(round(L1m.x0 - M, 3), round(L1m.y0 - M, 3)), (round(L2m.x1 + M, 3), round(L2m.y0 - M, 3)),
            (round(L2m.x1 + M, 3), round(L2m.y1 + M, 3)), (round(L1m.x0 - M, 3), round(L1m.y1 + M, 3))]
    zone(b, "VMID", "VMID", PRIO["VMID"], vmid, zlog)

    # ---------------------------------------------------------------------------------------
    # 5) VOUT (priority 4): L2.2 + C6-C8 VOUT pads + TP4, then a 2.75 mm strip along the top edge
    #    (above the C6-C8 GND pads, which face J2) over J2.2 (GND) to a 3.35 mm bus RIGHT of the
    #    terminal pins (x 174.65-178.0) with a pocket round each VOUT pin J2.1/J3.1/J4.1.
    #    The VOUT pins alternate with GND/LOAD pins, so the bus never crosses LOAD_A/LOAD_B.
    #    The top strip over J2.2 is the only place under 2 mm: 1.90 mm (0.5 mm edge + 0.3 mm gap).
    # ---------------------------------------------------------------------------------------
    cap_gx = round(C6g.x0 - G, 3)                 # 162.05: column edge left of C6-C8 GND pads
    strip_b = round(C6g.y0 - G, 3)                # 103.25: strip bottom above C6.2
    bus_x = round(J2g.x + J2g.r + G, 3)           # 174.65: bus left edge, 0.35 mm right of the pins
    j22_top = round(J2g.y - J2g.r - 0.30, 3)      # 102.40: pinch over J2.2 (0.30 mm = rule clearance)
    pk_x = round(J2o.x0 - 1.3, 3)                 # 170.40: pocket left edge (left thermal spoke)
    tp8_x = round(TP8.x - TP8.r - G, 3)           # 162.65: right of TP4, clear of TP8
    vout = [
        (round(L2o.x0 - M, 3), Y0),
        (X1, Y0),
        (X1, round(J4o.y1 + 1.2, 3)),                                # bus bottom below J4.1
        (pk_x, round(J4o.y1 + 1.2, 3)),
        (pk_x, round(J4b.y + J4b.r + G, 3)), (bus_x, round(J4b.y + J4b.r + G, 3)),   # J4.1 pocket
        (bus_x, round(J3o.y1 + 1.8, 3)), (pk_x, round(J3o.y1 + 1.8, 3)),
        (pk_x, round(J3a.y + J3a.r + G, 3)), (bus_x, round(J3a.y + J3a.r + G, 3)),   # J3.1 pocket
        (bus_x, round(J2o.y1 + 2.7, 3)), (pk_x, round(J2o.y1 + 2.7, 3)),
        (pk_x, round(J2o.y0 - 0.95, 3)), (bus_x, round(J2o.y0 - 0.95, 3)),           # J2.1 pocket
        (bus_x, j22_top),                                            # up the bus past J2.2
        (round(J2g.x - 1.5, 3), j22_top),                            # over J2.2 (pinch)
        (round(J2g.x - 1.5 - (strip_b - j22_top), 3), strip_b),      # 45 deg down to the strip
        (cap_gx, strip_b),
        (cap_gx, round(C8g.y1 + G, 3)),
        (tp8_x, round(C8g.y1 + G + (tp8_x - cap_gx), 3)),           # 45 deg out to take TP4
        (tp8_x, round(TP4.y1 + 1.0, 3)),
        (round(TP4.x0 - 1.0, 3), round(TP4.y1 + 1.0, 3)),            # TP4 pocket (3 spokes)
        (round(TP4.x0 - 1.0, 3), round(C8v.y1 + M, 3)),
        (round(L2o.x0 - M, 3), round(C8v.y1 + M, 3)),
    ]
    zone(b, "VOUT_bus", "VOUT", PRIO["VOUT"], vout, zlog)

    # ---------------------------------------------------------------------------------------
    # 6) LOAD_A / LOAD_B: 1.5 mm F.Cu tracks from the terminal pin, left, one 45 deg dogleg,
    #    then horizontally into the SOT-23 drain pad along its long (x) axis.
    # ---------------------------------------------------------------------------------------
    for jp, qd, net in ((J3a, Q6d, "LOAD_A"), (J4b, Q7d, "LOAD_B")):
        jx, jy = jp.pad.GetPosition().x, jp.pad.GetPosition().y
        qx, qy = qd.pad.GetPosition().x, qd.pad.GetPosition().y
        xb = qx + FMM(0.9625)             # short straight entry into the pad
        xa = xb + (qy - jy)               # exact 45 deg dogleg (integer nm)
        track(b, net, 1.5, [(jx, jy), (xa, jy), (xb, qy), (qx, qy)], log=tlog)


# ----------------------------------------------------------------------------------------------
# Stage S2: driver, gate and bootstrap
# ----------------------------------------------------------------------------------------------
W_DRIVE, W_SW, W_VIN, W_SIG = 0.5, 0.5, 0.5, 0.3


def build_s2(b, tlog):
    c = lambda ref, num: (PadInfo(b, ref, num).x, PadInfo(b, ref, num).y)     # pad centre (mm)
    P = lambda ref, num: PadInfo(b, ref, num)
    T = lambda net, w, pts, layer=F_CU: track(b, net, w, pts, layer, log=tlog)

    q1g, q4c, q4e, q4b = P("Q1", "1"), c("Q4", "3"), c("Q4", "2"), c("Q4", "1")
    q5b, q5e, q5c = c("Q5", "1"), c("Q5", "2"), c("Q5", "3")
    q3b, q3c, q2b, q2c = c("Q3", "1"), c("Q3", "3"), c("Q2", "1"), c("Q2", "3")
    r1b, r2a, r3v, r3d = c("R1", "2"), c("R2", "1"), c("R3", "1"), c("R3", "2")
    r4b, r4d, r5e, r5g = c("R4", "1"), c("R4", "2"), c("R5", "1"), c("R5", "2")
    r6g, r6s, c9b, c9s = c("R6", "1"), c("R6", "2"), c("C9", "1"), c("C9", "2")
    d2k, d2a, tp2, tp3, tp9 = c("D2", "1"), c("D2", "2"), c("TP2", "1"), c("TP3", "1"), c("TP9", "1")
    gap_x = round((P("Q3", "3").x1 + P("Q4", "3").x0) / 2, 4)       # 123.65: Q3.3 | Q4.3 gap centre

    # --- GATE (0.5): three straight runs, each starting at its own point inside the Q1.1 pad -------
    gy = q1g.y
    T("GATE", W_DRIVE, walk((r5g[0], gy), ("v", r5g[1])))                       # Q1.1 -> R5.2 (x 128.6)
    T("GATE", W_DRIVE, walk((r6g[0], gy), ("v", r6g[1])))                       # Q1.1 -> R6.1 (x 130.175)
    T("GATE", W_DRIVE, walk((r5g[0] - 0.3, gy), ("dx", tp3[0], +1), ("v", tp3[1])))   # Q1.1 -> TP3 (gate probe)

    # --- DRV_E (0.5): Q4 emitter -> R5.1 -> Q5 emitter, one chain through the R5.1 pad ----------
    T("DRV_E", W_DRIVE, walk(q4e, ("h", 127.6), ("dy", 118.1, +1), ("h", r5e[0]),
                             ("dy", 118.6, +1), ("v", 119.6), ("dy", q5e[1], +1), ("h", q5e[0])))

    # --- SW driver branch (0.5): leaves SW_node once, at L1.2's lower edge, then straight down
    #     through R6.2 and the inner end of Q5.3 to C9.2 (return path beside GATE / DRV_E).
    sw_x = r6s[0]                                                                # 131.825
    T("SW", W_SW, walk((sw_x, 110.6), ("v", r6s[1]), ("v", q5c[1]), ("v", 121.0),
                       ("dy", c9s[1], -1), ("h", c9s[0])))
    T("SW", W_SW, walk(q5c, ("h", 133.6), ("dx", tp2[0], -1)))                  # Q5.3 -> TP2 (probe)

    # --- BOOT (0.5): one pad-to-pad chain Q4.3 -> D2.1 -> R4.1 -> C9.1 (no Y node; reviewer S2 fix) ---
    yd = round(d2k[1] - 0.8875, 4)                                               # 122.9125: 45 deg lands here
    yn = round(yd - (q4c[0] - d2k[0]), 4)                                        # 121.70
    T("BOOT", W_DRIVE, walk(q4c, ("v", yn), ("dy", yd, -1), ("v", d2k[1])))           # -> D2.1 (the 90 deg
    T("BOOT", W_DRIVE, walk(d2k, ("h", r4b[0]), ("h", c9b[0])))                        #  turn is inside D2.1)
    T("BOOT", W_DRIVE, walk(c9b, ("v", 125.9), ("dx", tp9[0] + 0.8, +1), ("h", tp9[0])))    # C9.1 -> TP9

    # --- DRV_B (0.5): three F.Cu islands joined by ONE B.Cu run through three vias ---------------
    #     (Q3.3 is boxed in by BOOT / VIN->D2; Q5.1 sits in the DRV_E / GATE / SW cell.)
    va = (q3c[0], 120.45)                                    # under Q3.3
    vb = (q4b[0], 121.05)                                    # between Q4.1 and R4.2
    vc = (q5b[0], 117.4)                                     # above Q5.1, below R6
    T("DRV_B", W_DRIVE, walk(q3c, ("v", va[1])))
    T("DRV_B", W_DRIVE, walk(q4b, ("v", vb[1]), ("v", 121.75), ("dy", r4d[1], -1)))  # Q4.1 -> via -> R4.2
    T("DRV_B", W_DRIVE, walk(q5b, ("v", vc[1])))
    for v in (va, vb, vc):
        via(b, "DRV_B", v[0], v[1], log=tlog)
    T("DRV_B", W_DRIVE, walk(va, ("h", vb[0] - 0.6), ("dy", vb[1], +1), ("h", vb[0] + 0.6),
                             ("dx", vc[0], -1), ("v", vc[1])), pcbnew.B_Cu)

    # --- VIN branches: each leaves VIN_input at one point and ends on its own pad ---------------
    T("VIN", W_VIN, walk((r3v[0], 115.35), ("v", r3v[1])))                       # -> R3.1 (0.5)
    T("VIN", W_VIN, walk((gap_x, 117.3), ("v", 118.6)))                          # -> D2.2: 0.5 to the gap,
    T("VIN", 0.25, walk((gap_x, 118.6), ("v", 120.2)))                           #   0.25 between Q3.3/Q4.3,
    T("VIN", W_VIN, walk((gap_x, 120.2), ("v", 120.55), ("dy", 121.55, -1), ("h", 121.35),
                         ("dy", 122.55, -1), ("v", d2a[1])))                      #   0.5 under Q3 to D2.2

    # --- DRV_IN (0.3): branch point inside the R3.2 pad; 45 deg legs to Q2.3 and Q3.1 (along its axis)
    T("DRV_IN", W_SIG, walk(r3d, ("dx", q2c[0], +1), ("v", q2c[1])))
    T("DRV_IN", W_SIG, walk(r3d, ("dy", q3b[1], +1), ("h", q3b[0])))

    # --- Q2 base (0.3): chain R2.1 -> Q2.1 -> R1.2 (no Y node; reviewer S2 fix) --------------------
    T("Net-(Q2-B)", W_SIG, walk(r2a, ("h", q2b[0])))                                     # R2.1 -> into Q2.1
    T("Net-(Q2-B)", W_SIG, walk((q2b[0], r2a[1]), ("v", r1b[1] - (q2b[0] - r1b[0])), ("dx", r1b[0], +1)))  # -> R1.2

    # loop polygons for the report (track centre lines; components as straight pad-to-pad links)
    die = q1_die(b)
    q1s = c("Q1", "3")
    gate_loop = [(c9b[0], d2k[1]), d2k, (d2k[0], yd), (q4c[0], yn), q4c, q4e,
                 (127.6, q4e[1]), (127.85, 118.1), (r5e[0], 118.1), r5g, (r5g[0], gy), die, q1s,
                 (sw_x, 110.6), (sw_x, 121.0), (130.775, c9s[1]), c9s]
    turnoff_loop = [(r5g[0], gy), r5g, (r5e[0], 118.1), (129.1, 118.6), (129.1, 119.6), (129.85, q5e[1]), q5e,
                    (sw_x, q5c[1]), (sw_x, 110.6), q1s, die]
    return {"gate drive (C9 -> Q4 -> R5 -> Q1 -> SW -> C9)": gate_loop,
            "turn-off (Q1.G -> R5 -> Q5 -> SW -> Q1.S)": turnoff_loop}


# ----------------------------------------------------------------------------------------------
# Stage S3: NUCLEO signals, load-switch gates, sense nets, VOUT Kelvin tap, VIN tap, TRIG
# ----------------------------------------------------------------------------------------------
W_SENSE, W_TAP = 0.3, 0.25


def build_s3(b, tlog):
    c = lambda ref, num: (PadInfo(b, ref, num).x, PadInfo(b, ref, num).y)
    T = lambda net, w, pts, layer=F_CU: track(b, net, w, pts, layer, log=tlog)

    # --- PWM (0.3): straight up x = R1.1's x from inside J5.12; TP5 stub from R1.1's left half ---
    r1p, j512, tp5 = c("R1", "1"), c("J5", "12"), c("TP5", "1")
    T("PWM", W_SIG, walk((r1p[0], j512[1]), ("v", r1p[1])))
    T("PWM", W_SIG, walk((r1p[0] - 0.3, r1p[1]), ("h", tp5[0] + (r1p[1] - tp5[1])), ("dx", tp5[0], -1)))

    # --- load-switch gates (0.3): pad-to-pad, the two tracks meet only through pad copper -------
    for ra, rb, q in (("R11", "R13", "Q6"), ("R12", "R14", "Q7")):
        rg = c(ra, "2" if ra == "R11" else "1")            # R11.2 / R12.1 (gate side of the series R)
        pd = c(rb, "1")                                     # R13.1 / R14.1 (pull-down)
        qg = c(q, "1")
        T(f"Net-({q}-G)", W_SIG, walk(pd, ("v", rg[1] + 0.25)))          # pull-down -> into the series R pad
        T(f"Net-({q}-G)", W_SIG, walk(rg, ("h", qg[0])))                 # series R -> gate, along Q's axis

    # --- LSW_A (0.3): R11.1 <- short F.Cu stub <- B.Cu hop under the Kelvin tap (x 157.1 -> 155.5,
    #     y 121.0) <- 45 deg run over the free middle <- J5.5 from above ---------------------------
    r11, j55 = c("R11", "1"), c("J5", "5")
    la1, la2 = (157.1, 121.0), (155.5, 121.0)
    T("LSW_A", W_SIG, walk(la1, ("v", r11[1] + (r11[0] - la1[0])), ("dy", r11[1], +1)))
    via(b, "LSW_A", *la1, log=tlog); via(b, "LSW_A", *la2, log=tlog)
    T("LSW_A", W_SIG, walk(la1, ("h", la2[0])), pcbnew.B_Cu)
    T("LSW_A", W_SIG, walk(la2, ("dy", 134.0, -1), ("h", j55[0] + 1.0), ("dy", 135.0, -1), ("v", j55[1])))

    # --- LSW_B (0.3): J5.6 down under the NUCLEO (y 139.3), out of the right end, 45 deg up,
    #     B.Cu hop under the Kelvin tap (x 155.4 -> 157.2, y 130.55), into R12.2 along its axis ---
    r12, j56 = c("R12", "2"), c("J5", "6")
    lb1, lb2 = (155.4, r12[1]), (157.2, r12[1])
    yb = 139.3
    T("LSW_B", W_SIG, walk(j56, ("v", yb - 0.5), ("dy", yb, +1), ("h", lb1[0] - 0.65 - (yb - lb1[1])),
                           ("dx", lb1[0] - 0.65, -1), ("h", lb1[0])))
    via(b, "LSW_B", *lb1, log=tlog); via(b, "LSW_B", *lb2, log=tlog)
    T("LSW_B", W_SIG, walk(lb1, ("h", lb2[0])), pcbnew.B_Cu)
    T("LSW_B", W_SIG, walk(lb2, ("h", r12[0])))

    # --- sense dividers (0.3): J6 pin straight down into the filter cap; divider row at y 155.5 ---
    for jp, cap, r_lo, r_hi, net in (("11", "C10", "R8", ("R7", "2"), "VOUT_SENSE"),
                                     ("10", "C11", "R10", ("R9", "2"), "VIN_SENSE")):
        jpc, cc = c("J6", jp), c(cap, "1")
        T(net, W_SENSE, walk(jpc, ("v", cc[1] - 0.225)))                 # J6 pin -> C (tight)
        row = [cc, c(r_lo, "1"), c(*r_hi)]
        y = c(*r_hi)[1]                                                  # 155.5 (R7.2 / R9.2 centre)
        T(net, W_SENSE, walk((row[0][0], y), ("h", row[1][0]), ("h", row[2][0])))

    # --- TRIG (0.3): J6.9 -> TP10, above the divider row ---------------------------------------
    j69, tp10 = c("J6", "9"), c("TP10", "1")
    T("Net-(J6-Pin_9)", W_SIG, walk(j69, ("dy", 154.3, +1), ("h", tp10[0] - (tp10[1] - 154.3)), ("dy", tp10[1], +1)))

    # --- VIN tap to R9.1 (0.25): from TP1 (bottom of VIN_input's left strip, no DC current below
    #     C5.1) down the left edge, along the bottom edge under the sense row, up into R9.1 --------
    tp1, r9 = c("TP1", "1"), c("R9", "1")
    yb2 = 159.2
    T("VIN", W_TAP, walk(tp1, ("v", yb2 - 0.8), ("dy", yb2, +1), ("h", r9[0] - 0.8), ("dx", r9[0], -1), ("v", r9[1])))

    # --- VOUT Kelvin tap to R7.1 (0.25): from C7.1 through TP4, out of the TP4 lobe bottom,
    #     over R11 (0.33 mm), down x 156.3 (over both LSW hops), under the NUCLEO at y 145,
    #     round the left end of J6, into R7.1 along its axis ---------------------------------------
    c7, tp4, r7 = c("C7", "1"), c("TP4", "1"), c("R7", "1")
    yk, xk, yr = 117.125, 156.3, 145.0
    kel = walk(c7, ("v", tp4[1] - (tp4[0] - c7[0])), ("dx", tp4[0], +1), ("v", yk - 0.4), ("dx", tp4[0] - 0.4, +1),
               ("h", xk + 0.4), ("dx", xk, +1), ("v", yr - 0.8), ("dx", xk - 0.8, +1), ("h", 106.3),
               ("dx", 105.5, +1), ("v", r7[1] - 0.8), ("dy", r7[1], +1), ("h", r7[0]))
    T("VOUT", W_TAP, kel)
    return kel


def kelvin_report(b, kel):
    """Length of the Kelvin tap outside VOUT copper and its distance to SW / VMID copper and the
    inductor bodies (12.5 x 12.5 mm, centred on L1 / L2)."""
    pts = [(TMM(x), TMM(y)) for x, y in kel]
    vz = [z for z in all_zones(b) if z.GetNetname() == "VOUT"][0]
    def inside_vout(p):
        return vz.HitTestFilledArea(F_CU, pcbnew.VECTOR2I(nm(p[0]), nm(p[1])))
    samples = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(2, int(math.hypot(x1 - x0, y1 - y0) / 0.02))
        samples += [(x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n) for k in range(n)]
    outside = [p for p in samples if not inside_vout(p)]
    total = sum(math.hypot(x1 - x0, y1 - y0) for (x0, y0), (x1, y1) in zip(pts, pts[1:]))
    out_len = total * len(outside) / len(samples)
    def box_d(p, cx, cy, h=6.25):
        dx, dy = max(abs(p[0] - cx) - h, 0), max(abs(p[1] - cy) - h, 0)
        return math.hypot(dx, dy)
    l1 = b.FindFootprintByReference("L1").GetPosition(); l2 = b.FindFootprintByReference("L2").GetPosition()
    dl = min(min(box_d(p, TMM(l1.x), TMM(l1.y)), box_d(p, TMM(l2.x), TMM(l2.y))) for p in outside) - W_TAP / 2
    def copper_d(net):
        best = 1e9
        for z in all_zones(b):
            if z.GetNetname() == net:
                for p in outside[::5]:
                    best = min(best, math.sqrt(z.GetFilledPolysList(F_CU).SquaredDistance(pcbnew.VECTOR2I(nm(p[0]), nm(p[1])))) / 1e6)
        for t in b.GetTracks():
            if t.GetNetname() == net and t.GetClass() == "PCB_TRACK" and t.GetLayer() == F_CU:
                s, e = (TMM(t.GetStart().x), TMM(t.GetStart().y)), (TMM(t.GetEnd().x), TMM(t.GetEnd().y))
                for p in outside[::5]:
                    best = min(best, seg_dist(p, p, s, e) - TMM(t.GetWidth()) / 2)
        return best - W_TAP / 2
    print(f"\nKelvin tap: total {total:.1f} mm, {out_len:.1f} mm outside VOUT copper; edge-to-edge minimum "
          f"distance to inductor bodies {dl:.2f} mm, SW copper {copper_d('SW'):.2f} mm, VMID copper {copper_d('VMID'):.2f} mm")


# ----------------------------------------------------------------------------------------------
# Stage S4: GND pours, local solid GND for the output caps, return / stitching vias
# ----------------------------------------------------------------------------------------------
GV_D, GV_DRILL = 0.8, 0.4          # return / stitching vias
SV_D, SV_DRILL = 0.6, 0.3          # small GND vias (signal-area returns)
# Reviewer-verified positions (S3 geometry); re-checked here, nudged minimally if they now conflict.
REVIEWED_VIAS = [
    ("hot-loop GND", GV_D, [(112.8, 102.4), (115.4, 102.4), (118.0, 102.4), (121.0, 102.9), (123.0, 102.9), (124.5, 103.0)]),
    ("output-cap pocket", GV_D, [(164.6, 104.5), (164.6, 107.5), (164.6, 110.5), (166.6, 106.0), (166.6, 109.0)]),
    ("Q6/Q7 sources", SV_D, [(163.06, 121.2), (162.0, 121.2), (163.06, 133.7), (162.0, 133.7)]),
    ("right-hand area", SV_D, [(166.0, 125.0), (166.0, 138.0), (160.0, 140.0), (160.0, 152.0), (170.0, 152.0)]),
    ("driver GND", SV_D, [(118.25, 123.3), (119.5, 121.6), (113.3, 125.1), (112.0, 124.0)]),
    ("stitching by TP7 (reviewer S4 fix)", GV_D, [(137.30, 115.20)]),
    ("sense / NUCLEO GND", SV_D, [(116.66, 158.1), (118.9, 158.1), (121.2, 158.1), (123.3, 157.6),
                                 (135.44, 140.5), (140.52, 148.8), (125.0, 148.0), (110.0, 148.0)]),
]
DRILL_OF = {GV_D: GV_DRILL, SV_D: SV_DRILL}


def gnd_zone(b, name, layer, prio, pts, conn, gap, spoke, islands=pcbnew.ISLAND_REMOVAL_MODE_ALWAYS):
    z = zone(b, name, "GND", prio, pts)
    z.SetLayer(layer)
    z.SetPadConnection(conn)
    z.SetThermalReliefGap(FMM(gap)); z.SetThermalReliefSpokeWidth(FMM(spoke))
    z.SetIslandRemovalMode(islands)
    return z


def build_s4_zones(b, zlog, islands):
    ex0, ey0, ex1, ey1 = board_rect(b)
    rect = [(ex0 + EDGE, ey0 + EDGE), (ex1 - EDGE, ey0 + EDGE), (ex1 - EDGE, ey1 - EDGE), (ex0 + EDGE, ey1 - EDGE)]
    # Global pours (priority 0). F.Cu: thermal on EVERY pad, so the small SMD GND pads are not solid
    # (tombstoning); gap 0.3 so 0603 / SOT-23 pads still resolve >= 2 spokes. B.Cu: THT pads + vias.
    zf = gnd_zone(b, "GND_F", F_CU, 0, rect, pcbnew.ZONE_CONNECTION_THERMAL, 0.3, 0.6, islands)
    # Notch: GND_hotloop (solid, priority 3) owns its pads; GND_F stops 0.1 mm inside its outline so the
    # two same-net fills still overlap, but GND_F no longer tries (starved) thermals on D1.2 / C1-C4.2.
    hot = [z for z in all_zones(b) if z.GetZoneName() == "GND_hotloop"][0]
    hp = [(x, (y - 0.6) if abs(y - (ey0 + EDGE)) < 1e-6 else y) for x, y in poly_pts(hot.Outline())]
    notch = pcbnew.SHAPE_POLY_SET(); notch.NewOutline()
    for x, y in hp:
        notch.Append(FMM(x), FMM(y))
    notch.Deflate(FMM(0.1), pcbnew.CORNER_STRATEGY_CHAMFER_ALL_CORNERS, FMM(0.005))
    # ...and keep every pad that GND_hotloop owns >= gap + spoke (0.9 mm) inside the notch, so GND_F never
    # builds a (starved) thermal on it (D1.2 sits only 0.15 mm inside the hot-loop outline).
    for fp in b.GetFootprints():
        for pd in fp.Pads():
            if pd.GetNetname() == "GND" and not pd.HasHole() and hot.Outline().Contains(pd.GetPosition()):
                ps = pcbnew.SHAPE_POLY_SET()
                pd.TransformShapeToPolygon(ps, F_CU, FMM(0.9), FMM(0.005), pcbnew.ERROR_OUTSIDE)
                notch.BooleanAdd(ps)
    notch.Simplify()
    newo = pcbnew.SHAPE_POLY_SET(zf.Outline()); newo.BooleanSubtract(notch); newo.Simplify()
    zf.Outline().RemoveAllContours(); zf.Outline().Append(newo)
    gnd_zone(b, "GND_B", pcbnew.B_Cu, 0, rect, pcbnew.ZONE_CONNECTION_THERMAL, 0.5, 0.6, islands)
    # Output-cap GND pocket (priority 1): C6.2-C8.2 solid (SMD), J2.2 / TP8 thermal (THT).
    oc = [(162.10, 103.30), (170.35, 103.30), (170.35, 112.90), (162.10, 112.90)]
    gnd_zone(b, "GND_outcaps", F_CU, 1, oc, pcbnew.ZONE_CONNECTION_THT_THERMAL, 0.5, 0.6, islands)
    for name, prio, pts in (("GND_F", 0, rect), ("GND_B", 0, rect), ("GND_outcaps", 1, oc)):
        zlog.append((name, "GND", prio, pts))


def gnd_fill(b, layer):
    s = pcbnew.SHAPE_POLY_SET()
    for z in all_zones(b):
        if z.GetNetname() == "GND" and z.IsOnLayer(layer) and z.HasFilledPolysForLayer(layer):
            f = pcbnew.SHAPE_POLY_SET(z.GetFilledPolysList(layer)); f.Unfracture(); s.BooleanAdd(f)
    s.Simplify()
    return s


def _deflated(s, r):
    d = pcbnew.SHAPE_POLY_SET(s)
    d.Deflate(FMM(r), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, FMM(0.005))
    d.BuildBBoxCaches()
    return d


class ViaPlanner:
    """A GND via of diameter D at p is accepted only if it sits inside the F.Cu AND B.Cu GND copper by
    >= D/2 + 0.02 mm (so >= 0.32 mm from foreign copper, since the fill already keeps 0.3 mm), is
    >= 1 mm edge-to-edge from SW copper, keeps 0.5 mm hole-to-hole to other vias and THT holes."""
    def __init__(self, b):
        self.f, self.bk = gnd_fill(b, F_CU), gnd_fill(b, pcbnew.B_Cu)
        self.ok_f = {D: _deflated(self.f, D / 2 + 0.02) for D in (GV_D, SV_D)}
        self.ok_b = {D: _deflated(self.bk, D / 2 + 0.02) for D in (GV_D, SV_D)}
        sw = pcbnew.SHAPE_POLY_SET()
        for z in all_zones(b):
            if z.GetNetname() == "SW":
                f = pcbnew.SHAPE_POLY_SET(z.GetFilledPolysList(F_CU)); f.Unfracture(); sw.BooleanAdd(f)
        for t in b.GetTracks():
            if t.GetNetname() == "SW" and t.GetClass() == "PCB_TRACK":
                t.TransformShapeToPolygon(sw, t.GetLayer(), 0, FMM(0.005), pcbnew.ERROR_OUTSIDE)
        for fp in b.GetFootprints():                    # SW pads too (TP2 sticks out of the track)
            for pd in fp.Pads():
                if pd.GetNetname() == "SW":
                    pd.TransformShapeToPolygon(sw, F_CU, 0, FMM(0.005), pcbnew.ERROR_OUTSIDE)
        sw.Simplify()
        self.sw = {D: None for D in (GV_D, SV_D)}
        for D in self.sw:
            s = pcbnew.SHAPE_POLY_SET(sw); s.Inflate(FMM(1.0 + D / 2), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, FMM(0.005))
            s.BuildBBoxCaches(); self.sw[D] = s
        self.holes = [(TMM(p.GetPosition().x), TMM(p.GetPosition().y), TMM(p.GetDrillSize().x) / 2)
                      for fp in b.GetFootprints() for p in fp.Pads() if p.HasHole()]
        self.vias = [(TMM(v.GetPosition().x), TMM(v.GetPosition().y), TMM(v.GetDrillValue()) / 2)
                     for v in b.GetTracks() if v.GetClass() == "PCB_VIA"]
        self.placed = {}

    def ok(self, p, D):
        r = DRILL_OF[D] / 2
        if any(math.dist(p, (x, y)) < r + hr + 0.5 for x, y, hr in self.vias):
            return False
        if any(math.dist(p, (x, y)) < r + hr + 0.5 for x, y, hr in self.holes):
            return False
        v = pcbnew.VECTOR2I(nm(p[0]), nm(p[1]))
        return (self.ok_f[D].Contains(v, -1, 0, True) and self.ok_b[D].Contains(v, -1, 0, True)
                and not self.sw[D].Contains(v, -1, 0, True))

    def add(self, group, p, D):
        self.vias.append((p[0], p[1], DRILL_OF[D] / 2)); self.placed.setdefault(group, []).append((p, D))

    def nudge(self, p, D, rmax=1.0, step=0.05):
        if self.ok(p, D):
            return p
        k = int(rmax / step)
        cands = sorted(((math.hypot(i, j) * step, (round(p[0] + i * step, 3), round(p[1] + j * step, 3)))
                        for i in range(-k, k + 1) for j in range(-k, k + 1)), key=lambda q: q[0])
        for d, q in cands:
            if 0 < d <= rmax and self.ok(q, D):
                return q
        return None

    def near(self, group, centre, n, rmax, D, spacing=1.6, step=0.25):
        k = int(rmax / step)
        cands = sorted((math.hypot(i, j) * step, (round(centre[0] + i * step, 3), round(centre[1] + j * step, 3)))
                       for i in range(-k, k + 1) for j in range(-k, k + 1) if math.hypot(i, j) * step <= rmax)
        got = 0
        for d, p in cands:
            if got >= n:
                break
            if all(math.dist(p, q) >= spacing for q, _ in self.placed.get(group, [])) and self.ok(p, D):
                self.add(group, p, D); got += 1
        return got

    def grid(self, group, box, pitch, D):
        x0, y0, x1, y1 = box
        nx, ny = max(0, int((x1 - x0) / pitch)), max(0, int((y1 - y0) / pitch))
        for j in range(ny + 1):
            for i in range(nx + 1):
                p = (x0 + i * pitch, y0 + j * pitch)
                if any(math.dist(p, (x, y)) < pitch * 0.7 for x, y, _ in self.vias):
                    continue                                # already covered by a nearby via
                for dx, dy in ((0, 0), (0.6, 0), (-0.6, 0), (0, 0.6), (0, -0.6), (1.2, 0), (-1.2, 0), (0, 1.2), (0, -1.2)):
                    q = (round(p[0] + dx, 3), round(p[1] + dy, 3))
                    if self.ok(q, D):
                        self.add(group, q, D); break


def fill_pieces(b, layer, min_area=0.0):
    """Connected pieces of GND copper on a layer: (area mm2, GND pads touched, GND vias inside, bbox, piece)."""
    s = gnd_fill(b, layer)
    pads = []
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname() == "GND" and p.IsOnLayer(layer):
                ps = pcbnew.SHAPE_POLY_SET(); p.TransformShapeToPolygon(ps, layer, FMM(0.01), FMM(0.005), pcbnew.ERROR_OUTSIDE)
                bb = p.GetBoundingBox()
                pads.append((f"{fp.GetReference()}.{p.GetNumber()}", ps, (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom())))
    vias = [v.GetPosition() for v in b.GetTracks() if v.GetClass() == "PCB_VIA" and v.GetNetname() == "GND"]
    out = []
    for k in range(s.OutlineCount()):
        area = abs(s.Outline(k).Area()) / 1e12
        if area < min_area:
            continue
        piece = pcbnew.SHAPE_POLY_SET(); piece.AddOutline(s.Outline(k))
        for h in range(s.HoleCount(k)):
            piece.AddHole(s.Hole(k, h))
        piece.BuildBBoxCaches()
        pb = s.Outline(k).BBox()
        X0, Y0, X1, Y1 = pb.GetLeft(), pb.GetTop(), pb.GetRight(), pb.GetBottom()
        touched = []
        for name, ps, (a0, b0, a1, b1) in pads:
            if a1 < X0 or a0 > X1 or b1 < Y0 or b0 > Y1:
                continue
            q = pcbnew.SHAPE_POLY_SET(ps); q.BooleanIntersection(piece)
            if q.OutlineCount():
                touched.append(name)
        nv = sum(1 for v in vias if X0 <= v.x <= X1 and Y0 <= v.y <= Y1 and piece.Contains(v, -1, 0, True))
        out.append((area, touched, nv, (TMM(X0), TMM(Y0), TMM(X1), TMM(Y1)), piece))
    return out


def build_s4_vias(b, tlog):
    import time
    t0 = time.time()
    vp = ViaPlanner(b)
    log = {}
    for group, D, pts in REVIEWED_VIAS:
        for p in pts:
            q = vp.nudge(p, D)
            if q is None:
                log.setdefault("reviewer via rejected (no valid spot within 1 mm)", []).append((group, p))
                continue
            if q != p:
                log.setdefault("reviewer via moved", []).append((group, p, q, round(math.dist(p, q), 2)))
            vp.add(group, q, D)
    print(f"  [s4] reviewer vias placed ({time.time() - t0:.1f} s)", flush=True)
    c = lambda ref, num: (PadInfo(b, ref, num).x, PadInfo(b, ref, num).y)
    vp.near("J1.2 / C5.2 return", c("J1", "2"), 3, 4.5, GV_D)
    vp.near("J1.2 / C5.2 return", c("C5", "2"), 2, 3.5, GV_D)
    vp.near("J2.2 return", c("J2", "2"), 4, 5.5, GV_D)
    print(f"  [s4] return vias placed ({time.time() - t0:.1f} s)", flush=True)
    ex0, ey0, ex1, ey1 = board_rect(b)
    vp.grid("stitching: power stage (~5 mm)", (ex0 + 1.5, ey0 + 1.5, ex1 - 1.5, 128.0), 5.0, GV_D)
    for box in ((ex0 + 1.2, ey1 - 1.2, ex1 - 1.2, ey1 - 1.2), (ex0 + 1.2, 128.0, ex0 + 1.2, ey1 - 1.2),
                (ex1 - 1.2, 128.0, ex1 - 1.2, ey1 - 1.2)):
        vp.grid("stitching: board edges (~5 mm)", box, 5.0, GV_D)
    vp.grid("stitching: rest of board (~8 mm)", (ex0 + 2, 128.0, ex1 - 2, ey1 - 2), 8.0, GV_D)
    print(f"  [s4] stitching placed ({time.time() - t0:.1f} s)", flush=True)
    # every F.Cu GND piece >= 1 mm2 gets >= 2 vias if there is room (pieces < 1 mm2 / without room are islands)
    pend = []
    for area, touched, nv, bbx, piece in fill_pieces(b, F_CU, 1.0):
        own = sum(1 for (p, _) in [x for g in vp.placed.values() for x in g]
                  if piece.Contains(pcbnew.VECTOR2I(nm(p[0]), nm(p[1])), -1, 0, True))
        if own >= 2 or touched:                      # pieces touching a GND pad are not islands
            continue
        need, cands = 2 - own, []
        step = 0.25
        x = bbx[0]
        while x <= bbx[2]:
            y = bbx[1]
            while y <= bbx[3]:
                if piece.Contains(pcbnew.VECTOR2I(nm(x), nm(y)), -1, 0, True):
                    cands.append((round(x, 3), round(y, 3)))
                y += step
            x += step
        cx, cy = (bbx[0] + bbx[2]) / 2, (bbx[1] + bbx[3]) / 2
        chosen = []                                  # all-or-nothing: a 1-via sliver is removed instead
        for p in sorted(cands, key=lambda q: math.dist(q, (cx, cy))):
            if len(chosen) >= need:
                break
            for D in (GV_D, SV_D):
                if all(math.dist(p, q) >= 1.5 for q, _ in chosen) and vp.ok(p, D) and                         all(math.dist(p, q) >= DRILL_OF[D] / 2 + DRILL_OF[E] / 2 + 0.5 for q, E in chosen):
                    chosen.append((p, D)); break
        if len(chosen) >= need:
            for p, D in chosen:
                vp.add("island ties", p, D)
        else:
            pend.append((round(area, 2), [round(v, 1) for v in bbx], touched))
    if pend:
        log["F.Cu GND pieces >= 1 mm2 without room for 2 vias (left to island removal)"] = pend
    print(f"  [s4] island ties done ({time.time() - t0:.1f} s)", flush=True)
    for group, pts in vp.placed.items():
        for p, D in pts:
            via(b, "GND", p[0], p[1], D, DRILL_OF[D])
        tlog.append(("GND", f"{len(pts)} vias", group, [(round(p[0], 2), round(p[1], 2), D) for p, D in pts]))
    return vp.placed, log


def s4_report(b, placed, vlog, orphans):
    print()
    print("=== S4 GND ===")
    n = {GV_D: 0, SV_D: 0}
    for g, pts in placed.items():
        for _, D in pts:
            n[D] += 1
        print(f"  vias [{g}]: {len(pts)}  " + " ".join(f"({p[0]:.2f},{p[1]:.2f}){'' if D == GV_D else '*'}" for p, D in pts))
    print(f"  GND vias total {sum(n.values())}: {n[GV_D]} x {GV_D}/{GV_DRILL}, {n[SV_D]} x {SV_D}/{SV_DRILL} (* = 0.6/0.3)")
    for k, v in vlog.items():
        print(f"  NOTE {k}: {v}")
    print("  would-be islands before removal (no GND pad / via):", orphans)
    for L in (F_CU, pcbnew.B_Cu):
        pcs = fill_pieces(b, L)
        print(f"  {pcbnew.LayerName(L)} GND copper after final fill: {len(pcs)} piece(s); "
              + "; ".join(f"{a:.1f} mm2 bbox {[round(v, 1) for v in bb]} pads {len(t)} vias {nv}" for a, t, nv, bb, _ in sorted(pcs, key=lambda q: -q[0])))
    rows = []
    fills = {L: gnd_fill(b, L) for L in (F_CU, pcbnew.B_Cu)}
    zones = [z for z in all_zones(b) if z.GetNetname() == "GND"]
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname() != "GND":
                continue
            for L in (F_CU, pcbnew.B_Cu):
                if not p.IsOnLayer(L):
                    continue
                zs = [z for z in zones if z.IsOnLayer(L) and z.Outline().Contains(p.GetPosition())]
                if not zs:
                    continue
                if any(z.GetPadConnection() == pcbnew.ZONE_CONNECTION_FULL or
                       (z.GetPadConnection() == pcbnew.ZONE_CONNECTION_THT_THERMAL and not p.HasHole()) for z in zs):
                    rows.append(f"{fp.GetReference()}.{p.GetNumber()}/{pcbnew.LayerName(L)[0]} solid"); continue
                gap = min(TMM(z.GetThermalReliefGap()) for z in zs)
                outer, inner = pcbnew.SHAPE_POLY_SET(), pcbnew.SHAPE_POLY_SET()
                p.TransformShapeToPolygon(outer, L, FMM(gap - 0.05), FMM(0.002), pcbnew.ERROR_INSIDE)
                p.TransformShapeToPolygon(inner, L, FMM(0.05), FMM(0.002), pcbnew.ERROR_OUTSIDE)
                outer.BooleanSubtract(inner)
                outer.BooleanIntersection(fills[L])
                k = sum(1 for i in range(outer.OutlineCount()) if abs(outer.Outline(i).Area()) > FMM(0.05) ** 2)
                rows.append(f"{fp.GetReference()}.{p.GetNumber()}/{pcbnew.LayerName(L)[0]} {k}sp")
    print("  GND pad connections (layer, spokes):", ", ".join(sorted(rows)))


# ----------------------------------------------------------------------------------------------
# Stage S5: silkscreen (text and graphics only; footprints and copper untouched)
# ----------------------------------------------------------------------------------------------
REF_H, REF_T = 1.0, 0.18
LAB_H, LAB_T = 1.2, 0.20
TIT_H, TIT_T = 1.5, 0.25
NUCLEO_BOX = (102.10, 135.35, 152.36, 153.89)
TP_NAMES = {"TP1": "VIN", "TP2": "SW", "TP3": "GATE", "TP4": "VOUT", "TP5": "PWM", "TP6": "GND",
            "TP7": "GND", "TP8": "GND", "TP9": "BOOT", "TP10": "TRIG"}
CONN_LABELS = {("J1", "1"): "+12V", ("J1", "2"): "GND", ("J2", "1"): "VOUT", ("J2", "2"): "GND",
               ("J3", "1"): "VOUT", ("J3", "2"): "36R", ("J4", "1"): "VOUT", ("J4", "2"): "24R"}
S5_KEEP_TEXTS = {"D1", "D1/TX", "VIN", "USB ->"}  # owner's existing board silk (kept, not regenerated)


def _poly_bbox(s):
    bb = s.BBox()
    return (TMM(bb.GetLeft()), TMM(bb.GetTop()), TMM(bb.GetRight()), TMM(bb.GetBottom()))


class SilkPlacer:
    """Collision model for one silk layer. Hard obstacles: exposed copper (pads +0.2 mm), silk already on
    the layer (+0.12 mm), part bodies (F.Fab outlines / inductor boxes / NUCLEO outline, F side only),
    board edge (-0.5 mm). Soft: tented vias (+0.1 mm), avoided if possible."""
    CELL = 2.0

    def __init__(self, b, layer):
        self.b, self.layer = b, layer
        cu = F_CU if layer == pcbnew.F_SilkS else pcbnew.B_Cu
        ex0, ey0, ex1, ey1 = board_rect(b)
        self.inside = (ex0 + 0.5, ey0 + 0.5, ex1 - 0.5, ey1 - 0.5)
        self.grid = {}
        for fp in b.GetFootprints():
            for p in fp.Pads():
                if p.IsOnLayer(cu) and (p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD or cu == F_CU) and p.IsOnCopperLayer():
                    s = pcbnew.SHAPE_POLY_SET(); p.TransformShapeToPolygon(s, cu, FMM(0.2), FMM(0.01), pcbnew.ERROR_OUTSIDE)
                    self._add(s, "pad", f"{fp.GetReference()}.{p.GetNumber()}")
            if layer == pcbnew.F_SilkS:
                for g in fp.GraphicalItems():
                    if g.GetLayer() == layer and g.GetClass() == "PCB_SHAPE":
                        s = pcbnew.SHAPE_POLY_SET(); g.TransformShapeToPolygon(s, layer, FMM(0.12), FMM(0.01), pcbnew.ERROR_OUTSIDE)
                        self._add(s, "silk", fp.GetReference())
                for bx in self._bodies(fp):
                    self._add(self._rect(*bx), "body", fp.GetReference())
        if layer == pcbnew.F_SilkS:
            self._add(self._rect(*NUCLEO_BOX), "body", "NUCLEO")
        for d in b.GetDrawings():
            if d.GetLayer() == layer:
                s = pcbnew.SHAPE_POLY_SET(); d.TransformShapeToPolygon(s, layer, FMM(0.12), FMM(0.01), pcbnew.ERROR_OUTSIDE)
                self._add(s, "silk", "board")
        for v in b.GetTracks():
            if v.GetClass() == "PCB_VIA":
                s = pcbnew.SHAPE_POLY_SET(); v.TransformShapeToPolygon(s, cu, FMM(0.1), FMM(0.01), pcbnew.ERROR_OUTSIDE)
                self._add(s, "via", v.GetNetname())

    @staticmethod
    def _rect(x0, y0, x1, y1):
        s = pcbnew.SHAPE_POLY_SET(); s.NewOutline()
        for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            s.Append(FMM(x), FMM(y))
        return s

    @staticmethod
    def _bodies(fp):
        ref = fp.GetReference()
        if ref.startswith("TP"):
            return []
        if ref in ("L1", "L2"):
            x, y = TMM(fp.GetPosition().x), TMM(fp.GetPosition().y)
            return [(x - 6.25, y - 6.25, x + 6.25, y + 6.25)]
        xs, ys = [], []
        for g in fp.GraphicalItems():
            if g.GetLayer() == pcbnew.F_Fab and g.GetClass() == "PCB_SHAPE":
                bb = g.GetBoundingBox()
                xs += [TMM(bb.GetLeft()), TMM(bb.GetRight())]; ys += [TMM(bb.GetTop()), TMM(bb.GetBottom())]
        return [(min(xs), min(ys), max(xs), max(ys))] if xs else []

    def _cells(self, bb):
        c = self.CELL
        for i in range(int(bb[0] // c), int(bb[2] // c) + 1):
            for j in range(int(bb[1] // c), int(bb[3] // c) + 1):
                yield (i, j)

    def _add(self, s, kind, owner):
        bb = _poly_bbox(s)
        for k in self._cells(bb):
            self.grid.setdefault(k, []).append((bb, s, kind, owner))

    def hits(self, s, bb):
        """(hard collisions, soft via collisions) for a text polygon s with bbox bb."""
        hard, soft, seen = [], 0, set()
        if bb[0] < self.inside[0] or bb[1] < self.inside[1] or bb[2] > self.inside[2] or bb[3] > self.inside[3]:
            return ["edge"], 0
        for k in self._cells(bb):
            for ob in self.grid.get(k, []):
                if id(ob) in seen:
                    continue
                seen.add(id(ob))
                obb, os_, kind, owner = ob
                if obb[2] < bb[0] or obb[0] > bb[2] or obb[3] < bb[1] or obb[1] > bb[3]:
                    continue
                q = pcbnew.SHAPE_POLY_SET(s); q.BooleanIntersection(os_)
                if q.OutlineCount():
                    if kind == "via":
                        soft += 1
                    else:
                        hard.append(f"{kind}:{owner}")
        return hard, soft

    def text_poly(self, item):
        s = pcbnew.SHAPE_POLY_SET()
        item.TransformShapeToPolygon(s, self.layer, 0, FMM(0.01), pcbnew.ERROR_OUTSIDE)
        s.Simplify()
        return s

    TEXT_GAP = 0.35                                   # min gap between placed texts (readability)

    def _grow(self, s):
        g = pcbnew.SHAPE_POLY_SET(s)
        g.Inflate(FMM(self.TEXT_GAP), pcbnew.CORNER_STRATEGY_CHAMFER_ALL_CORNERS, FMM(0.01))
        return g

    def set_extents(self, ext):
        """ext: {ref: (x0, y0, x1, y1)} part extents (pads + body) used for the ambiguity test."""
        self.ext = ext

    @staticmethod
    def _bdist(p, bx):
        return math.hypot(max(bx[0] - p[0], 0, p[0] - bx[2]), max(bx[1] - p[1], 0, p[1] - bx[3]))

    def _unambiguous(self, centre, owner):
        if not owner or owner not in getattr(self, "ext", {}):
            return True
        d_own = self._bdist(centre, self.ext[owner])
        # test points are labelled by signal name, not reference, so they cannot be confused with a part
        return all(d_own <= self._bdist(centre, bx) + 0.01 for r, bx in self.ext.items()
                   if r != owner and (owner.startswith("TP") or not r.startswith("TP")))

    def place(self, item, target, radius=3.0, angles=(0, 90), step=0.125, around=None, owner=None):
        """Put the text at the free spot closest to `target` (or to the box `around`, measured from its
        edge), 0 deg before 90 deg. Passes: (unambiguous, via-free) -> (unambiguous) -> (any)."""
        passes = ((True, False), (True, True), (False, True)) if owner else ((False, False), (False, True))
        half = max(around[2] - around[0], around[3] - around[1]) / 2 if around else 0.0
        k = int((radius + half) / step)                  # grid reaches `radius` beyond the box edge
        for need_unamb, allow_via in passes:
            best = None
            for ang in angles:
                item.SetTextAngleDegrees(ang)
                item.SetPosition(pcbnew.VECTOR2I(nm(target[0]), nm(target[1])))
                base = self.text_poly(item)
                cands = []
                for i in range(-k, k + 1):
                    for j in range(-k, k + 1):
                        dx, dy = i * step, j * step
                        cx, cy = target[0] + dx, target[1] + dy
                        d = self._bdist((cx, cy), around) if around else math.hypot(dx, dy)
                        if d <= radius:
                            cands.append((d + (0.3 if ang else 0.0), dx, dy))
                for d, dx, dy in sorted(cands):
                    if best is not None and d >= best[0]:
                        break
                    if need_unamb and not self._unambiguous((target[0] + dx, target[1] + dy), owner):
                        continue
                    s = pcbnew.SHAPE_POLY_SET(base); s.Move(pcbnew.VECTOR2I(nm(dx), nm(dy)))
                    hard, soft = self.hits(s, _poly_bbox(s))
                    if not hard and (allow_via or soft == 0):
                        best = (d, ang, dx, dy, soft)
                        break
            if best:
                d, ang, dx, dy, soft = best
                item.SetTextAngleDegrees(ang)
                item.SetPosition(pcbnew.VECTOR2I(nm(target[0] + dx), nm(target[1] + dy)))
                self._add(self._grow(self.text_poly(item)), "silk", "text")
                return (round(target[0] + dx, 2), round(target[1] + dy, 2), ang, round(d, 2), soft,
                        "ok" if need_unamb or not owner else "AMBIGUOUS")
        return None

    def put(self, item, x, y, ang=0):
        """Fixed position (hand layout); registers it and reports any hard collision."""
        item.SetTextAngleDegrees(ang); item.SetPosition(pcbnew.VECTOR2I(nm(x), nm(y)))
        s = self.text_poly(item)
        hard, soft = self.hits(s, _poly_bbox(s))
        self._add(self._grow(s), "silk", "text")
        return (x, y, ang, "fixed", soft, ("HITS " + ",".join(hard)) if hard else "ok")


def fp_pad_box(fp):
    xs, ys = [], []
    for p in fp.Pads():
        bb = p.GetBoundingBox()
        xs += [TMM(bb.GetLeft()), TMM(bb.GetRight())]; ys += [TMM(bb.GetTop()), TMM(bb.GetBottom())]
    return (min(xs), min(ys), max(xs), max(ys))


def board_text(b, s, layer, h, t, mirror=False):
    x = pcbnew.PCB_TEXT(b)
    x.SetText(s); x.SetLayer(layer)
    x.SetTextSize(pcbnew.VECTOR2I(FMM(h), FMM(h))); x.SetTextThickness(FMM(t))
    if mirror:
        x.SetMirrored(True)
    b.Add(x)
    return x


def build_s5(b):
    log, fails = [], []
    rec = lambda name, res: (log if res and "HITS" not in str(res[-1]) else fails).append((name, res))
    # 0) drop the board-level silk text generated by a previous run (the owner's texts are kept)
    for d in list(b.GetDrawings()):
        if d.GetClass() == "PCB_TEXT" and (d.GetLayer() == pcbnew.B_SilkS or
                                           (d.GetLayer() == pcbnew.F_SilkS and d.GetText() not in S5_KEEP_TEXTS)):
            b.Delete(d)
    # NUCLEO pin-1 label "D1" by J5 would duplicate the diode's reference: use the NUCLEO's own "D1/TX"
    for d in b.GetDrawings():
        if d.GetClass() == "PCB_TEXT" and d.GetLayer() == pcbnew.F_SilkS and d.GetText() == "D1":
            d.SetText("D1/TX")
    fps = {fp.GetReference(): fp for fp in b.GetFootprints()}
    pin = lambda ref, num: [(TMM(q.GetPosition().x), TMM(q.GetPosition().y)) for q in fps[ref].Pads() if q.GetNumber() == num][0]
    # 1) sizes / layers: references 1.0/0.18 on F.Silkscreen; TP references to F.Fab, TP signal name
    #    (the footprint Value field) visible on F.Silkscreen
    for ref, fp in fps.items():
        r, v = fp.Reference(), fp.Value()
        if ref.startswith("TP"):
            assert v.GetText() == TP_NAMES[ref], (ref, v.GetText())
            r.SetLayer(pcbnew.F_Fab); r.SetTextThickness(FMM(0.15))
            v.SetLayer(pcbnew.F_SilkS); v.SetVisible(True)
            v.SetTextSize(pcbnew.VECTOR2I(FMM(REF_H), FMM(REF_H))); v.SetTextThickness(FMM(REF_T))
        else:
            r.SetLayer(pcbnew.F_SilkS); r.SetVisible(True)
            r.SetTextSize(pcbnew.VECTOR2I(FMM(REF_H), FMM(REF_H))); r.SetTextThickness(FMM(REF_T))
    F = SilkPlacer(b, pcbnew.F_SilkS)
    ext = {}
    for ref, fp in fps.items():
        bx = [fp_pad_box(fp)] + SilkPlacer._bodies(fp)
        ext[ref] = (min(q[0] for q in bx), min(q[1] for q in bx), max(q[2] for q in bx), max(q[3] for q in bx))
    F.set_extents(ext)

    # 2) connectors (hand layout). J2-J4: pin labels in the column left of the block at pin height
    #    (vertical, reads from the right edge), reference just below each block; J1: "+12V" above pin 1,
    #    "GND" right of the block at pin 2, reference above the block's left end.
    lab = lambda s: board_text(b, s, pcbnew.F_SilkS, LAB_H, LAB_T)
    x1, y1 = pin("J1", "1"); x2, y2 = pin("J1", "2")
    j1b = ext["J1"]
    rec("J1.1 '+12V'", F.put(lab("+12V"), x1 + 1.3, j1b[1] - 1.15))
    rec("J1.2 'GND'", F.put(lab("GND"), j1b[2] + 2.5, y2))
    rec("J1", F.put(fps["J1"].Reference(), x1 - 2.7, j1b[1] - 1.15))
    for ref, s2, s1 in (("J2", "GND", "VOUT"), ("J3", "36R", "VOUT"), ("J4", "24R", "VOUT")):
        bx = ext[ref]
        silk_x0 = min(TMM(g.GetBoundingBox().GetLeft()) for g in fps[ref].GraphicalItems()
                      if g.GetLayer() == pcbnew.F_SilkS and g.GetClass() == "PCB_SHAPE")
        xc = round(silk_x0 - 0.85, 2)                                  # column just left of the block silk
        (px1, py1), (px2, py2) = pin(ref, "1"), pin(ref, "2")
        rec(f"{ref}.2 '{s2}'", F.put(lab(s2), xc, py2, 90))
        rec(f"{ref}.1 '{s1}'", F.put(lab(s1), xc, py1, 90))
        rec(ref, F.put(fps[ref].Reference(), px1, bx[3] + 1.25))         # just below the block
    # 3) NUCLEO socket names just outside the NUCLEO outline, title block and input note
    for s, tgt in (("CN3", (107.0, 134.3)), ("CN4", (106.5, 155.0))):
        rec(s, F.place(board_text(b, s, pcbnew.F_SilkS, REF_H, REF_T), tgt, radius=2.0, angles=(0,)))
    # J6 reference next to "CN4" at the left end of the J6 row (away from TP10)
    rec("J6", F.place(fps["J6"].Reference(), (103.7, 155.0), radius=1.0, angles=(0,)))
    for s, h, th, tgt in (("BUCK 12V->6V REV C", TIT_H, TIT_T, (160.0, 155.6)),
                          ("UNAL Manizales - Sistemas Dinamicos y Control 2026", REF_H, REF_T, (155.5, 157.35)),
                          ("12V (MAX 15V)", REF_H, REF_T, (107.5, 129.6)),
                          ("I LIMIT 1.5A", REF_H, REF_T, (107.5, 131.2))):
        rec(s, F.place(board_text(b, s, pcbnew.F_SilkS, h, th), tgt, radius=2.0, angles=(0,)))
    # 4) sense divider row (R7 | R8 C10 C11 R10 | R9): R7 left of R7; the rest packed in part order
    #    on one line below the row (too dense for one-by-one placement)
    r7 = fps["R7"]
    rec("R7", F.put(r7.Reference(), ext["R7"][0] - 1.55, TMM(r7.GetPosition().y)))
    row = ["R8", "C10", "C11", "R10", "R9"]
    yrow = 158.6
    widths = {}
    for ref in row:
        f = fps[ref].Reference(); f.SetTextAngleDegrees(0); f.SetPosition(pcbnew.VECTOR2I(0, 0))
        bb = _poly_bbox(F.text_poly(f)); widths[ref] = bb[2] - bb[0]
    want = [TMM(fps[r].GetPosition().x) for r in row]
    xs, lo = [], ext["R7"][2] + 0.6
    for ref, w in zip(row, want):                                       # left-to-right push
        x = max(w, lo + widths[ref] / 2); xs.append(x); lo = x + widths[ref] / 2 + 0.6
    hi = 128.0                                                          # stay clear of TP10
    for k in range(len(row) - 1, -1, -1):                               # right-to-left pull back
        xs[k] = min(xs[k], hi - widths[row[k]] / 2); hi = xs[k] - widths[row[k]] / 2 - 0.6
    for ref, x in zip(row, xs):
        rec(ref, F.put(fps[ref].Reference(), round(x, 2), yrow))
    # 5) inductors: below their body (clear of TP2/TP7)
    for ref, tgt in (("L1", (141.0, 115.5)), ("L2", (147.5, 115.5))):
        rec(ref, F.place(fps[ref].Reference(), tgt, radius=2.0, angles=(0,), owner=ref))
    # 5b) R4: fixed directly below its own pad (the search otherwise drifts it between Q4 and Q5)
    bx4 = fp_pad_box(fps["R4"])
    rec("R4", F.put(fps["R4"].Reference(), round((bx4[0] + bx4[2]) / 2, 3), round(bx4[3] + 0.98, 3)))
    # 6a) TP3 'GATE' first (its only clear spot is also Q4's best), then references, then other TP names
    def tp_name(ref):
        c = pin(ref, "1")
        rec(f"{ref} '{TP_NAMES[ref]}'", F.place(fps[ref].Value(), c, radius=3.5,
                                                around=(c[0] - 1, c[1] - 1, c[0] + 1, c[1] + 1), owner=ref))
    tp_name("TP3")
    # 6) everything else: densest areas first, nearest unambiguous free spot within ~3 mm
    order = ["Q4", "Q5", "R5", "R6", "Q3", "C9", "D2", "Q2", "R3", "R2", "R1", "Q1", "D1", "C4",
             "C1", "C2", "C3", "C5", "R11", "R13", "Q6", "R12", "R14", "Q7", "C6", "C7", "C8", "J5"]
    done = set(order) | set(row) | {"R4", "R7", "L1", "L2", "J6"}
    order += [r for r in fps if r not in done and not r.startswith(("TP", "J"))]
    for ref in order:
        fp = fps[ref]
        box = fp_pad_box(fp)
        c = ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)
        res = F.place(fp.Reference(), c, radius=3.0, around=box, owner=ref) or \
            F.place(fp.Reference(), c, radius=6.0, around=box, owner=ref)
        rec(ref, res)
    # TP10 'TRIG': vertical, in the strip between R9.1 and TP10 (the side away from the title block;
    # the NUCLEO outline leaves no room above the pad)
    c10 = pin("TP10", "1")
    r91 = [q for q in fps["R9"].Pads() if q.GetNumber() == "1"][0].GetBoundingBox()
    xt = round((TMM(r91.GetRight()) + 0.2 + c10[0] - 1.0 - 0.2) / 2, 3)
    res = F.put(fps["TP10"].Value(), xt, round(c10[1] - 0.2, 3), 90)
    if "HITS" in str(res[-1]):
        fails.append(("TP10 'TRIG' (left strip)", res))
        res = F.place(fps["TP10"].Value(), (132.6, 154.7), radius=1.0, angles=(0,))
    rec("TP10 'TRIG'", res)
    for ref in TP_NAMES:
        if ref not in ("TP3", "TP10"):
            tp_name(ref)
    # 7) B.Silkscreen (mirrored, hand-soldered side): connector labels, TP names, CN3/CN4, USB arrow.
    #    Seen from below the board is flipped left-right, so the arrow to the USB end (+x) reads "<- USB".
    B = SilkPlacer(b, pcbnew.B_SilkS)
    for (ref, num), s in CONN_LABELS.items():
        c = pin(ref, num)
        res = B.place(board_text(b, s, pcbnew.B_SilkS, LAB_H, LAB_T, mirror=True), c, radius=4.0,
                      around=(c[0] - 1.3, c[1] - 1.3, c[0] + 1.3, c[1] + 1.3))
        rec(f"B {ref}.{num} '{s}'", res)
    for ref, name in TP_NAMES.items():
        c = pin(ref, "1")
        res = B.place(board_text(b, name, pcbnew.B_SilkS, REF_H, REF_T, mirror=True), c, radius=3.5,
                      around=(c[0] - 1, c[1] - 1, c[0] + 1, c[1] + 1))
        rec(f"B {ref} '{name}'", res)
    j5r, j6r = pin("J5", "1"), pin("J6", "1")
    for s, tgt, h, t in (("CN3", (j5r[0] + 4.4, j5r[1]), REF_H, REF_T), ("CN4", (j6r[0] + 4.4, j6r[1]), REF_H, REF_T),
                         ("<- USB", (j5r[0] + 6.0, (j5r[1] + j6r[1]) / 2), LAB_H, LAB_T)):
        rec(f"B {s}", B.place(board_text(b, s, pcbnew.B_SilkS, h, t, mirror=True), tgt, radius=3.0, angles=(0,)))
    # C5 polarity on the solder side: "+" beside the square pad 1 (VIN), away from pad 2
    c51 = pin("C5", "1")
    rec("B C5 '+'", B.place(board_text(b, "+", pcbnew.B_SilkS, LAB_H, LAB_T, mirror=True), (c51[0] - 1.7, c51[1]),
                            radius=1.5, angles=(0,)))
    return log, fails


def q1_die(b):
    q1 = b.FindFootprintByReference("Q1")
    body = [g for g in q1.GraphicalItems() if g.GetLayer() == pcbnew.F_Fab and g.GetClass() == "PCB_SHAPE"
            and g.GetShape() == pcbnew.SHAPE_T_POLY]
    bb = body[0].GetBoundingBox()
    return (TMM(bb.GetCenter().x), TMM(bb.GetCenter().y))


def shoelace(pts):
    return abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))) / 2


# ----------------------------------------------------------------------------------------------
# Checks / report
# ----------------------------------------------------------------------------------------------
def poly_pts(sps, i=0):
    ch = sps.Outline(i)
    return [(TMM(ch.CPoint(k).x), TMM(ch.CPoint(k).y)) for k in range(ch.PointCount())]


def seg_dist(p, q, a, b):
    def pt_seg(pt, s0, s1):
        (x, y), (x0, y0), (x1, y1) = pt, s0, s1
        dx, dy = x1 - x0, y1 - y0
        L = dx * dx + dy * dy
        t = 0 if L == 0 else max(0, min(1, ((x - x0) * dx + (y - y0) * dy) / L))
        return math.hypot(x - x0 - t * dx, y - y0 - t * dy)
    def cross(o, a_, b_):
        return (a_[0] - o[0]) * (b_[1] - o[1]) - (a_[1] - o[1]) * (b_[0] - o[0])
    d1, d2, d3, d4 = cross(a, b, p), cross(a, b, q), cross(p, q, a), cross(p, q, b)
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)) and d1 and d2 and d3 and d4:
        return 0.0
    return min(pt_seg(p, a, b), pt_seg(q, a, b), pt_seg(a, p, q), pt_seg(b, p, q))


def inside(pt, poly):
    x, y = pt; c = False
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            c = not c
    return c


def poly_dist(A, B):
    if any(inside(p, B) for p in A) or any(inside(p, A) for p in B):
        return 0.0
    ea, eb = list(zip(A, A[1:] + A[:1])), list(zip(B, B[1:] + B[:1]))
    return min(seg_dist(p, q, a, b) for p, q in ea for a, b in eb)


def check_outlines(b, names=None):
    """Distance from every zone OUTLINE to foreign-net copper (pads, tracks, other zones' outlines).
    Anything under G means the fill will be knocked out there (or the outline was drawn tight)."""
    pads = []
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if not p.IsOnLayer(F_CU) or p.GetNetCode() <= 0:
                continue
            s = pcbnew.SHAPE_POLY_SET()
            p.TransformShapeToPolygon(s, F_CU, 0, FMM(0.002), pcbnew.ERROR_INSIDE)
            pads.append((f"{fp.GetReference()}.{p.GetNumber()}", p.GetNetname(), poly_pts(s)))
    zones = [(z.GetZoneName(), z.GetNetname(), poly_pts(z.Outline())) for z in all_zones(b)
             if names is None or z.GetZoneName() in names]
    tracks = [(t.GetNetname(), (TMM(t.GetStart().x), TMM(t.GetStart().y)), (TMM(t.GetEnd().x), TMM(t.GetEnd().y)),
               TMM(t.GetWidth())) for t in b.GetTracks() if t.GetClass() == "PCB_TRACK" and t.GetLayer() == F_CU]
    print("\nZone outline -> nearest foreign copper (flag < %.2f mm):" % G)
    for name, net, poly in zones:
        near = []
        for pn, pnet, pp in pads:
            if pnet != net:
                near.append((poly_dist(poly, pp), pn))
        for zn, znet, zp in zones:
            if znet != net:
                near.append((poly_dist(poly, zp), "zone " + zn))
        for tnet, s, e, w in tracks:
            if tnet != net:
                ea = list(zip(poly, poly[1:] + poly[:1]))
                dd = 0.0 if inside(s, poly) or inside(e, poly) else min(seg_dist(s, e, a, c) for a, c in ea)
                near.append((max(0.0, dd - w / 2), f"track {tnet}"))
        near.sort()
        tight = [f"{n} {dd:.3f}" for dd, n in near if dd < G - 1e-6]
        print(f"  {name:12} nearest: " + ", ".join(f"{n} {dd:.3f}" for dd, n in near[:3])
              + (f"   UNDER {G}: {tight}" if tight else ""))


# Pads that the main copper of each zone must join ("terminals" for the width test).
MAIN_PADS = {
    "GND_hotloop": [("C1", "2"), ("C2", "2"), ("C3", "2"), ("C4", "2"), ("D1", "2")],
    "VIN_input": [("J1", "1"), ("C1", "1"), ("C2", "1"), ("C3", "1"), ("C4", "1"), ("Q1", "2"), ("C5", "1"), ("TP1", "1")],
    "SW_node": [("D1", "1"), ("Q1", "3"), ("L1", "2")],
    "VMID": [("L1", "1"), ("L2", "1")],
    "VOUT_bus": [("L2", "2"), ("C6", "1"), ("C7", "1"), ("C8", "1"), ("TP4", "1"), ("J2", "1"), ("J3", "1"), ("J4", "1")],
}


def corridor(b, z):
    """Fill + the zone's own pads (THT pads with their thermal ring filled back in): the copper corridor
    the zone provides, ignoring the deliberate thermal-relief spokes."""
    c = pcbnew.SHAPE_POLY_SET(z.GetFilledPolysList(F_CU))
    c.Unfracture()
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetNetCode() == z.GetNetCode() and p.IsOnLayer(F_CU) and z.Outline().Contains(p.GetPosition()):
                s = pcbnew.SHAPE_POLY_SET()
                gap = FMM(THERMAL_GAP + 0.02) if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH else 0
                p.TransformShapeToPolygon(s, F_CU, gap, FMM(0.005), pcbnew.ERROR_OUTSIDE)
                c.BooleanAdd(s)
    c.Simplify()
    return c


def opening(poly, w):
    """Morphological opening with a disk of diameter w: the union of all w-wide disks that fit."""
    e = pcbnew.SHAPE_POLY_SET(poly)
    e.Deflate(FMM(w / 2), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, FMM(0.005))
    e.Inflate(FMM(w / 2), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, FMM(0.005))
    e.Simplify()
    return e


def piece_of(op, pad):
    for k in range(op.OutlineCount()):
        if op.Contains(pad.GetPosition(), k):
            return k
    return None


def width_report(b, z):
    """Widest w such that every main pad sits inside ONE connected piece of the w-opening, i.e. the
    pads are joined by copper at least w wide everywhere (0.05 mm resolution)."""
    pads = [PadInfo(b, r, n).pad for r, n in MAIN_PADS.get(z.GetZoneName(), [])]
    cor = corridor(b, z)
    def joined(w):
        op = opening(cor, w)
        ks = {piece_of(op, p) for p in pads}
        return None not in ks and len(ks) == 1
    w, best = 0.2, None
    while w <= 6.0 and joined(w):
        best = w
        w = round(w + 0.05, 3)
    op2 = opening(cor, 2.0)
    groups = {}
    for (r, n), p in zip(MAIN_PADS.get(z.GetZoneName(), []), pads):
        groups.setdefault(piece_of(op2, p), []).append(f"{r}.{n}")
    return best, groups


def spoke_report(b):
    """Thermal spokes actually formed on each THT pad inside a zone: pieces of fill inside the
    thermal-gap ring around the pad (a spoke = one piece), and the narrowest spoke width."""
    out = []
    for z in all_zones(b):
        if z.GetNetname() == "GND" or not z.IsOnLayer(F_CU) or not z.HasFilledPolysForLayer(F_CU):
            continue
        fill = pcbnew.SHAPE_POLY_SET(z.GetFilledPolysList(F_CU)); fill.Unfracture()
        for fp in b.GetFootprints():
            for p in fp.Pads():
                if (p.GetAttribute() != pcbnew.PAD_ATTRIB_PTH or p.GetNetCode() != z.GetNetCode()
                        or not z.Outline().Contains(p.GetPosition())):
                    continue
                outer, inner = pcbnew.SHAPE_POLY_SET(), pcbnew.SHAPE_POLY_SET()
                p.TransformShapeToPolygon(outer, F_CU, FMM(THERMAL_GAP - 0.05), FMM(0.002), pcbnew.ERROR_INSIDE)
                p.TransformShapeToPolygon(inner, F_CU, FMM(0.05), FMM(0.002), pcbnew.ERROR_OUTSIDE)
                outer.BooleanSubtract(inner)
                ring = pcbnew.SHAPE_POLY_SET(fill); ring.BooleanIntersection(outer)
                n = sum(1 for k in range(ring.OutlineCount()) if abs(ring.Outline(k).Area()) > FMM(0.05) ** 2)
                out.append(f"{fp.GetReference()}.{p.GetNumber()}({z.GetNetname()}) {n} spokes")
    return out


def report(b, zlog, tlog, loops=None):
    print("\n=== ZONES (F.Cu) ===")
    CN = {pcbnew.ZONE_CONNECTION_THT_THERMAL: "THT_THERMAL (SMD solid, THT thermal)",
          pcbnew.ZONE_CONNECTION_THERMAL: "THERMAL (all pads)", pcbnew.ZONE_CONNECTION_FULL: "FULL"}
    zs = {z.GetZoneName(): z for z in all_zones(b)}
    for name, net, prio, pts in zlog:
        z = zs[name]
        print(f"{name} net={net} layer={'+'.join(pcbnew.LayerName(l) for l in z.GetLayerSet().Seq())} priority={z.GetAssignedPriority()} clearance={TMM(z.GetLocalClearance() or 0)} "
              f"min_thickness={TMM(z.GetMinThickness())} pad_connection={CN.get(z.GetPadConnection(), z.GetPadConnection())} "
              f"thermal gap {TMM(z.GetThermalReliefGap())} spoke {TMM(z.GetThermalReliefSpokeWidth())}")
        o = z.Outline()
        for k in range(o.OutlineCount()):
            print("   outline:", " ".join(f"({x:.3f},{y:.3f})" for x, y in poly_pts(o, k)))
            for h in range(o.HoleCount(k)):
                hh = o.Hole(k, h)
                print("   hole:", " ".join(f"({TMM(hh.CPoint(i).x):.3f},{TMM(hh.CPoint(i).y):.3f})" for i in range(hh.PointCount())))
    print("\n=== TRACKS ===")
    for net, w, layer, pts in tlog:
        print(f"{net} w={w} {layer}: " + " -> ".join("(" + ",".join(str(v) for v in q) + ")" for q in pts))
    print("\n=== FILL RESULTS ===")
    for z in all_zones(b):
        if z.GetNetname() == "GND" and z.GetZoneName() != "GND_hotloop":
            continue
        fp = z.GetFilledPolysList(F_CU)
        oa = abs(z.Outline().Area()) / 1e12
        fa = fp.Area() / 1e12
        best, groups = width_report(b, z)
        g2 = "; ".join(f"piece {k}: {' '.join(v)}" for k, v in groups.items())
        print(f"  {z.GetZoneName():12} outline {oa:6.1f} mm2  filled {fa:6.1f} mm2  fill pieces {fp.OutlineCount()}  "
              f"main pads joined by copper >= {best} mm wide   [2.0 mm opening -> {g2}]")
    print("\nTHT thermal reliefs (spoke width %.2f mm, gap %.2f mm):" % (SPOKE_W, THERMAL_GAP))
    print("   " + "; ".join(spoke_report(b)))
    check_outlines(b, {"GND_hotloop", "VIN_input", "SW_node", "VMID", "VOUT_bus"})
    # Hot loop: C4 (VIN pad) -> Q1 tab -> die (Q1 body centre) -> source lead -> D1 K -> D1 A -> C4 GND pad
    pc = lambda r, n: (TMM(PadInfo(b, r, n).pad.GetPosition().x), TMM(PadInfo(b, r, n).pad.GetPosition().y))
    q1 = b.FindFootprintByReference("Q1")
    body = [g for g in q1.GraphicalItems() if g.GetLayer() == pcbnew.F_Fab and g.GetClass() == "PCB_SHAPE"
            and g.GetShape() == pcbnew.SHAPE_T_POLY]
    bb = body[0].GetBoundingBox()
    die = (TMM(bb.GetCenter().x), TMM(bb.GetCenter().y))
    loop = [pc("C4", "2"), pc("C4", "1"), die, pc("Q1", "3"), pc("D1", "1"), pc("D1", "2")]
    area = abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(loop, loop[1:] + loop[:1]))) / 2
    print("\nHot loop (pad centres; die assumed at Q1 body centre %s):" % (tuple(round(v, 2) for v in die),))
    print("   " + " -> ".join(f"({x:.2f},{y:.2f})" for x, y in loop) + f"   area ~ {area:.1f} mm2")
    for name, pts in (loops or {}).items():
        # without the die: Q1 gate lead -> source lead taken as a straight line
        ext = [p for p in pts if p != die]
        print(f"Loop {name}: area {shoelace(pts):.1f} mm2 incl. Q1 die excursion, {shoelace(ext):.1f} mm2 external copper only")
        print("   " + " -> ".join(f"({x:.2f},{y:.2f})" for x, y in pts))
    # B.Cu signal copper inside the coordinator's keep-outs (power strip y<120; J1.2/C5.2 return x<126,y<128)
    for t in b.GetTracks():
        if t.GetClass() == "PCB_TRACK" and t.GetLayer() == pcbnew.B_Cu:
            (x0, y0), (x1, y1) = (TMM(t.GetStart().x), TMM(t.GetStart().y)), (TMM(t.GetEnd().x), TMM(t.GetEnd().y))
            L = math.hypot(x1 - x0, y1 - y0)
            n = 200
            inside1 = sum(1 for k in range(n) if (y0 + (y1 - y0) * (k + .5) / n) < 120) / n * L
            inside2 = sum(1 for k in range(n) if (x0 + (x1 - x0) * (k + .5) / n) < 126 and (y0 + (y1 - y0) * (k + .5) / n) < 128) / n * L
            print(f"B.Cu {t.GetNetname()} ({x0:.3f},{y0:.3f})->({x1:.3f},{y1:.3f}) L={L:.2f} mm; in y<120: {inside1:.2f}; in x<126&y<128: {inside2:.2f}")


def geo2(b):
    """Track vertices where two incident segments meet at <= 90 deg; split into 'in free copper' (the
    owner's no-90-degree rule) and 'inside a same-net pad' (pad junctions, informational)."""
    inc = {}
    for t in b.GetTracks():
        if t.GetClass() != "PCB_TRACK":
            continue
        s, e = (t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)
        for a, o in ((s, e), (e, s)):
            inc.setdefault((a, t.GetLayer(), t.GetNetCode()), []).append((o[0] - a[0], o[1] - a[1]))
    pads = [p for fp in b.GetFootprints() for p in fp.Pads()]
    free, inpad = [], []
    for (pt, L, nc), dirs in inc.items():
        bad = False
        for i in range(len(dirs)):
            for j in range(i + 1, len(dirs)):
                (ax, ay), (bx, by) = dirs[i], dirs[j]
                cos = (ax * bx + ay * by) / (math.hypot(ax, ay) * math.hypot(bx, by))
                if cos >= -1e-9:                      # angle <= 90 deg
                    bad = True
        if bad:
            v = pcbnew.VECTOR2I(*pt)
            where = inpad if any(p.GetNetCode() == nc and p.IsOnLayer(L) and p.HitTest(v) for p in pads) else free
            where.append((round(TMM(pt[0]), 3), round(TMM(pt[1]), 3), b.FindNet(nc).GetNetname() if False else nc))
    print(f"GEO-2: junctions with angle <= 90 deg outside pads: {len(free)} {free if free else ''}; inside same-net pads: {len(inpad)}")


def check_endpoints(path):
    """Reload the SAVED board and confirm every track end sits on same-net copper (pad, via, another
    track's end or a zone fill) and that no item was re-netted by the fill."""
    b = pcbnew.LoadBoard(path)
    pads = [p for fp in b.GetFootprints() for p in fp.Pads()]
    vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
    trks = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
    ends = {}
    for t in trks:
        for e in (t.GetStart(), t.GetEnd()):
            ends.setdefault((e.x, e.y, t.GetLayer(), t.GetNetCode()), []).append(t)
    bad = []
    for t in trks:
        for e in (t.GetStart(), t.GetEnd()):
            L, nc = t.GetLayer(), t.GetNetCode()
            ok = len(ends[(e.x, e.y, L, nc)]) > 1
            ok = ok or any(p.GetNetCode() == nc and p.IsOnLayer(L) and p.HitTest(e) for p in pads)
            ok = ok or any(v.GetNetCode() == nc and v.GetPosition() == e for v in vias)
            ok = ok or any(z.GetNetCode() == nc and z.IsOnLayer(L) and z.HitTestFilledArea(L, e) for z in all_zones(b))
            if not ok:
                bad.append(f"{t.GetNetname()} @({TMM(e.x):.3f},{TMM(e.y):.3f}) {pcbnew.LayerName(L)}")
    nets = sorted({t.GetNetname() for t in b.GetTracks()})
    print(f"\nEndpoint check on saved board: {len(trks)} segments, {len(vias)} vias, nets {nets}; "
          f"ends not on same-net copper: {bad if bad else 'none'}")


def main():
    stage = sys.argv[1].upper() if len(sys.argv) > 1 else "S1"
    assert stage in STAGES, stage
    n = STAGES.index(stage) + 1
    if n > 5:
        raise SystemExit(f"unknown stage {stage}")
    write_rules()                              # before LoadBoard so the loaded project already has it
    b = pcbnew.LoadBoard(BOARD)
    n_fp, n_dr = len(b.GetFootprints()), len(b.GetDrawings())
    for t in list(b.GetTracks()):              # PCB_TRACK, PCB_ARC, PCB_VIA (Delete: Remove + free;
        b.Delete(t)                            #  plain Remove() left dangling proxies -> crash)
    for z in all_zones(b):
        b.Delete(z)
    assert (len(b.GetFootprints()), len(b.GetDrawings())) == (n_fp, n_dr)
    zlog, tlog = [], []
    build_s1(b, zlog, tlog)
    loops = build_s2(b, tlog) if n >= 2 else {}
    kel = build_s3(b, tlog) if n >= 3 else None
    s4 = None
    if n >= 4:
        build_s4_zones(b, zlog, pcbnew.ISLAND_REMOVAL_MODE_NEVER)
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        print('  [s4] zones filled', flush=True)
        placed, vlog = build_s4_vias(b, tlog)
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        orphans = {pcbnew.LayerName(L): [(round(a, 2), [round(v, 1) for v in bb]) for a, t, nv, bb, _ in fill_pieces(b, L)
                                         if not t and nv == 0] for L in (F_CU, pcbnew.B_Cu)}
        for z in all_zones(b):
            if z.GetNetname() == "GND":
                z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        for v in b.GetTracks():                     # teardrop flag on signal vias (generation: KiCad GUI)
            if v.GetClass() == "PCB_VIA" and v.GetNetname() != "GND":
                v.SetTeardropsEnabled(True)
        s4 = (placed, vlog, orphans)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    s5 = build_s5(b) if n >= 5 else None
    b.Save(BOARD)
    print(f"saved {BOARD}: {len(b.GetTracks())} track items, {b.GetAreaCount()} zones")
    report(b, zlog, tlog, loops)
    if kel:
        kelvin_report(b, kel)
    if s4:
        s4_report(b, *s4)
    if s5:
        print()
        print("=== S5 SILK ===")
        for name, res in s5[0]:
            print(f"  placed {name}: (x, y, angle, distance from part/pin edge, vias under) = {res}")
        print(f"  NOT PLACED ({len(s5[1])}): {s5[1]}")
    check_endpoints(BOARD)
    geo2(b)


if __name__ == "__main__":
    main()
