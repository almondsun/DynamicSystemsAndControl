"""Rev B routing: manual power/gate/Kelvin geometry, GND fan-out, grid router, GND planes.

    python3.14 -I route_revb.py <placed.kicad_pcb> <routed.kicad_pcb>
KiCad DRC (kicad-cli, with zone refill and schematic parity) is the acceptance check.
"""
import math
import sys
import time
from pathlib import Path

import numpy as np
import pcbnew

sys.path.insert(0, str(Path(__file__).resolve().parent))
import router  # noqa: E402

F, B = "F.Cu", "B.Cu"
# (net, layer, width mm, [points]) - straight segments between consecutive points.
MANUAL = [
    # VIN: J1 -> trunk -> bulk caps -> corridor right of Q1 -> drain; branches to TP1, U2/C9, D2, C3.
    ("VIN", F, 3.0, [(113.0, 35.6), (116.0, 38.6), (116.0, 52.0), (130.25, 52.0), (130.25, 71.2)]),
    ("VIN", F, 2.6, [(130.25, 71.2), (132.5, 73.45), (132.5, 89.94)]),
    ("VIN", F, 1.9, [(132.5, 89.94), (130.0, 89.94)]),
    ("VIN", F, 0.6, [(130.4, 82.4), (132.0, 82.4)]),
    ("VIN", F, 3.0, [(113.0, 35.6), (120.0, 36.5)]),
    ("VIN", F, 1.0, [(116.0, 47.45), (124.7, 47.45)]),
    ("VIN", F, 3.0, [(116.0, 52.0), (116.0, 77.44), (121.4, 77.44)]),
    # VIN to U1 VCC/C7 on B.Cu from the D2 anode pad (keeps the F.Cu left corridor for logic).
    ("VIN", B, 0.5, [(121.4, 77.44), (123.4, 79.44), (123.4, 96.9), (121.0, 96.9)]),
    ("VIN", F, 0.5, [(121.0, 96.9), (121.725, 96.2), (121.725, 95.0)]),
    ("VIN", F, 0.5, [(118.6, 93.755), (120.6, 93.755), (121.45, 94.6)]),
    # Gate loop on F.Cu only: HO -> R1 -> G; VB -> D2 cathode -> C6; VS under C6 -> R2 -> S.
    ("HO", F, 0.5, [(118.6, 87.405), (119.2, 87.405), (119.2, 86.0), (119.9, 85.3), (124.69, 85.3)]),
    ("GATE", F, 0.5, [(126.51, 85.3), (127.3, 85.3), (128.9, 86.9)]),
    ("GATE", F, 0.5, [(126.8, 88.9), (126.8, 85.3)]),
    ("GATE", F, 0.5, [(126.51, 85.0), (126.4, 81.5)]),
    ("BOOT", F, 0.5, [(118.6, 88.675), (120.6, 88.675), (121.0, 88.3)]),
    ("BOOT", F, 0.5, [(121.5, 88.5), (121.725, 90.2)]),
    ("SW", F, 0.5, [(118.6, 89.945), (119.65, 89.945), (119.65, 92.1), (128.6, 92.1)]),
    ("SW", F, 0.5, [(124.675, 91.0), (124.675, 92.1)]),
    ("SW", F, 0.5, [(126.8, 91.0), (126.8, 92.1)]),
    # SW power node: S -> L1 pad 1; D1 cathode -> L1 pad 1; TP3.
    ("SW", F, 1.8, [(130.0, 92.48), (137.0, 92.48)]),
    ("SW", F, 1.6, [(133.5, 99.6), (137.0, 99.6)]),
    # Direct source -> freewheel cathode link: closes the hot loop without detouring through L1.
    ("SW", F, 1.2, [(130.4, 93.2), (133.1, 98.9)]),
    ("SW", F, 1.0, [(133.0, 104.2), (137.0, 104.2)]),
    # L1 pad 2 -> RS1 (IP), power entering RS1 from the outer end only (TA-I Kelvin land).
    ("IP", F, 3.5, [(158.9, 98.5), (185.5, 98.5)]),
    ("VOUT", F, 3.5, [(195.3, 98.5), (196.5, 98.5)]),
    ("VOUT", F, 2.0, [(197.7, 90.0), (197.7, 98.5)]),
    ("VOUT", F, 2.0, [(197.7, 98.5), (198.0, 107.4)]),
    ("VOUT", F, 1.0, [(191.5, 106.0), (197.0, 106.0)]),
    # Kelvin sense from the inner pad edges straight to U6 IN+/IN-.
    ("IP", F, 0.25, [(188.1, 97.0), (188.9, 96.2), (188.9, 93.7)]),
    ("VOUT", F, 0.25, [(192.7, 97.0), (191.9, 96.2), (191.9, 93.7)]),
    # Under-body links between pins on opposite sides (heel to heel, >= 0.3 mm to other pads).
    ("BUF_OE_N", F, 0.25, [(183.5, 46.05), (184.3, 46.05), (184.3, 48.0), (183.5, 48.0)]),
    ("BUF_OE_N", F, 0.25, [(184.3, 48.0), (184.3, 48.65), (188.5, 48.65)]),
    ("NRESET", F, 0.25, [(157.6, 61.73), (162.4, 61.73)]),
    ("NFAULT", F, 0.25, [(157.6, 64.27), (161.6, 64.27), (161.6, 63.0), (162.4, 63.0)]),
    ("NFAULT", F, 0.25, [(161.6, 64.27), (162.4, 64.27)]),
    # Fine-pitch supply pins: thin stubs clear of neighbours, the router joins at the stub end.
    ("+5V", F, 0.25, [(189.4, 46.05), (190.7, 46.05)]),
    ("+5V", F, 0.25, [(189.4, 46.7), (190.3, 46.7), (190.7, 46.05)]),
    ("NUC_3V3", F, 0.25, [(190.4, 69.05), (191.5, 69.05), (192.3, 68.25), (192.3, 67.5)]),
    ("GND", F, 0.3, [(183.1, 49.95), (181.65, 50.0)]),
    # U6 supply pin to C16 (C16 GND gets its own via below).
    ("+5V", F, 0.4, [(191.7, 91.3), (191.9, 89.9)]),
]
VIAS = [("VIN", 121.0, 96.9, 0.8, 0.4),
        # U7 pin 7 (GND, 0.65 mm pitch): own stitching via at the toe before signals are routed.
        ("GND", 181.65, 50.0, 0.8, 0.4)]
# GND pads that carry switching or bulk current get several stitching vias.
GND_VIAS = {("D1", "2"): 4, ("C1", "2"): 3, ("C2", "2"): 3, ("C3", "2"): 2, ("C4", "2"): 2, ("C5", "2"): 2,
            ("U2", "2"): 4, ("C7", "2"): 1, ("U1", "2"): 1, ("U6", "2"): 1, ("C16", "2"): 1}
# Signal nets routed by the grid router: (net, width). Power nets above are manual.
SIGNALS = [
    ("PWM_IN", 0.25), ("MCU_PWM", 0.25), ("RUN", 0.25), ("RESET", 0.25), ("DPRIME", 0.25), ("RUN_5V", 0.25),
    ("RESET_5V", 0.25), ("BUF_OE_N", 0.25), ("ADC_EN", 0.25), ("NUC_PG", 0.25), ("PG_DELAY", 0.25),
    ("NUC_SENSE", 0.25), ("NFAULT_MCU", 0.25), ("VSENSE", 0.25), ("VSENSE_PROT", 0.25), ("VSENSE_DIV", 0.25),
    ("REF_2V5", 0.25), ("+5V", 0.4), ("NUC_3V3", 0.35), ("ISENSE", 0.25), ("OVSENSE", 0.25), ("VREF", 0.25),
    ("NTRIP", 0.25), ("FAULT", 0.25), ("NFAULT", 0.25), ("NRESET", 0.25), ("FB", 0.25), ("SD", 0.25),
    ("HIN", 0.25), ("VOUT", 0.3),
]
SW_ANALOG_CLEARANCE = 0.5
ANALOG = {"ISENSE", "OVSENSE", "VREF", "VSENSE", "VSENSE_PROT", "VSENSE_DIV", "REF_2V5", "NUC_SENSE", "PG_DELAY"}
POWER_NETS = {"SW", "IP", "GND", "VIN"}


def mm2(v):
    return pcbnew.FromMM(float(v))


def add_track(board, net, layer, width, a, b):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm2(a[0]), mm2(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(mm2(b[0]), mm2(b[1])))
    t.SetWidth(mm2(width))
    t.SetLayer(board.GetLayerID(layer))
    t.SetNet(board.FindNet(net))
    board.Add(t)
    return t


def add_via(board, net, x, y, dia, drill):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(mm2(x), mm2(y)))
    v.SetWidth(mm2(dia))
    v.SetDrill(mm2(drill))
    v.SetNet(board.FindNet(net))
    board.Add(v)
    return v


def manual(board):
    for net, layer, width, pts in MANUAL:
        for a, b in zip(pts, pts[1:]):
            add_track(board, net, layer, width, a, b)
    for net, x, y, dia, drill in VIAS:
        add_via(board, net, x, y, dia, drill)


def gnd_fanout(board, grid):
    gnd = board.FindNet("GND").GetNetCode()
    free, via_ok = grid.free_maps(gnd, "GND", 0.2, 0.25, 0.4)
    # Keep the escape corridors of 0.65 mm-pitch pins free for the signal router.
    escape = np.zeros((grid.ny, grid.nx), bool)
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetAttribute() == pcbnew.PAD_ATTRIB_SMD and neighbour_gap(fp, pad) < 0.3:
                for _, iy, ix in escape_cells(grid, pad, length=2.0):
                    escape[iy, ix] = True
    from scipy import ndimage
    keep = ndimage.distance_transform_edt(~escape) * grid.g < 0.4 + 0.25 + 0.15
    placed = []
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname() != "GND" or pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                continue
            if neighbour_gap(fp, pad) < 0.3:
                continue  # 0.65 mm-pitch GND pins join the pour at their toe (U7.7 has a manual via)
            want = GND_VIAS.get((fp.GetReference(), pad.GetNumber()), 1)
            px, py = router.MM(pad.GetPosition().x), router.MM(pad.GetPosition().y)
            bb = pad.GetBoundingBox()
            half = max(router.MM(bb.GetWidth()), router.MM(bb.GetHeight())) / 2
            cands = []
            for r in np.arange(half + 0.45, half + 2.6, 0.1):
                for k in range(72):
                    a = 2 * math.pi * k / 72
                    x, y = px + r * math.cos(a), py + r * math.sin(a)
                    iy, ix = grid.cell(x, y)
                    if 0 <= iy < grid.ny and 0 <= ix < grid.nx and via_ok[iy, ix] and not keep[iy, ix]:
                        cands.append((r, x, y))
            got = 0
            for r, x, y in sorted(cands):
                if any(math.dist((x, y), q) < 1.3 for q in placed):
                    continue
                # Short F.Cu stub from pad centre to the via must stay clear of other nets.
                if not stub_clear(grid, free, (px, py), (x, y), set(router.item_cells(grid, pad))):
                    continue
                v = add_via(board, "GND", x, y, 0.8, 0.4)
                t = add_track(board, "GND", F, 0.4, (px, py), (x, y))
                grid.add_item(v, gnd)
                grid.add_item(t, gnd)
                placed.append((x, y))
                free, via_ok = grid.free_maps(gnd, "GND", 0.2, 0.25, 0.4)
                got += 1
                if got == want:
                    break
            if got < want:
                print(f"WARNING: {fp.GetReference()}.{pad.GetNumber()} GND vias {got}/{want}")


def neighbour_gap(fp, pad):
    """Smallest edge-to-edge gap from pad to another pad of the same footprint (bounding boxes)."""
    a = pad.GetBoundingBox()
    best = 9.0
    for q in fp.Pads():
        if q.GetNumber() == pad.GetNumber():
            continue
        b = q.GetBoundingBox()
        dx = max(b.GetX() - a.GetRight(), a.GetX() - b.GetRight(), 0)
        dy = max(b.GetY() - a.GetBottom(), a.GetY() - b.GetBottom(), 0)
        best = min(best, router.MM(math.hypot(dx, dy)))
    return best


def stub_clear(grid, free, a, b, own):
    n = max(2, int(math.dist(a, b) / 0.05))
    for k in range(n + 1):
        x = a[0] + (b[0] - a[0]) * k / n
        y = a[1] + (b[1] - a[1]) * k / n
        iy, ix = grid.cell(x, y)
        if not free[0, iy, ix] and (0, iy, ix) not in own:
            return False
    return True


def net_pads(board, net):
    return [p for fp in board.GetFootprints() for p in fp.Pads() if p.GetNetname() == net]


def pad_key(pad):
    return (pad.GetParentFootprint().GetReference(), pad.GetNumber())


def clusters(board, pads):
    """Pad clusters of one net from KiCad's own connectivity (exact copper overlap)."""
    board.BuildConnectivity()
    conn = board.GetConnectivity()
    parent = {pad_key(p): pad_key(p) for p in pads}

    def find(k):
        while parent[k] != k:
            k = parent[k]
        return k
    # GetConnectedPads() only reports pads touching the item; GetConnectedItems() walks the cluster.
    for p in pads:
        for q in conn.GetConnectedItems(p):
            if q.GetClass() == "PAD" and pad_key(q) in parent:
                parent[find(pad_key(q))] = find(pad_key(p))
    return {pad_key(p): find(pad_key(p)) for p in pads}, conn


def cluster_mask(grid, conn, members):
    mask = np.zeros((2, grid.ny, grid.nx), bool)
    seen = set()
    for pad in members:
        for item in [pad] + list(conn.GetConnectedItems(pad)):
            k = item.m_Uuid.AsString()
            if k in seen:
                continue
            seen.add(k)
            for li, iy, ix in router.item_cells(grid, item):
                mask[li, iy, ix] = True
    return mask


def escape_cells(grid, pad, length=1.6):
    """Cells on the long axis of a fine-pitch SMD pad, from its centre outward past the toe.
    A track centred on that axis keeps >= 0.3 mm to 0.65 mm-pitch neighbours, which the
    rasterisation margin would otherwise refuse."""
    if pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
        return []
    bb = pad.GetBoundingBox()
    w, h = router.MM(bb.GetWidth()), router.MM(bb.GetHeight())
    if min(w, h) >= 0.65:
        return []
    px, py = router.MM(pad.GetPosition().x), router.MM(pad.GetPosition().y)
    fx, fy = (router.MM(v) for v in (pad.GetParentFootprint().GetPosition().x,
                                     pad.GetParentFootprint().GetPosition().y))
    if w >= h:
        dx, dy, reach = (1 if px >= fx else -1), 0, w / 2 + length
    else:
        dx, dy, reach = 0, (1 if py >= fy else -1), h / 2 + length
    cells = []
    for k in range(int(reach / grid.g) + 1):
        iy, ix = grid.cell(px + dx * k * grid.g, py + dy * k * grid.g)
        cells.append((0, iy, ix))
    return cells


def anchor_width(pad):
    bb = pad.GetBoundingBox()
    return min(router.MM(bb.GetWidth()), router.MM(bb.GetHeight())) * 0.9


def route_signals(board, grid, only=None):
    sw = board.FindNet("SW").GetNetCode()
    failures = []
    for net, width in SIGNALS:
        if only and net not in only:
            continue
        code = board.FindNet(net).GetNetCode()
        clear = 0.25
        via_dia, via_drill = (0.8, 0.4) if net in ("+5V", "NUC_3V3", "VOUT") else (0.6, 0.3)
        pads = net_pads(board, net)
        skipped = set()
        while True:
            root, conn = clusters(board, pads)
            main = root[pad_key(pads[0])]
            todo = [p for p in pads if root[pad_key(p)] != main and pad_key(p) not in skipped]
            if not todo:
                break
            free, via_ok = grid.free_maps(code, net, width / 2, clear, via_dia / 2,
                                          sw_net=sw if net in ANALOG else 0, sw_clear=SW_ANALOG_CLEARANCE)
            tgt = cluster_mask(grid, conn, [p for p in pads if root[pad_key(p)] == main])
            ty, tx = np.argwhere(tgt[0] | tgt[1]).mean(0)
            pad = min(todo, key=lambda p: math.dist(grid.cell(router.MM(p.GetPosition().x),
                                                              router.MM(p.GetPosition().y)), (ty, tx)))
            src = cluster_mask(grid, conn, [p for p in pads if root[pad_key(p)] == root[pad_key(pad)]])
            for q in ([pad] + [q for q in pads if root[pad_key(q)] == main]) if width <= 0.25 else []:
                for c in escape_cells(grid, q):
                    if grid.owner[c] in (0, code):
                        free[c] = True
            t0 = time.time()
            path = grid.astar(free, via_ok, src, tgt)
            print(f"  {net} {pad_key(pad)} {'ok' if path else 'FAIL'} {time.time() - t0:.1f}s", flush=True)
            if path is None or len(path) < 2:
                failures.append((net, *pad_key(pad)))
                skipped.add(pad_key(pad))
                continue
            start = end = None
            if path[0] in set(router.item_cells(grid, pad)):
                start = (router.MM(pad.GetPosition().x), router.MM(pad.GetPosition().y))
            for q in pads:
                if root[pad_key(q)] == main and path[-1] in set(router.item_cells(grid, q)):
                    end = (router.MM(q.GetPosition().x), router.MM(q.GetPosition().y))
                    break
            aw = min([anchor_width(pad)] + [anchor_width(q) for q in pads if root[pad_key(q)] == main])
            router.emit(board, grid, path, code, width, via_dia, via_drill, start, end, aw)
        print(f"routed {net}: {len(pads)} pads, skipped {len(skipped)}", flush=True)
    return failures


def stitch(board):
    """GND vias where both pours are solid (0.6 mm margin), on a 4 mm grid, plus one per isolated
    F.Cu fragment; the planes are then refilled."""
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    zf = [z for z in board.Zones() if z.GetLayer() == pcbnew.F_Cu][0]
    zb = [z for z in board.Zones() if z.GetLayer() == pcbnew.B_Cu][0]
    pf, pb = zf.GetFilledPolysList(pcbnew.F_Cu), zb.GetFilledPolysList(pcbnew.B_Cu)

    def solid(x, y):
        for k in range(12):
            a = 2 * math.pi * k / 12
            for r in (0.0, 0.62):
                pt = pcbnew.VECTOR2I(mm2(x + r * math.cos(a)), mm2(y + r * math.sin(a)))
                if not (pf.Contains(pt) and pb.Contains(pt)):
                    return False
        return True
    smd = []
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetAttribute() in (pcbnew.PAD_ATTRIB_SMD, pcbnew.PAD_ATTRIB_CONN):
                b = pad.GetBoundingBox()
                smd.append((router.MM(b.GetX()) - 0.65, router.MM(b.GetY()) - 0.65,
                            router.MM(b.GetRight()) + 0.65, router.MM(b.GetBottom()) + 0.65))
    existing = [(router.MM(v.GetPosition().x), router.MM(v.GetPosition().y)) for v in board.GetTracks()
                if v.GetClass() == "PCB_VIA" and v.GetNetname() == "GND"]
    added = 0
    bb = board.GetBoardEdgesBoundingBox()
    x0, y0, x1, y1 = (router.MM(v) for v in (bb.GetX(), bb.GetY(), bb.GetRight(), bb.GetBottom()))
    for i in range(pf.OutlineCount()):
        ol = pf.Outline(i)
        pts = [(router.MM(ol.CPoint(k).x), router.MM(ol.CPoint(k).y)) for k in range(ol.PointCount())]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        has = any(min(xs) <= x <= max(xs) and min(ys) <= y <= max(ys) and
                  pf.Outline(i).PointInside(pcbnew.VECTOR2I(mm2(x), mm2(y))) for x, y in existing)
        cands = [(x, y) for x in np.arange(min(xs), max(xs), 0.25) for y in np.arange(min(ys), max(ys), 0.25)]
        grid_pts = [(x, y) for x, y in cands if abs(((x - x0) % 4.0) - 2.0) < 0.13 and abs(((y - y0) % 4.0) - 2.0) < 0.13]
        for x, y in (grid_pts if has else grid_pts + cands):
            if not pf.Outline(i).PointInside(pcbnew.VECTOR2I(mm2(x), mm2(y))) or not solid(x, y):
                continue
            if any(math.dist((x, y), q) < 2.5 for q in existing):
                continue
            if any(a <= x <= c and b <= y <= d for a, b, c, d in smd):
                continue  # project rule: no via hole within 0.2 mm of an SMD pad
            add_via(board, "GND", float(x), float(y), 0.8, 0.4)
            existing.append((x, y))
            added += 1
            has = True
            if not grid_pts:
                break
    filler.Fill(board.Zones())
    print("stitching vias added:", added)


def zones(board):
    bb = board.GetBoardEdgesBoundingBox()
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetNet(board.FindNet("GND"))
        outline = z.Outline()
        outline.NewOutline()
        for x, y in ((bb.GetX(), bb.GetY()), (bb.GetRight(), bb.GetY()), (bb.GetRight(), bb.GetBottom()),
                     (bb.GetX(), bb.GetBottom())):
            outline.Append(x, y)
        z.SetLocalClearance(mm2(0.3))
        z.SetMinThickness(mm2(0.25))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THT_THERMAL)
        z.SetThermalReliefGap(mm2(0.4))
        z.SetThermalReliefSpokeWidth(mm2(0.5))
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        z.SetAssignedPriority(0)
        board.Add(z)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())


def main() -> None:
    board = pcbnew.LoadBoard(sys.argv[1])
    manual(board)
    grid = router.Grid(board)
    for name, bbx in (("L1", board.FindFootprintByReference("L1")),):
        c = bbx.GetCourtyard(pcbnew.F_CrtYd).BBox()
        grid.add_keepout(name, router.MM(c.GetX()), router.MM(c.GetY()), router.MM(c.GetRight()),
                         router.MM(c.GetBottom()), (0, 1), lambda n: n not in POWER_NETS)
    grid.add_keepout("cell_bcu", 119.5, 78.0, 140.0, 106.0, (1,), lambda n: n not in ("GND", "VIN"))
    gnd_fanout(board, grid)
    failures = route_signals(board, grid)
    zones(board)
    stitch(board)
    pcbnew.SaveBoard(sys.argv[2], board)
    print("failures:", failures)


if __name__ == "__main__":
    main()
