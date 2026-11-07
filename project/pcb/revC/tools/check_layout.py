"""check_layout.py -- independent routing audit for the Buck 12 V -> 6 V Rev C board (KiCad 10).

usage:  "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" -I check_layout.py <board.kicad_pcb>
            [--stage S0..S5] [--baseline <pcb>] [--sch <kicad_sch>] [--render] [--no-export]

Read-only on the board under test: the board, its .kicad_pro/.kicad_dru/.kicad_sch and libraries
are first COPIED into review/runs/<stamp>/snap/ and every check (pcbnew API, kicad-cli DRC,
gerber/drill export, JLC spacing script) runs on that snapshot.  Nothing is ever saved back.

Stage semantics (see checklist.md):
  always   -> FAIL from S1 on (WARN at S0, i.e. the unrouted baseline)
  complete -> WARN at S0..S3, FAIL from S4 on (unconnected items, GND pours, teardrops, stitching)
  final    -> WARN at S0..S4, FAIL at S5 (silkscreen and labels)
Exit code 1 if any check FAILs, else 0.  Every line: STATUS  ID  title -- summary, then details.
"""
import argparse, collections, datetime, hashlib, json, math, os, re, shutil, subprocess, sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
SCRATCH = os.path.dirname(os.path.dirname(HERE))
KCLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
KPY = r"C:\Program Files\KiCad\10.0\bin\python.exe"
PROJECT_DIR = r"C:\Users\voxte\DynamicSystemsAndControl\project\pcb\revC\pcb_revC"   # read-only fallback for sch/libs
DEFAULT_BASELINE = os.path.join(HERE, "unrouted_baseline.kicad_pcb")
JLC_SPACING = os.path.join(SCRATCH, "jlc_spacing.py")

FMM, TMM = pcbnew.FromMM, pcbnew.ToMM
ERR = FMM(0.002)                       # polygon approximation error
F, B = pcbnew.F_Cu, pcbnew.B_Cu
LNAME = {F: "F.Cu", B: "B.Cu"}

# ------------------------------------------------------------------ design constants (spec + sources)
POWER = ["VIN", "SW", "VMID", "VOUT", "LOAD_A", "LOAD_B"]
DRIVE = ["GATE", "BOOT", "DRV_E", "DRV_B"]
SENSE = ["VOUT_SENSE", "VIN_SENSE"]
CTRL = ["PWM", "LSW_A", "LSW_B"]
W_POWER, W_DRIVE, W_SIG = 1.5, 0.5, 0.25
W_IPC_2A = 1.0           # IPC-2152 fits, 1 oz external, 10 C rise, 2 A: 0.93 mm (Brooks/Adam Eq.3-2), 1.01 mm (smps.us Fig.5-2 fit)
W_SW_MIN = 2.0           # spec: SW zone >= 2 mm wide
# low-current branches of power nets: (ref, pad) -> minimum width.  A narrow branch is legal only if it
# ends on one of these pads and attaches to the wide power copper at exactly one place.
TAP_PREF = {("D2", "2"): W_DRIVE}      # preferred (WARN below); TAPS holds the hard minimum
TAPS = {"VIN": {("R3", "1"): W_SIG, ("R9", "1"): W_SIG, ("D2", "2"): W_SIG, ("TP1", "1"): W_SIG},
        "VOUT": {("R7", "1"): W_SIG, ("TP4", "1"): W_SIG},
        "SW": {("Q5", "3"): W_DRIVE, ("R6", "2"): W_DRIVE, ("C9", "2"): W_DRIVE, ("TP2", "1"): W_DRIVE}}
# deviations the reviewer accepted after analysis (stage report gives the reasoning); key = (check, net, origin "x,y")
ACCEPTED_DEV = {("SIG-4", "VIN", "102.5,125.5"): "S3: VIN tap starts at TP1, dead end of the VIN strip (no DC current); "
                                                  "DC drop J1.1->C1..C3 ~1.4 mV = 0.4 ADC LSB"}
HOT_LOOP = [("C4", "1"), ("Q1", "2"), ("Q1", "3"), ("D1", "1"), ("D1", "2"), ("C4", "2")]
GATE_LOOP = [("C9", "1"), ("Q4", "3"), ("Q4", "2"), ("R5", "1"), ("R5", "2"), ("Q1", "1"), ("Q1", "3"), ("C9", "2")]
HOT_PAIRS = [("VIN", ("C4", "1"), ("Q1", "2")), ("SW", ("Q1", "3"), ("D1", "1")), ("GND", ("D1", "2"), ("C4", "2")),
             ("VIN", ("C1", "1"), ("Q1", "2")), ("VIN", ("C2", "1"), ("Q1", "2")), ("VIN", ("C3", "1"), ("Q1", "2")),
             ("GND", ("C1", "2"), ("D1", "2")), ("GND", ("C2", "2"), ("D1", "2")), ("GND", ("C3", "2"), ("D1", "2"))]
HOT_GND = [("C1", "2"), ("C2", "2"), ("C3", "2"), ("C4", "2"), ("D1", "2")]
POWER_GND_PADS = HOT_GND + [("C6", "2"), ("C7", "2")]
SMD_POWER_REFS = ["C1", "C2", "C3", "C4", "C6", "C7", "C8", "Q1", "D1", "L1", "L2"]
POWER_THT = {("J1", "1"), ("J1", "2"), ("J2", "1"), ("J2", "2"), ("J3", "1"), ("J3", "2"), ("J4", "1"), ("J4", "2"), ("C5", "1"), ("C5", "2")}
HOT_REFS = ["C1", "C2", "C3", "C4", "Q1", "D1"]
STAGE_REFS = ["C1", "C2", "C3", "C4", "C6", "C7", "C8", "Q1", "D1", "L1", "L2"]
HAND_SOLDER = ["J1", "J2", "J3", "J4", "J5", "J6", "C5"] + ["TP%d" % i for i in range(1, 11)]
BODY_OVERRIDE = {"L1": 12.5, "L2": 12.5}        # Bourns SRR1280 body 12.5 x 12.5 mm (Fab-less custom footprint)
CONN_LABELS = {"J1": ["+12V", "GND"], "J2": ["VOUT", "GND"], "J3": ["VOUT", "36R"], "J4": ["VOUT", "24R"]}
LABEL_NET = {"+12V": "VIN", "12V": "VIN", "GND": "GND", "VOUT": "VOUT", "36R": "LOAD_A", "24R": "LOAD_B"}
SILK_DRC = {"silk_overlap", "silk_over_copper", "silk_edge_clearance", "silk_clearance", "text_height", "text_thickness",
            "mirrored_text_on_front_layer", "nonmirrored_text_on_back_layer"}
ENV_DRC = {"lib_footprint_issues", "lib_footprint_mismatch"}


# ------------------------------------------------------------------ small geometry helpers (mm floats)
def mmxy(v):
    return (TMM(v.x), TMM(v.y))


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def pt_seg(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def shoelace(pts):
    return abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]))) / 2.0


def V(x, y):
    return pcbnew.VECTOR2I(FMM(x), FMM(y))


def box_poly(x1, y1, x2, y2):
    s = pcbnew.SHAPE_POLY_SET(); s.NewOutline()
    for x, y in ((x1, y1), (x2, y1), (x2, y2), (x1, y2)):
        s.Append(FMM(x), FMM(y))
    return s


def bbox_mm(b):
    return (TMM(b.GetLeft()), TMM(b.GetTop()), TMM(b.GetRight()), TMM(b.GetBottom()))


def boxes_overlap(a, b, m=0.0):
    return not (a[2] + m < b[0] or b[2] + m < a[0] or a[3] + m < b[1] or b[3] + m < a[1])


def area_mm2(ps):
    return ps.Area() / 1e12


def copy_ps(ps):
    return ps.CloneDropTriangulation()


def inter_area(a, b):
    t = copy_ps(a); t.BooleanIntersection(b); return area_mm2(t)


def sub_poly(ps, i):
    s = pcbnew.SHAPE_POLY_SET(); s.AddOutline(ps.COutline(i))
    for h in range(ps.HoleCount(i)):
        s.AddHole(ps.CHole(i, h))
    return s


def inflate(ps, mm_):
    t = copy_ps(ps)
    if mm_ > 0:
        t.Inflate(FMM(mm_), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, ERR)
    elif mm_ < 0:
        t.Deflate(FMM(-mm_), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, ERR)
    return t


# ------------------------------------------------------------------ result bookkeeping
class Audit:
    def __init__(self, stage):
        self.stage = stage
        self.results = []

    def lvl(self, kind):
        return {"always": "FAIL" if self.stage >= 1 else "WARN",
                "complete": "FAIL" if self.stage >= 4 else "WARN",
                "final": "FAIL" if self.stage >= 5 else "WARN",
                "advice": "WARN"}[kind]

    def add(self, cid, title, status, summary, details=()):
        self.results.append({"id": cid, "title": title, "status": status, "summary": summary, "details": list(details)})


def worst(*st):
    order = {"FAIL": 3, "WARN": 2, "PASS": 1, "N/A": 0}
    return max(st, key=lambda s: order[s]) if st else "N/A"


# ------------------------------------------------------------------ board model
class Model:
    def __init__(self, board):
        self.b = board
        self.fps = {f.GetReference(): f for f in board.GetFootprints()}
        self.pads = [p for f in board.GetFootprints() for p in f.Pads() if p.GetNumber()]
        self.segs, self.arcs, self.vias = [], [], []
        for t in board.GetTracks():
            ty = t.Type()
            if ty == pcbnew.PCB_VIA_T:
                self.vias.append(t.Cast() if hasattr(t, "Cast") else t)
            elif ty == pcbnew.PCB_ARC_T:
                self.arcs.append(t.Cast() if hasattr(t, "Cast") else t)
            else:
                self.segs.append(t)
        allz = list(board.Zones())
        self.zones = [z for z in allz if not z.IsTeardropArea()]
        self.tdrops = [z for z in allz if z.IsTeardropArea()]
        self.netname = {}
        for p in self.pads:
            self.netname[p.GetNetCode()] = p.GetNetname()
        for t in self.segs + self.arcs + self.vias + allz:
            self.netname[t.GetNetCode()] = t.GetNetname()
        self._cu = {}
        self._padpoly = {}

    def code(self, net):
        n = self.b.FindNet(net)
        return n.GetNetCode() if n else -1

    def pad(self, ref, num):
        f = self.fps.get(ref)
        if not f:
            return None
        for p in f.Pads():
            if p.GetNumber() == num:
                return p
        return None

    def pxy(self, ref, num):
        p = self.pad(ref, num)
        return mmxy(p.GetPosition()) if p else None

    def padpoly(self, p, layer, grow=0.0):
        key = (p.m_Uuid.AsString(), layer, round(grow, 4))
        if key not in self._padpoly:
            s = pcbnew.SHAPE_POLY_SET()
            p.TransformShapeToPolygon(s, layer, FMM(grow) if grow > 0 else 0, ERR, pcbnew.ERROR_INSIDE)
            self._padpoly[key] = s
        return self._padpoly[key]

    def zone_fill(self, z, layer):
        s = pcbnew.SHAPE_POLY_SET()
        if z.IsOnLayer(layer) and z.HasFilledPolysForLayer(layer):
            s.Append(z.GetFilledPolysList(layer))
        return s

    def copper(self, code, layer, zones=True, tracks=True, pads=True):
        key = (code, layer, zones, tracks, pads)
        if key in self._cu:
            return self._cu[key]
        s = pcbnew.SHAPE_POLY_SET()
        if tracks:
            for t in self.segs + self.arcs + self.vias:
                if t.GetNetCode() == code and t.IsOnLayer(layer):
                    t.TransformShapeToPolygon(s, layer, 0, ERR, pcbnew.ERROR_INSIDE)
        if pads:
            for p in self.pads:
                if p.GetNetCode() == code and p.IsOnLayer(layer) and p.FlashLayer(layer):
                    p.TransformShapeToPolygon(s, layer, 0, ERR, pcbnew.ERROR_INSIDE)
        if zones:
            for z in self.zones + self.tdrops:
                if z.GetNetCode() == code:
                    s.Append(self.zone_fill(z, layer))
        s.Simplify()
        self._cu[key] = s
        return s

    def fp_body(self, ref):
        f = self.fps[ref]
        x, y = mmxy(f.GetPosition())
        if ref in BODY_OVERRIDE:
            h = BODY_OVERRIDE[ref] / 2
            return (x - h, y - h, x + h, y + h)
        boxes = [bbox_mm(g.GetBoundingBox()) for g in f.GraphicalItems()
                 if g.GetLayer() in (pcbnew.F_Fab, pcbnew.B_Fab) and g.GetClass() == "PCB_SHAPE"]
        if not boxes:
            return None
        return (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))

    def region(self, refs, margin):
        pts = []
        for r in refs:
            f = self.fps.get(r)
            if f:
                for p in f.Pads():
                    pts.append(bbox_mm(p.GetBoundingBox()))
        return (min(b[0] for b in pts) - margin, min(b[1] for b in pts) - margin,
                max(b[2] for b in pts) + margin, max(b[3] for b in pts) + margin)

    def track_desc(self, t):
        a, b = mmxy(t.GetStart()), mmxy(t.GetEnd())
        return "%s %s w%.2f (%.2f,%.2f)-(%.2f,%.2f)" % (t.GetNetname(), t.GetLayerName(), TMM(t.GetWidth()), a[0], a[1], b[0], b[1])


# ------------------------------------------------------------------ connectivity of narrow segment groups
def seg_endpoint_graph(m, segs, tol=0.001):
    """Union-find over segments sharing endpoints (same layer) or joined through a same-net via."""
    parent = list(range(len(segs)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i

    def union(i, j):
        parent[find(i)] = find(j)

    ends = []
    for i, t in enumerate(segs):
        for e in (mmxy(t.GetStart()), mmxy(t.GetEnd())):
            ends.append((i, e, t.GetLayer(), t.GetNetCode()))
    for (i, e1, l1, n1), (j, e2, l2, n2) in ((x, y) for k, x in enumerate(ends) for y in ends[k + 1:]):
        if i != j and n1 == n2 and l1 == l2 and dist(e1, e2) < tol:
            union(i, j)
    for v in m.vias:
        vp, r = mmxy(v.GetPosition()), TMM(v.GetWidth(F)) / 2
        hit = [i for (i, e, l, n) in ends if n == v.GetNetCode() and dist(e, vp) <= r]
        for i in hit[1:]:
            union(hit[0], i)
    groups = collections.defaultdict(list)
    for i in range(len(segs)):
        groups[find(i)].append(i)
    return list(groups.values())


def endpoint_connected(m, t, e, tol=0.001):
    """True if segment end e (mm) of track t touches same-net copper other than t itself."""
    code, layer = t.GetNetCode(), t.GetLayer()
    for o in m.segs + m.arcs:
        if o is t or o.GetNetCode() != code or o.GetLayer() != layer:
            continue
        if pt_seg(e, mmxy(o.GetStart()), mmxy(o.GetEnd())) <= TMM(o.GetWidth()) / 2 + tol:
            return True
    for v in m.vias:
        if v.GetNetCode() == code and dist(e, mmxy(v.GetPosition())) <= TMM(v.GetWidth(F)) / 2 + tol:
            return True
    for p in m.pads:
        if p.GetNetCode() == code and p.IsOnLayer(layer) and m.padpoly(p, layer).Contains(V(*e), -1, FMM(tol)):
            return True
    for z in m.zones + m.tdrops:
        if z.GetNetCode() == code and m.zone_fill(z, layer).Contains(V(*e), -1, FMM(tol)):
            return True
    return False


def touches(m, e, code, layer, tol=0.01):
    """Where does point e land: list of ('pad', ref.num) / ('zone',) / ('via',) of the same net."""
    out = []
    for p in m.pads:
        if p.GetNetCode() == code and p.IsOnLayer(layer) and m.padpoly(p, layer).Contains(V(*e), -1, FMM(tol)):
            out.append(("pad", "%s.%s" % (p.GetParentFootprint().GetReference(), p.GetNumber())))
    for z in m.zones:
        if z.GetNetCode() == code and m.zone_fill(z, layer).Contains(V(*e), -1, FMM(tol)):
            out.append(("zone", z.GetZoneName() or "zone"))
    return out


def net_terminal_groups(m, code, layer, terminals, w, thermal_gap=0.5):
    """Erode the net's copper on one layer by w/2 and return groups of terminal pads that stay joined.
    terminals: list of (ref, num).  Thermal-relief pads are detected with a ring of gap + w/2."""
    cu = m.copper(code, layer)
    e = inflate(cu, -(w / 2 - 0.01)) if w > 0 else copy_ps(cu)
    parent = {t: t for t in terminals}

    def find(x):
        while parent[x] != x:
            x = parent[x]
        return x

    owners = collections.defaultdict(list)
    missing = []
    for t in terminals:
        p = m.pad(*t)
        if p is None or not p.IsOnLayer(layer):
            missing.append(t); continue
        # thermal-relief pads: spokes are deliberately narrow, so probe beyond the relief gap
        # (a starved thermal is DRC's job: starved_thermal)
        z = pad_in_zone_outline(m, p, layer)
        solid = z is None or pad_zone_coverage(m, p, layer) >= 0.98
        gap = max(thermal_gap, TMM(z.GetThermalReliefGap())) if z is not None else thermal_gap
        # copper >= w wide must reach the pad: after erosion it lies within w/2 of the pad edge.  This also
        # accepts pads that are themselves narrower than w (0603/1206 pads), whose own width is not a neck.
        probe = m.padpoly(p, layer, (0.0 if solid else gap) + w / 2 + 0.05)
        hit = False
        for i in range(e.OutlineCount()):
            if inter_area(probe, sub_poly(e, i)) > 1e-6:
                owners[i].append(t); hit = True
        if not hit:
            missing.append(t)
    for i, ts in owners.items():
        for t in ts[1:]:
            parent[find(t)] = find(ts[0])
    groups = collections.defaultdict(list)
    for t in terminals:
        groups[find(t)].append(t)
    return [g for g in groups.values()], missing


def net_path(m, net, a, b_):
    """Shortest routed centreline path (track segments, vias, pads as nodes) between pads a and b of one net."""
    import heapq
    code = m.code(net)
    G = collections.defaultdict(list)
    key = lambda p: (round(p[0], 4), round(p[1], 4))
    for t in [t for t in m.segs if t.GetNetCode() == code]:
        p, q = key(mmxy(t.GetStart())), key(mmxy(t.GetEnd()))
        L = dist(p, q); G[p].append((q, L)); G[q].append((p, L))
    nodes = list(G)
    for v in m.vias:
        if v.GetNetCode() == code:
            c = mmxy(v.GetPosition()); r = TMM(v.GetWidth(F)) / 2
            for n in nodes:
                if dist(n, c) <= r + 1e-3:
                    G[n].append((("via", c), 0)); G[("via", c)].append((n, 0))
    for ref, num in (a, b_):
        p = m.pad(ref, num)
        if p is None:
            return None, None
        for n in nodes:
            if p.IsOnLayer(F) and m.padpoly(p, F).Contains(V(*n), -1, FMM(0.001)):
                G[n].append(((ref, num), 0)); G[(ref, num)].append((n, 0))
    best = {a: 0}; prev = {}; pq = [(0, a)]
    while pq:
        d, u = heapq.heappop(pq)
        if u == b_:
            break
        if d > best.get(u, 1e9):
            continue
        for v, w in G[u]:
            if d + w < best.get(v, 1e9):
                best[v] = d + w; prev[v] = u; heapq.heappush(pq, (d + w, v))
    if b_ not in best:
        return None, None
    pts, u = [], b_
    while u != a:
        u = prev[u]
        if isinstance(u[0], float):
            pts.append(u)
    pts.reverse()
    return [m.pxy(*a)] + pts + [m.pxy(*b_)], best[b_]


def net_dead_items(m, code):
    """Copper of one net that has no path to any pad: ('island', desc) for zone-fill outlines,
    ('floating', desc) for tracks/vias.  Nodes overlap-joined per layer; vias and PTH pads join layers."""
    nodes = []          # (kind, desc, {layer: poly}, is_pad)
    for p in m.pads:
        if p.GetNetCode() == code:
            nodes.append(("pad", "", {l: m.padpoly(p, l, 0.005) for l in (F, B) if p.IsOnLayer(l) and p.FlashLayer(l)}, True))
    for t in m.segs + m.arcs + m.vias:
        if t.GetNetCode() != code:
            continue
        polys = {}
        for l in (F, B):
            if t.IsOnLayer(l):
                s = pcbnew.SHAPE_POLY_SET(); t.TransformShapeToPolygon(s, l, FMM(0.005), ERR, pcbnew.ERROR_INSIDE); polys[l] = s
        d = ("via %s @(%.2f,%.2f)" % ((t.GetNetname(),) + mmxy(t.GetPosition()))) if t.Type() == pcbnew.PCB_VIA_T else m.track_desc(t)
        nodes.append(("floating", d, polys, False))
    for z in m.zones + m.tdrops:
        if z.GetNetCode() != code:
            continue
        for l in (F, B):
            fill = m.zone_fill(z, l)
            for i in range(fill.OutlineCount()):
                sp = sub_poly(fill, i)
                bb = bbox_mm(sp.BBox())
                # +5 um so that same-net copper that merely TOUCHES counts as connected (KiCad does the same)
                nodes.append(("island", "%s%s %s island %.3f mm^2 at (%.1f,%.1f)-(%.1f,%.1f)" % (
                    (z.GetNetname(), " teardrop" if z.IsTeardropArea() else "", LNAME[l], area_mm2(sp)) + bb), {l: inflate(sp, 0.005)}, False))
    n = len(nodes)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i

    boxes = [{l: bbox_mm(ps.BBox()) for l, ps in nd[2].items()} for nd in nodes]
    for i in range(n):
        for j in range(i + 1, n):
            if find(i) == find(j):
                continue
            for l in (F, B):
                if l in boxes[i] and l in boxes[j] and boxes_overlap(boxes[i][l], boxes[j][l]) and inter_area(nodes[i][2][l], nodes[j][2][l]) > 0:
                    parent[find(i)] = find(j); break
    live = {find(i) for i in range(n) if nodes[i][3]}
    return [(nd[0], nd[1]) for i, nd in enumerate(nodes) if not nd[3] and find(i) not in live]


def pad_zone_coverage(m, p, layer):
    """Fraction of the pad area covered by same-net zone fill on that layer (1.0 = solid connection)."""
    pp = m.padpoly(p, layer)
    a = area_mm2(pp)
    if a <= 0:
        return 0.0
    fill = pcbnew.SHAPE_POLY_SET()
    for z in m.zones:
        if z.GetNetCode() == p.GetNetCode():
            fill.Append(m.zone_fill(z, layer))
    if fill.OutlineCount() == 0:
        return 0.0
    fill.Simplify()
    return inter_area(pp, fill) / a


def pad_in_zone_outline(m, p, layer):
    for z in m.zones:
        if z.GetNetCode() == p.GetNetCode() and z.IsOnLayer(layer) and z.Outline().Contains(p.GetPosition()):
            return z
    return None


# ------------------------------------------------------------------ snapshot + external tools
def snapshot(board_path, run_dir, sch_override):
    snap = os.path.join(run_dir, "snap"); os.makedirs(snap, exist_ok=True)
    src_dir, stem = os.path.dirname(os.path.abspath(board_path)), os.path.splitext(os.path.basename(board_path))[0]
    dst = os.path.join(snap, "chk.kicad_pcb")
    shutil.copy2(board_path, dst)
    notes = []
    for ext in (".kicad_pro", ".kicad_dru"):
        s = os.path.join(src_dir, stem + ext)
        if os.path.exists(s):
            shutil.copy2(s, os.path.join(snap, "chk" + ext))
        else:
            notes.append("no %s next to the board" % ext)
    sch = sch_override or os.path.join(src_dir, stem + ".kicad_sch")
    if not os.path.exists(sch):
        sch = os.path.join(PROJECT_DIR, "pcb_revC.kicad_sch"); notes.append("schematic taken from project folder (read-only copy)")
    shutil.copy2(sch, os.path.join(snap, "chk.kicad_sch"))
    for name in ("fp-lib-table", "sym-lib-table", "buckRevC.kicad_sym", "buckRevC.pretty"):
        s = os.path.join(src_dir, name)
        if not os.path.exists(s):
            s = os.path.join(PROJECT_DIR, name)
        if os.path.isdir(s):
            shutil.copytree(s, os.path.join(snap, name), dirs_exist_ok=True)
        elif os.path.exists(s):
            shutil.copy2(s, os.path.join(snap, name))
    return dst, notes


def run_drc(pcb, run_dir):
    out_json, out_rpt = os.path.join(run_dir, "drc.json"), os.path.join(run_dir, "drc.rpt")
    r1 = subprocess.run([KCLI, "pcb", "drc", "--severity-all", "--schematic-parity", "--format", "json", "-o", out_json, pcb],
                        capture_output=True, text=True, timeout=600)
    subprocess.run([KCLI, "pcb", "drc", "--severity-all", "--schematic-parity", "-o", out_rpt, pcb],
                   capture_output=True, text=True, timeout=600)
    data = json.load(open(out_json, encoding="utf-8")) if os.path.exists(out_json) else None
    return data, (r1.stdout or "") + (r1.stderr or ""), r1.returncode


# ------------------------------------------------------------------ checks
def chk_drc(A, m, drc, drc_log, rc, dru_path):
    if drc is None:
        A.add("DRC-1", "kicad-cli DRC ran", "FAIL", "no DRC report produced (rc=%s)" % rc, drc_log.splitlines()[-5:]); return
    viol, unc, par = drc.get("violations", []), drc.get("unconnected_items", []), drc.get("schematic_parity", [])

    def fmt(v):
        its = "; ".join("%s @(%.2f,%.2f)" % (i.get("description", ""), i["pos"]["x"], i["pos"]["y"]) for i in v.get("items", [])[:2])
        return "[%s/%s] %s :: %s" % (v.get("type"), v.get("severity"), v.get("description", ""), its)

    errs = [v for v in viol if v.get("severity") == "error" and v.get("type") not in SILK_DRC]
    A.add("DRC-1", "DRC errors (excluding unconnected and silk) = 0", "PASS" if not errs else A.lvl("always"),
          "%d error(s): %s" % (len(errs), dict(collections.Counter(v["type"] for v in errs))), [fmt(v) for v in errs])
    A.add("DRC-2", "Unconnected items = 0", "PASS" if not unc else A.lvl("complete"), "%d unconnected" % len(unc),
          [fmt(v) for v in unc])
    parity_failed = "Failed to fetch schematic netlist" in drc_log
    A.add("DRC-3", "Schematic parity = 0 issues", "FAIL" if parity_failed else ("PASS" if not par else A.lvl("always")),
          "parity NOT RUN (schematic netlist unavailable)" if parity_failed else "%d parity issue(s)" % len(par), [fmt(v) for v in par])
    dang = [v for v in viol if v.get("type") in ("track_dangling", "via_dangling")]
    cu_w = [v for v in viol if v.get("severity") != "error" and v.get("type") not in SILK_DRC | ENV_DRC | {"track_dangling", "via_dangling"}]
    A.add("DRC-4", "DRC copper warnings = 0 (dangling: always; others: complete)",
          worst("PASS", A.lvl("always") if dang else "PASS", A.lvl("complete") if cu_w else "PASS"),
          "%d dangling, %d other copper warning(s): %s" % (len(dang), len(cu_w), dict(collections.Counter(v["type"] for v in cu_w))),
          [fmt(v) for v in dang + cu_w])
    env = [v for v in viol if v.get("type") in ENV_DRC]
    if env:
        A.add("DRC-6", "DRC environment warnings (library tables)", "WARN", "%d" % len(env), [fmt(v) for v in env])
    # custom rules
    det = []
    if not dru_path or not os.path.exists(dru_path):
        A.add("DRC-5", "Custom .kicad_dru: Power >= 1.5 mm, Drive >= 0.5 mm", A.lvl("always"), "no .kicad_dru next to the board"); return
    txt = open(dru_path, encoding="utf-8", errors="replace").read()
    rules = re.findall(r"\(rule\s+(\"[^\"]*\"|\S+)(.*?)(?=\n\s*\(rule\s|\Z)", txt, re.S)
    ok_p = ok_d = False
    for name, body in rules:
        mw = re.search(r"track_width\s*\(min\s+([\d.]+)\s*mm\)", body)
        cond = re.search(r"\(condition\s+\"([^\"]*)\"", body)
        det.append("rule %s: condition=%s track_width_min=%s" % (name, cond.group(1) if cond else "-", mw.group(1) if mw else "-"))
        if mw and cond and "Power" in cond.group(1) and float(mw.group(1)) >= W_POWER - 1e-6:
            ok_p = True
        if mw and cond and "Drive" in cond.group(1) and float(mw.group(1)) >= W_DRIVE - 1e-6:
            ok_d = True
    syntax_err = [l for l in drc_log.splitlines() if re.search(r"rule|dru", l, re.I) and re.search(r"error|invalid|unknown", l, re.I)]
    if not txt.lstrip().startswith("(version"):
        syntax_err.append("file does not start with (version N)")
    # effectiveness probe: kicad-cli silently ignores a broken .kicad_dru, so plant a 1.0 mm VMID stub and a
    # 0.3 mm GATE stub (inside their own pads) in a throw-away copy and require DRC to flag both
    eff = probe_rules(os.path.dirname(dru_path))
    det.append("probe: %s" % eff[1])
    st = "PASS" if ok_p and ok_d and not syntax_err and eff[0] else A.lvl("always")
    A.add("DRC-5", "Custom .kicad_dru: Power >= 1.5 mm, Drive >= 0.5 mm (+0.3 mm Power clearance), and DRC actually enforces them", st,
          "power rule %s, drive rule %s, syntax problems %d, enforced by DRC %s" % (ok_p, ok_d, len(syntax_err), eff[0]), det + syntax_err)


def probe_rules(snap_dir):
    pdir = os.path.join(os.path.dirname(snap_dir), "rule_probe")
    if os.path.isdir(pdir):
        shutil.rmtree(pdir)
    shutil.copytree(snap_dir, pdir)
    pcb = os.path.join(pdir, "chk.kicad_pcb")
    b = pcbnew.LoadBoard(pcb)
    stubs = []
    for net, ref, num, w in (("VMID", "L1", "1", 1.0), ("GATE", "Q1", "1", 0.3)):
        f = b.FindFootprintByReference(ref)
        pad = [q for q in f.Pads() if q.GetNumber() == num][0] if f else None
        if pad is None or pad.GetNetname() != net:
            return (False, "cannot build probe (%s.%s missing)" % (ref, num))
        c = pad.GetPosition()
        t = pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(c.x - FMM(0.2), c.y)); t.SetEnd(pcbnew.VECTOR2I(c.x + FMM(0.2), c.y))
        t.SetWidth(FMM(w)); t.SetLayer(F); t.SetNet(pad.GetNet()); b.Add(t)
        stubs.append((net, w))
    # clearance probe: a floating 0.25 mm GND stub with a 0.25 mm edge gap to a Power SMD pad, at a spot with
    # no other copper within 0.6 mm -> must be flagged under a 0.3 mm Power clearance, not under the 0.2 default
    clr_spot = None
    mm_ = Model(b)
    others = pcbnew.SHAPE_POLY_SET()
    for code in mm_.netname:
        if code > 0:
            others.Append(mm_.copper(code, F))
    others.Simplify()
    for q in [q for q in mm_.pads if q.GetNetname() in POWER and q.GetAttribute() == pcbnew.PAD_ATTRIB_SMD]:
        cx, cy = mmxy(q.GetPosition()); hx, hy = TMM(q.GetSize().x) / 2, TMM(q.GetSize().y) / 2
        if q.GetOrientationDegrees() % 180 != 0:
            hx, hy = hy, hx
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            sx, sy = cx + dx * (hx + 0.25 + 0.125), cy + dy * (hy + 0.25 + 0.125)
            seg = (sx - 0.15 * abs(dy), sy - 0.15 * abs(dx), sx + 0.15 * abs(dy), sy + 0.15 * abs(dx))
            probe = box_poly(min(seg[0], seg[2]) - 0.125 - 0.6, min(seg[1], seg[3]) - 0.125 - 0.6, max(seg[0], seg[2]) + 0.125 + 0.6, max(seg[1], seg[3]) + 0.125 + 0.6)
            hit = copy_ps(others); hit.BooleanIntersection(probe)
            own = copy_ps(mm_.padpoly(q, F)); own.BooleanIntersection(probe)
            if abs(area_mm2(hit) - area_mm2(own)) < 1e-4:
                clr_spot = (seg, q); break
        if clr_spot:
            break
    if clr_spot:
        (x1, y1, x2, y2), q = clr_spot
        t = pcbnew.PCB_TRACK(b); t.SetStart(V(x1, y1)); t.SetEnd(V(x2, y2)); t.SetWidth(FMM(0.25)); t.SetLayer(F); t.SetNet(b.FindNet("GND")); b.Add(t)
    pcbnew.SaveBoard(pcb, b)
    out = os.path.join(pdir, "probe.json")
    subprocess.run([KCLI, "pcb", "drc", "--severity-all", "--format", "json", "-o", out, pcb], capture_output=True, text=True, timeout=600)
    try:
        d = json.load(open(out, encoding="utf-8"))
    except Exception as e:  # noqa
        return (False, "probe DRC failed: %s" % e)
    tw = [v for v in d.get("violations", []) if v.get("type") == "track_width"]
    hit = {net: any("[%s]" % net in i.get("description", "") for v in tw for i in v.get("items", [])) for net, w in stubs}
    msg = "planted VMID 1.0 mm / GATE 0.3 mm stubs; DRC track_width flagged %s" % hit
    if clr_spot:
        (x1, y1, x2, y2), q = clr_spot
        cv = [v for v in d.get("violations", []) if v.get("type") == "clearance" and
              any(abs(i["pos"]["x"] - (x1 + x2) / 2) < 0.4 and abs(i["pos"]["y"] - (y1 + y2) / 2) < 0.4 for i in v.get("items", []))]
        hit["clearance"] = bool(cv)
        msg += "; GND stub 0.25 mm from %s.%s (%s) flagged: %s" % (q.GetParentFootprint().GetReference(), q.GetNumber(), q.GetNetname(),
                                                                cv[0]["description"] if cv else False)
    else:
        msg += "; no free spot for a clearance probe"
    return (all(hit.values()), msg)


def chk_rules(A, m, pro_path):
    det, bad = [], []
    try:
        p = json.load(open(pro_path, encoding="utf-8"))
    except Exception as e:  # noqa
        A.add("RUL-1", "Project rules and netclasses match the spec", A.lvl("always"), "cannot read .kicad_pro: %s" % e); return
    r = p["board"]["design_settings"]["rules"]
    cls = {c["name"]: c for c in p["net_settings"]["classes"]}

    adv = []

    def need(label, val, ok, advisory=False):
        det.append("%-44s %s%s" % (label, val, "" if ok else ("   <- advisory" if advisory else "   <- MISMATCH")))
        if not ok:
            (adv if advisory else bad).append(label)

    need("min_clearance (0.2)", r.get("min_clearance"), abs((r.get("min_clearance") or 0) - 0.2) < 1e-6)
    need("min_copper_edge_clearance (>=0.3)", r.get("min_copper_edge_clearance"), (r.get("min_copper_edge_clearance") or 0) >= 0.3 - 1e-6)
    need("min_track_width (>=0.2, JLC 0.10)", r.get("min_track_width"), (r.get("min_track_width") or 0) >= 0.2 - 1e-6)
    need("min_via_diameter / annular (0.6/0.15)", (r.get("min_via_diameter"), r.get("min_via_annular_width")),
         (r.get("min_via_diameter") or 0) >= 0.6 - 1e-6 and (r.get("min_via_annular_width") or 0) >= 0.15 - 1e-6)
    need("min_hole_clearance (>=0.28 JLC PTH-track)", r.get("min_hole_clearance"), (r.get("min_hole_clearance") or 0) >= 0.28 - 1e-6, True)
    need("min_text_height / thickness (1.0/0.18)", (r.get("min_text_height"), r.get("min_text_thickness")),
         (r.get("min_text_height") or 0) >= 1.0 - 1e-6 and (r.get("min_text_thickness") or 0) >= 0.18 - 1e-6)
    need("min_resolved_spokes (>=2)", r.get("min_resolved_spokes"), (r.get("min_resolved_spokes") or 0) >= 2)
    dflt = cls.get("Default", {})
    pw, dr = cls.get("Power", {}), cls.get("Drive", {})
    need("Default netclass track/clearance (0.25/0.2)", (dflt.get("track_width"), dflt.get("clearance")),
         abs((dflt.get("track_width") or 0) - W_SIG) < 1e-6 and abs((dflt.get("clearance") or 0) - 0.2) < 1e-6)
    dru_txt = ""
    dru_p = os.path.splitext(pro_path)[0] + ".kicad_dru"
    if os.path.exists(dru_p):
        dru_txt = open(dru_p, encoding="utf-8", errors="replace").read()
    dru_clr = any("Power" in body and re.search(r"clearance\s*\(min\s+0?\.3\d*\s*mm\)", body)
                  for body in re.findall(r"\(rule\s.*?(?=\n\s*\(rule\s|\Z)", dru_txt, re.S))
    need("Power netclass track width (1.5)", pw.get("track_width"), abs((pw.get("track_width") or 0) - W_POWER) < 1e-6)
    nc_clr = abs((pw.get("clearance") or 0) - 0.3) < 1e-6
    need("Power clearance 0.3 (netclass%s)" % (" or .kicad_dru rule: dru rule present" if dru_clr else ""), pw.get("clearance"),
         nc_clr, advisory=dru_clr)      # dru-only: enforced (DRC-5 probe) but the netclass panel still says 0.2 -> advisory
    need("Power netclass via (0.8/0.4)", (pw.get("via_diameter"), pw.get("via_drill")),
         abs((pw.get("via_diameter") or 0) - 0.8) < 1e-6 and abs((pw.get("via_drill") or 0) - 0.4) < 1e-6)
    need("Drive netclass track (0.5)", dr.get("track_width"), abs((dr.get("track_width") or 0) - W_DRIVE) < 1e-6)
    for net in POWER + DRIVE:
        n = m.b.FindNet(net)
        want = "Power" if net in POWER else "Drive"
        have = n.GetNetClassName() if n else "<missing net>"
        if want not in str(have).split(","):
            bad.append("net %s class %s" % (net, have)); det.append("net %-8s resolves to %s (want %s)" % (net, have, want))
    A.add("RUL-1", "Project rules and netclasses match the spec", "PASS" if not bad and not adv else (A.lvl("always") if bad else "WARN"),
          ("%d mismatch(es): %s" % (len(bad), ", ".join(bad)) if bad else "spec items as specified") +
          ("; advisory: %s (actual geometry is measured in RUL-2)" % ", ".join(adv) if adv else ""), det)


def chk_jlc_geometry(A, m):
    det, fails, warns = [], [], []
    for p in m.pads:
        if p.GetAttribute() != pcbnew.PAD_ATTRIB_PTH:
            continue
        ring = (min(TMM(p.GetSize().x), TMM(p.GetSize().y)) - max(TMM(p.GetDrillSizeX()), TMM(p.GetDrillSizeY()))) / 2
        ref = "%s.%s" % (p.GetParentFootprint().GetReference(), p.GetNumber())
        if ring < 0.18:
            fails.append("PTH %s annular ring %.3f mm < 0.18 (JLC abs min)" % (ref, ring))
        elif ring < 0.25:
            warns.append("PTH %s annular ring %.3f mm < 0.25 (JLC recommended)" % (ref, ring))
    for v in m.vias:
        d, D = TMM(v.GetDrillValue()), TMM(v.GetWidth(F))
        if d < 0.15 or D - d < 0.1:
            fails.append("via %s @(%.2f,%.2f) %.2f/%.2f below JLC 0.15 drill / +0.1 diameter" % ((v.GetNetname(),) + mmxy(v.GetPosition()) + (D, d)))
    # hole edge to other-net copper (JLC: PTH-to-track 0.28 min / 0.35 rec; via hole-to-track 0.2)
    holes = [(mmxy(p.GetPosition()), max(TMM(p.GetDrillSizeX()), TMM(p.GetDrillSizeY())) / 2, p.GetNetCode(), "PTH %s.%s" % (p.GetParentFootprint().GetReference(), p.GetNumber()), 0.28, 0.35)
             for p in m.pads if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
    holes += [(mmxy(v.GetPosition()), TMM(v.GetDrillValue()) / 2, v.GetNetCode(), "via %s" % v.GetNetname(), 0.2, 0.2) for v in m.vias]
    codes = set(m.netname)
    worst_h = None
    cubox = {}
    for oc in codes:
        for layer in (F, B):
            cu = m.copper(oc, layer)
            cubox[(oc, layer)] = bbox_mm(cu.BBox()) if cu.OutlineCount() else None
    for (c, r, code, name, mn, rec) in holes:
        hb = (c[0] - r - 1.0, c[1] - r - 1.0, c[0] + r + 1.0, c[1] + r + 1.0)
        for oc in codes:
            if oc == code or oc <= 0:
                continue
            for layer in (F, B):
                if cubox[(oc, layer)] is None or not boxes_overlap(hb, cubox[(oc, layer)]):
                    continue
                cu = m.copper(oc, layer)
                d = math.sqrt(max(cu.SquaredDistance(V(*c), False), 0)) / 1e6 - r
                if worst_h is None or d < worst_h[0]:
                    worst_h = (d, name, m.netname.get(oc, "?"), LNAME[layer])
                if d < mn:
                    fails.append("%s hole edge %.3f mm from %s copper on %s (< %.2f JLC)" % (name, d, m.netname.get(oc, "?"), LNAME[layer], mn))
                elif d < rec:
                    warns.append("%s hole edge %.3f mm from %s copper on %s (< %.2f JLC rec.)" % (name, d, m.netname.get(oc, "?"), LNAME[layer], rec))
    if worst_h:
        det.append("closest hole-to-other-net copper: %.3f mm (%s vs %s on %s)" % worst_h)
    st = A.lvl("always") if fails else ("WARN" if warns else "PASS")
    A.add("RUL-2", "JLC 2-layer capability (annular rings, via sizes, hole-to-copper)", st,
          "%d fail, %d warn; %d PTH pads, %d vias" % (len(fails), len(warns), sum(1 for h in holes if h[3].startswith("PTH")), len(m.vias)),
          det + fails + warns)


def chk_hot_loop(A, m, base):
    pts = [m.pxy(*t) for t in HOT_LOOP]
    area = shoelace(pts)
    bpts = [base.pxy(*t) for t in HOT_LOOP] if base else None
    barea = shoelace(bpts) if bpts else None
    st = "PASS" if barea is None or abs(area - barea) < 0.5 else A.lvl("always")
    A.add("PWR-1", "Hot-loop pad-centre polygon C4.1>Q1.2>Q1.3>D1.1>D1.2>C4.2", st,
          "area %.1f mm^2 (baseline %s); perimeter %.1f mm" % (area, "%.1f" % barea if barea is not None else "-",
                                                               sum(dist(a, b) for a, b in zip(pts, pts[1:] + pts[:1]))),
          ["%s.%s (%.2f,%.2f)" % (t[0], t[1], p[0], p[1]) for t, p in zip(HOT_LOOP, pts)])
    # F.Cu-only connectivity of each hot-loop link
    det, bad, missing = [], [], []
    for net, a, b in HOT_PAIRS:
        code = m.code(net)
        groups, _ = net_terminal_groups(m, code, F, [a, b], 0.0)
        same_f = any(a in g and b in g for g in groups)
        any_cu = net_connected_any_layer(m, code, a, b)
        tag = "%s %s.%s-%s.%s" % (net, a[0], a[1], b[0], b[1])
        if same_f:
            det.append("OK   %s on F.Cu" % tag)
        elif any_cu:
            bad.append(tag); det.append("BAD  %s connected only through B.Cu/vias" % tag)
        else:
            missing.append(tag); det.append("OPEN %s not yet connected" % tag)
    st = worst("PASS", A.lvl("always") if bad else "PASS", A.lvl("complete") if missing else "PASS")
    A.add("PWR-2", "Hot loop and bulk-cap links on F.Cu only", st,
          "%d on F.Cu, %d via B.Cu, %d open" % (len(HOT_PAIRS) - len(bad) - len(missing), len(bad), len(missing)), det)
    # other-net F.Cu copper inside the hot-loop polygon
    poly = pcbnew.SHAPE_POLY_SET(); poly.NewOutline()
    for x, y in pts:
        poly.Append(FMM(x), FMM(y))
    intr = []
    hot_codes = {m.code("VIN"), m.code("SW"), m.code("GND")}
    for t in m.segs + m.arcs + m.vias:
        if t.GetNetCode() in hot_codes or not t.IsOnLayer(F):
            continue
        s = pcbnew.SHAPE_POLY_SET(); t.TransformShapeToPolygon(s, F, 0, ERR, pcbnew.ERROR_INSIDE)
        if inter_area(s, poly) > 1e-4:
            intr.append(m.track_desc(t) if t.Type() != pcbnew.PCB_VIA_T else "via %s @(%.2f,%.2f)" % ((t.GetNetname(),) + mmxy(t.GetPosition())))
    A.add("PWR-7", "No other-net F.Cu copper inside the hot-loop polygon", "PASS" if not intr else A.lvl("always"),
          "%d intruder(s)" % len(intr), intr)


def net_connected_any_layer(m, code, a, b):
    """Crude: pads a and b connected using copper of both layers joined by vias/PTH pads."""
    gF, _ = net_terminal_groups(m, code, F, [a, b], 0.0)
    if any(a in g and b in g for g in gF):
        return True
    # build a small graph of F/B outlines linked by vias and PTH pads
    nodes = {}
    for layer in (F, B):
        cu = m.copper(code, layer)
        for i in range(cu.OutlineCount()):
            nodes[(layer, i)] = sub_poly(cu, i)
    parent = {k: k for k in nodes}

    def find(x):
        while parent[x] != x:
            x = parent[x]
        return x

    links = [mmxy(v.GetPosition()) for v in m.vias if v.GetNetCode() == code]
    links += [mmxy(p.GetPosition()) for p in m.pads if p.GetNetCode() == code and p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
    for c in links:
        ks = [k for k, s in nodes.items() if s.Contains(V(*c), -1, FMM(0.01))]
        for k in ks[1:]:
            parent[find(k)] = find(ks[0])

    def owner(t):
        p = m.pad(*t)
        out = set()
        for k, s in nodes.items():
            if p.IsOnLayer(k[0]) and s.Contains(p.GetPosition(), -1, FMM(0.01)):
                out.add(find(k))
        return out

    return bool(owner(a) & owner(b))


def classify_narrow(m, net):
    """Return (taps, bad) for the narrow (< W_POWER) segment groups of a power net."""
    code = m.code(net)
    segs = [t for t in m.segs + m.arcs if t.GetNetCode() == code and TMM(t.GetWidth()) < W_POWER - 1e-3]
    if not segs:
        return [], []
    taps, bad = [], []
    wide = [t for t in m.segs + m.arcs if t.GetNetCode() == code and TMM(t.GetWidth()) >= W_POWER - 1e-3]
    for grp in seg_endpoint_graph(m, segs):
        gs = [segs[i] for i in grp]
        tap_pads, src = set(), []
        for t in gs:
            for e in (mmxy(t.GetStart()), mmxy(t.GetEnd())):
                hits = touches(m, e, code, t.GetLayer())
                for kind, what in hits:
                    if kind == "pad":
                        r, n = what.split(".")
                        if (r, n) in TAPS.get(net, {}):
                            tap_pads.add((r, n))
                        else:
                            src.append((what, e))
                    else:
                        src.append(("zone", e))
                for w in wide:
                    if w.GetLayer() == t.GetLayer() and pt_seg(e, mmxy(w.GetStart()), mmxy(w.GetEnd())) <= TMM(w.GetWidth()) / 2 + 0.01:
                        src.append(("wide-track", e))
        src_names = sorted(set(s[0] for s in src))
        # one physical attachment may appear as pad+zone at the same point, and several attachments inside the SAME
        # same-net fill outline are one node of wide copper (the narrow track is merely embedded in the zone)
        fills = {}
        for z in m.zones:
            if z.GetNetCode() == code:
                for layer in (F, B):
                    fl = m.zone_fill(z, layer)
                    for i in range(fl.OutlineCount()):
                        fills[(z.m_Uuid.AsString(), layer, i)] = (layer, sub_poly(fl, i))
        def node_of(pt, layer):
            for k, (l2, sp) in fills.items():
                if l2 == layer and sp.Contains(V(*pt), -1, FMM(0.01)):
                    return ("fill",) + k
            return None
        src_pts, nodes = [], []
        for s_ in src:
            nd = node_of(s_[1], gs[0].GetLayer())
            if nd is not None and nd in nodes:
                continue
            if nd is None and any(dist(s_[1], q) <= 0.5 for q in src_pts):
                continue
            src_pts.append(s_[1]); nodes.append(nd if nd is not None else ("pt", len(nodes)))
        wmin = min(TMM(t.GetWidth()) for t in gs)
        rec = {"net": net, "segs": gs, "tap_pads": tap_pads, "src": src, "src_names": src_names, "src_pts": src_pts, "wmin": wmin}
        if tap_pads and len(src_pts) <= 1:
            rec["need"] = max(TAPS[net][tp] for tp in tap_pads)
            taps.append(rec)
        else:
            bad.append(rec)
    return taps, bad


def chk_widths(A, m, drc):
    # power
    det, fails, warns = [], [], []
    tap_recs = {}
    for net in POWER:
        code = m.code(net)
        ws = [TMM(t.GetWidth()) for t in m.segs + m.arcs if t.GetNetCode() == code]
        taps, bad = classify_narrow(m, net)
        tap_recs[net] = taps
        det.append("%-6s %3d segs, min %s mm, %d tap branch(es), %d illegal narrow group(s)" % (net, len(ws), "%.2f" % min(ws) if ws else "-", len(taps), len(bad)))
        for rec in bad:
            t = rec["segs"][0]
            fails.append("%s narrow copper w%.2f not a recognised tap (touches %s; tap pads %s): %s" % (
                net, rec["wmin"], rec["src_names"] or "nothing", sorted("%s.%s" % tp for tp in rec["tap_pads"]) or "none", m.track_desc(t)))
        for rec in taps:
            pref = max([TAP_PREF.get(tp, 0) for tp in rec["tap_pads"]] + [rec["need"]])
            narrow_len = sum(TMM(t.GetLength()) for t in rec["segs"] if TMM(t.GetWidth()) < pref - 1e-3)
            if rec["wmin"] < rec["need"] - 1e-3:
                fails.append("%s tap to %s is %.2f mm < %.2f" % (net, sorted("%s.%s" % tp for tp in rec["tap_pads"]), rec["wmin"], rec["need"]))
            elif rec["wmin"] < pref - 1e-3:
                warns.append("%s tap to %s has %.2f mm of %.2f mm copper (< %.2f preferred, >= %.2f hard)" % (
                    net, sorted("%s.%s" % tp for tp in rec["tap_pads"]), narrow_len, rec["wmin"], pref, rec["need"]))
            else:
                warns.append("%s tap to %s at %.2f mm (spec Power>=1.5 applies unless the .kicad_dru exempts this branch)" % (
                    net, sorted("%s.%s" % tp for tp in rec["tap_pads"]), rec["wmin"]))
    st = A.lvl("always") if fails else ("WARN" if warns else "PASS")
    tw = [v for v in (drc or {}).get("violations", []) if v.get("type") == "track_width"]
    if any(f for f in fails if "not a recognised tap" in f) and not tw:
        det.append("NOTE: checker found narrow power copper but DRC reports 0 track_width violations -> custom rule not effective")
    A.add("PWR-4", "Power tracks >= 1.5 mm (IPC-2152 floor 1.0 mm @2 A/10 C); legal taps only", st,
          "%d fail, %d tap note(s)" % (len(fails), len(warns)), det + fails + warns)
    # drive and signals
    for cid, title, nets, wmin in (("DRV-1", "Drive nets >= 0.5 mm", DRIVE, W_DRIVE), ):
        bad = [m.track_desc(t) for t in m.segs + m.arcs if m.netname.get(t.GetNetCode()) in nets and TMM(t.GetWidth()) < wmin - 1e-3]
        A.add(cid, title, "PASS" if not bad else A.lvl("always"), "%d narrow segment(s)" % len(bad), bad)
    special = set(POWER) | set(DRIVE)
    bad, gnd_narrow = [], []
    for t in m.segs + m.arcs:
        n = m.netname.get(t.GetNetCode(), "")
        if n in special:
            continue
        w = TMM(t.GetWidth())
        if w < W_SIG - 1e-3:
            bad.append(m.track_desc(t))
        elif n == "GND" and w < W_DRIVE - 1e-3:
            gnd_narrow.append(m.track_desc(t))
    unc = [m.track_desc(t) for t in m.segs + m.arcs if m.netname.get(t.GetNetCode(), "").startswith("unconnected-")]
    st = worst("PASS", A.lvl("always") if bad or unc else "PASS", "WARN" if gnd_narrow else "PASS")
    A.add("SIG-1", "Signal tracks >= 0.25 mm (GND tracks < 0.5 mm flagged)", st,
          "%d below 0.25, %d GND below 0.5, %d on unconnected-* nets" % (len(bad), len(gnd_narrow), len(unc)), bad + gnd_narrow + unc)
    return tap_recs


def chk_layers(A, m):
    det, bad = [], []
    pc = {m.code(n) for n in POWER}
    for t in m.segs + m.arcs:
        if t.GetNetCode() in pc and t.GetLayer() != F:
            bad.append("track " + m.track_desc(t))
    for z in m.zones:
        if z.GetNetCode() in pc and z.IsOnLayer(B):
            bad.append("zone %s on B.Cu" % z.GetNetname())
    for v in m.vias:
        if v.GetNetCode() in pc:
            bad.append("via %s @(%.2f,%.2f) %.2f/%.2f" % ((v.GetNetname(),) + mmxy(v.GetPosition()) + (TMM(v.GetWidth(F)), TMM(v.GetDrillValue()))))
    A.add("PWR-3", "Power nets only on F.Cu (no B.Cu tracks/zones, no power vias)", "PASS" if not bad else A.lvl("always"),
          "%d item(s) off F.Cu" % len(bad), bad)
    # B.Cu signal jumps
    bsegs = [t for t in m.segs + m.arcs if t.GetLayer() == B and m.netname.get(t.GetNetCode()) != "GND"]
    jumps = []
    for grp in seg_endpoint_graph(m, bsegs):
        L = sum(TMM(bsegs[i].GetLength()) for i in grp)
        jumps.append((L, m.netname.get(bsegs[grp[0]].GetNetCode()), bsegs[grp[0]]))
    long_ = ["%s B.Cu run %.1f mm starting %s" % (n, L, m.track_desc(t)) for L, n, t in sorted(jumps, key=lambda x: -x[0]) if L > 10.0]
    A.add("SIG-6", "Bottom-layer signal jumps <= ~10 mm each", "PASS" if not long_ else "WARN",
          "%d B.Cu run(s), longest %.1f mm" % (len(jumps), max([j[0] for j in jumps] or [0])), long_)
    # B.Cu under the power stage
    hot = m.region(HOT_REFS, 1.0); stage = m.region(STAGE_REFS, 1.0)
    hp, sp = box_poly(*hot), box_poly(*stage)
    in_hot, in_stage = [], []
    gnd = m.code("GND")
    for t in m.segs + m.arcs:
        if t.GetLayer() != B or t.GetNetCode() == gnd:
            continue
        s = pcbnew.SHAPE_POLY_SET(); t.TransformShapeToPolygon(s, B, 0, ERR, pcbnew.ERROR_INSIDE)
        if inter_area(s, hp) > 1e-4:
            in_hot.append(m.track_desc(t))
        elif inter_area(s, sp) > 1e-4:
            in_stage.append(m.track_desc(t))
    gfill = m.copper(gnd, B, tracks=False, pads=False)
    cov_h = inter_area(gfill, hp) / area_mm2(hp)
    cov_s = inter_area(gfill, sp) / area_mm2(sp)
    outline = pcbnew.SHAPE_POLY_SET(); m.b.GetBoardPolygonOutlines(outline, False)
    cov_b = inter_area(gfill, outline) / max(area_mm2(outline), 1e-9)
    has_pour = gfill.OutlineCount() > 0
    st = worst("PASS", A.lvl("always") if in_hot else "PASS", "WARN" if in_stage else "PASS",
               A.lvl("complete") if not has_pour or cov_h < 0.90 else "PASS", "WARN" if has_pour and (cov_s < 0.85 or cov_b < 0.75) else "PASS")
    A.add("PWR-8", "B.Cu GND plane unbroken under the power stage", st,
          "B.Cu GND coverage: hot-loop box %.0f %%, power-stage box %.0f %%, board %.0f %%; %d non-GND B.Cu tracks under hot loop, %d under rest of stage" % (
              100 * cov_h, 100 * cov_s, 100 * cov_b, len(in_hot), len(in_stage)),
          ["hot-loop box (%.1f,%.1f)-(%.1f,%.1f), power-stage box (%.1f,%.1f)-(%.1f,%.1f)" % (hot + stage)] +
          ["under hot loop: " + x for x in in_hot] + ["under stage: " + x for x in in_stage])


def chk_necks(A, m):
    det, fails, warns, opens = [], [], [], []
    plans = []
    for net in POWER:
        terms = [(p.GetParentFootprint().GetReference(), p.GetNumber()) for p in m.pads
                 if p.GetNetname() == net and (p.GetParentFootprint().GetReference(), p.GetNumber()) not in TAPS.get(net, {})]
        if net == "SW":
            plans.append((net, F, terms, W_SW_MIN))
        else:
            plans.append((net, F, terms, W_POWER))
    plans.append(("GND(hot loop)", F, HOT_GND, W_POWER))
    for net, layer, terms, w in plans:
        code = m.code(net.split("(")[0])
        g0, miss0 = net_terminal_groups(m, code, layer, terms, 0.0)
        if len(g0) > 1 or miss0:
            opens.append("%s: terminals on %s in %d separate group(s) %s -- incomplete" % (
                net, LNAME[layer], len(g0), [["%s.%s" % t for t in g] for g in g0 if len(g) > 1] or "none joined"))
        for grp in [g for g in g0 if len(g) > 1]:          # neck-test every joined cluster, even if the net is incomplete
            gw, missw = net_terminal_groups(m, code, layer, grp, w)
            label = "%s{%s}" % (net, ",".join("%s.%s" % t for t in grp))
            if len(gw) == 1 and not missw:
                det.append("OK   %s joined by copper >= %.1f mm on %s" % (label, w, LNAME[layer])); continue
            gi, missi = net_terminal_groups(m, code, layer, grp, W_IPC_2A)
            ipc = len(gi) == 1 and not missi
            fails.append("%s: neck < %.1f mm splits it into %s%s" % (label, w, [["%s.%s" % t for t in g] for g in gw],
                                                                    "; still >= %.1f mm (IPC floor)" % W_IPC_2A if ipc else "; ALSO < %.1f mm IPC-2152 floor" % W_IPC_2A))
    zmin = ["zone %s %s min width %.2f mm" % (z.GetNetname(), z.GetLayerName(), TMM(z.GetMinThickness())) for z in m.zones if z.GetNetname() in POWER]
    st = worst("PASS", A.lvl("always") if fails else "PASS", A.lvl("complete") if opens else "PASS")
    A.add("PWR-5", "Power copper necks (erosion test): Power >= 1.5 mm, SW >= 2.0 mm, hot-loop GND >= 1.5 mm", st,
          "%d fail, %d deferred" % (len(fails), len(opens)), det + fails + opens + zmin)


def chk_sw_area(A, m):
    code = m.code("SW")
    cu = m.copper(code, F)
    pads = pcbnew.SHAPE_POLY_SET()
    for p in m.pads:
        if p.GetNetCode() == code and p.IsOnLayer(F):
            p.TransformShapeToPolygon(pads, F, 0, ERR, pcbnew.ERROR_INSIDE)
    pads.Simplify()
    tot, pa = area_mm2(cu), area_mm2(pads)
    extra = tot - pa
    st = "PASS" if extra <= 80.0 else "WARN"
    A.add("PWR-6", "SW node copper area minimal (judgement: <= 80 mm^2 beyond pads)", st,
          "SW F.Cu copper %.1f mm^2 (pads %.1f, routed/zone %.1f); B.Cu SW copper %.1f mm^2" % (tot, pa, extra, area_mm2(m.copper(code, B))))


def chk_drive(A, m):
    det, bad = [], []
    for net in DRIVE:
        vs = [v for v in m.vias if v.GetNetname() == net]
        allowed = 2 if net == "DRV_B" else 0
        det.append("%-6s vias %d (allowed %d)" % (net, len(vs), allowed))
        if len(vs) > allowed:
            bad.append("%s has %d via(s): %s" % (net, len(vs), ["(%.2f,%.2f)" % mmxy(v.GetPosition()) for v in vs]))
    dev = len(bad) == 1 and bad[0].startswith("DRV_B has 3 ")
    A.add("DRV-2", "Drive nets on F.Cu; only one jump on DRV_B (3 vias = accepted S2 deviation: 3 enclosed F.Cu islands)",
          "PASS" if not bad else ("WARN" if dev else A.lvl("always")), "%d violation(s)%s" % (len(bad), " (accepted deviation)" if dev else ""), det + bad)
    pts = [m.pxy(*t) for t in GATE_LOOP]
    P = {k: net_path(m, *k) for k in (("BOOT", ("C9", "1"), ("Q4", "3")), ("DRV_E", ("Q4", "2"), ("R5", "1")), ("GATE", ("R5", "2"), ("Q1", "1")),
                                      ("SW", ("L1", "2"), ("C9", "2")), ("DRV_E", ("R5", "1"), ("Q5", "2")), ("SW", ("Q5", "3"), ("L1", "2")))}
    det = ["%s %s.%s->%s.%s current path %s" % (k[0], k[1][0], k[1][1], k[2][0], k[2][1], "%.1f mm" % v[1] if v[0] else "open") for k, v in P.items()]
    if all(v[0] for v in P.values()):
        bo, de, ga, sw, de2, sw2 = [v[0] for v in P.values()]
        q13 = m.pxy("Q1", "3")
        a_on = shoelace(bo + de + ga + [q13] + sw[1:]); a_off = shoelace(list(reversed(ga)) + de2 + sw2[:-1] + [q13])
        gl = P[("GATE", ("R5", "2"), ("Q1", "1"))][1] + P[("DRV_E", ("Q4", "2"), ("R5", "1"))][1]
        st = "PASS" if a_on <= 80 and a_off <= 50 and gl <= 10 else "WARN"
        A.add("DRV-3", "Gate loops small (judgement: turn-on <= 80, turn-off <= 50 mm^2; Q4.E->R5->Q1.G <= 10 mm)", st,
              "turn-on loop %.1f mm^2, turn-off loop %.1f mm^2, gate current path %.1f mm (pad-centre placement area %.1f mm^2)" % (a_on, a_off, gl, shoelace(pts)), det)
    else:
        A.add("DRV-3", "Gate loops small", "N/A" if A.stage < 2 else A.lvl("complete"), "gate-drive paths not complete yet", det)


def chk_angles(A, m):
    bad_seg, zero, near = [], [], []
    for t in m.segs:
        a, b = mmxy(t.GetStart()), mmxy(t.GetEnd())
        if dist(a, b) < 1e-4:
            zero.append(m.track_desc(t)); continue
        ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 45.0
        dev = min(ang, 45.0 - ang)
        if dev > 1.0:
            bad_seg.append("%s angle off-45 by %.1f deg" % (m.track_desc(t), dev))
        elif dev > 0.05:
            near.append("%s off-45 by %.2f deg (pad-centre offset? end the track inside the pad on the exact axis)" % (m.track_desc(t), dev))
    st = worst("PASS", A.lvl("always") if bad_seg or zero else "PASS", "WARN" if near else "PASS")
    A.add("GEO-1", "Every straight segment at a multiple of 45 deg (arcs allowed; >1 deg FAIL, >0.05 deg WARN)", st,
          "%d off-grid, %d nearly, %d zero-length of %d segments (%d arcs exempt)" % (len(bad_seg), len(near), len(zero), len(m.segs), len(m.arcs)),
          bad_seg + zero + near)
    # junctions
    joints = collections.defaultdict(list)
    for t in m.segs:
        a, b = mmxy(t.GetStart()), mmxy(t.GetEnd())
        if dist(a, b) < 1e-4:
            continue
        for p, q in ((a, b), (b, a)):
            key = (t.GetNetCode(), t.GetLayer(), round(p[0], 3), round(p[1], 3))
            L = dist(p, q)
            joints[key].append(((q[0] - p[0]) / L, (q[1] - p[1]) / L))
    # T-junctions onto segment interiors
    for key in list(joints):
        code, layer, x, y = key
        for t in m.segs:
            if t.GetNetCode() != code or t.GetLayer() != layer:
                continue
            a, b = mmxy(t.GetStart()), mmxy(t.GetEnd())
            if min(dist((x, y), a), dist((x, y), b)) < 0.002:
                continue
            if pt_seg((x, y), a, b) < 0.002:
                L = dist(a, b)
                u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
                joints[key] += [u, (-u[0], -u[1])]
    fails, warns = [], []
    for (code, layer, x, y), dirs in joints.items():
        if len(dirs) < 2:
            continue
        e = (x, y)
        covered = any(p.GetNetCode() == code and p.IsOnLayer(layer) and m.padpoly(p, layer).Contains(V(*e), -1, FMM(0.001)) for p in m.pads) or \
            any(v.GetNetCode() == code and dist(e, mmxy(v.GetPosition())) <= TMM(v.GetWidth(F)) / 2 for v in m.vias) or \
            any(z.GetNetCode() == code and m.zone_fill(z, layer).Contains(V(*e), -1, FMM(0.001)) for z in m.zones)
        if covered:
            continue
        angs = [math.degrees(math.acos(max(-1.0, min(1.0, u[0] * v[0] + u[1] * v[1])))) for i, u in enumerate(dirs) for v in dirs[i + 1:]]
        amin = min(angs)
        where = "%s %s (%.2f,%.2f) %d-way min angle %.0f deg" % (m.netname.get(code), LNAME.get(layer, layer), x, y, len(dirs), amin)
        if len(dirs) == 2 and amin <= 90.0 + 0.5:
            fails.append(where)
        elif len(dirs) > 2 and amin < 90.0 - 0.5:
            fails.append(where)
        elif len(dirs) > 2 and amin <= 90.0 + 0.5:
            warns.append(where + " (T-junction)")
    st = A.lvl("always") if fails else ("WARN" if warns else "PASS")
    A.add("GEO-2", "No <=90 deg bends or acute junctions (T-junction 90 deg = WARN)", st,
          "%d fail, %d T-junction warn, %d joints checked (joints inside pads/vias/same-net fill skipped)" % (len(fails), len(warns), len(joints)), fails + warns)


def chk_dangling(A, m):
    bad = []
    for t in m.segs + m.arcs:
        for e in (mmxy(t.GetStart()), mmxy(t.GetEnd())):
            if not endpoint_connected(m, t, e):
                bad.append("dangling end (%.2f,%.2f) of %s" % (e[0], e[1], m.track_desc(t)))
    for v in m.vias:
        c, r = mmxy(v.GetPosition()), TMM(v.GetWidth(F)) / 2
        layers = []
        for layer in (F, B):
            hit = any(t.GetNetCode() == v.GetNetCode() and t.GetLayer() == layer and
                      min(dist(c, mmxy(t.GetStart())), dist(c, mmxy(t.GetEnd()))) <= r + 0.001 for t in m.segs + m.arcs)
            hit = hit or any(z.GetNetCode() == v.GetNetCode() and m.zone_fill(z, layer).Contains(V(*c)) for z in m.zones)
            hit = hit or any(p.GetNetCode() == v.GetNetCode() and p.IsOnLayer(layer) and m.padpoly(p, layer).Contains(V(*c), -1, FMM(r)) for p in m.pads)
            if hit:
                layers.append(LNAME[layer])
        if len(layers) < 2:
            bad.append("via %s @(%.2f,%.2f) connected on %s only" % (v.GetNetname(), c[0], c[1], layers or "no layer"))
    # duplicated / overlapping collinear segments
    dup = []
    for i, t in enumerate(m.segs):
        a, b = mmxy(t.GetStart()), mmxy(t.GetEnd())
        for o in m.segs[i + 1:]:
            if o.GetNetCode() != t.GetNetCode() or o.GetLayer() != t.GetLayer():
                continue
            c, d = mmxy(o.GetStart()), mmxy(o.GetEnd())
            if pt_seg(c, a, b) < 0.001 and pt_seg(d, a, b) < 0.001 or pt_seg(a, c, d) < 0.001 and pt_seg(b, c, d) < 0.001:
                dup.append("overlapping %s / %s" % (m.track_desc(t), m.track_desc(o)))
    st = worst("PASS", A.lvl("always") if bad else "PASS", "WARN" if dup else "PASS")
    A.add("GEO-3", "No dangling track ends / single-layer vias; no duplicate segments", st,
          "%d dangling, %d duplicate" % (len(bad), len(dup)), bad + dup)


def chk_vias(A, m):
    fails, warns, det = [], [], []
    pc = {m.code(n) for n in POWER}
    sizes = collections.Counter()
    for v in m.vias:
        D, d = round(TMM(v.GetWidth(F)), 3), round(TMM(v.GetDrillValue()), 3)
        sizes[(v.GetNetname() if v.GetNetCode() in pc else ("GND" if v.GetNetname() == "GND" else "sig/drive"), D, d)] += 1
        where = "via %s @(%.2f,%.2f) %.2f/%.2f" % ((v.GetNetname(),) + mmxy(v.GetPosition()) + (D, d))
        if v.GetNetCode() in pc:
            if D < 0.8 - 1e-3 or d < 0.4 - 1e-3:
                fails.append(where + " power via below 0.8/0.4")
        elif (D, d) not in ((0.6, 0.3), (0.8, 0.4)):
            if D < 0.6 - 1e-3 or (D - d) / 2 < 0.15 - 1e-3:
                fails.append(where + " below 0.6/0.3 project minimum")
            else:
                warns.append(where + " non-standard size")
        if v.GetViaType() != pcbnew.VIATYPE_THROUGH:
            fails.append(where + " not a through via")
    det += ["%s %.2f/%.2f x%d" % (k + (n,)) for k, n in sorted(sizes.items())]
    A.add("VIA-1", "Via sizes: signal 0.6/0.3, power 0.8/0.4 (JLC: drill>=0.15, dia>=drill+0.1)",
          A.lvl("always") if fails else ("WARN" if warns else "PASS"), "%d vias; %d fail, %d warn" % (len(m.vias), len(fails), len(warns)), det + fails + warns)
    # power layer changes (cluster within 3 mm)
    groups = []
    for v in [v for v in m.vias if v.GetNetCode() in pc]:
        c = mmxy(v.GetPosition())
        for g in groups:
            if g[0] == v.GetNetname() and any(dist(c, q) < 3.0 for q in g[1]):
                g[1].append(c); break
        else:
            groups.append([v.GetNetname(), [c]])
    det = ["%s layer change at (%.1f,%.1f): %d via(s) (spec >= 2; ROHM 0.6 A per 0.4 mm via -> >= 4 for 1.9 A fault)" % (g[0], g[1][0][0], g[1][0][1], len(g[1])) for g in groups]
    st = "PASS" if not groups else A.lvl("always")
    A.add("VIA-2", "Power layer changes: none expected (spec); if present >= 2 vias each", st, "%d power layer change(s)" % len(groups), det)
    # GND vias near the power GND pads and stitching density
    gvias = [mmxy(v.GetPosition()) for v in m.vias if v.GetNetname() == "GND"]
    det, miss = [], []
    for t in POWER_GND_PADS:
        p = m.pxy(*t)
        dmin = min([dist(p, q) for q in gvias] or [float("inf")])
        det.append("%s.%s nearest GND via %s" % (t[0], t[1], "%.1f mm" % dmin if dmin < 1e6 else "none"))
        if dmin > 3.0:
            miss.append("%s.%s" % t)
    gnd_f = m.copper(m.code("GND"), F, tracks=False, pads=False)
    stage = m.region(STAGE_REFS, 2.0)
    worst_gap, samples = 0.0, 0
    if gnd_f.OutlineCount():
        x = stage[0]
        while x <= stage[2]:
            y = stage[1]
            while y <= stage[3]:
                if gnd_f.Contains(V(x, y)):
                    samples += 1
                    d = min([dist((x, y), q) for q in gvias] or [99.0])
                    worst_gap = max(worst_gap, d)
                y += 1.0
            x += 1.0
    det.append("F.Cu GND fill in power-stage box: %d samples, worst distance to a GND via %.1f mm (criterion <= 5 mm)" % (samples, worst_gap))
    st = worst("PASS", A.lvl("complete") if miss else "PASS", A.lvl("complete") if samples == 0 or worst_gap > 5.0 else "PASS")
    A.add("VIA-3", "GND vias <= 3 mm from each power GND pad; stitching <= 5 mm in the power stage", st,
          "%d GND vias; pads without nearby via: %s" % (len(gvias), miss or "none"), det)


def chk_zones(A, m, board_path):
    det = []
    gnd = m.code("GND")
    for z in m.zones:
        for layer in (F, B):
            if not z.IsOnLayer(layer):
                continue
            fill = m.zone_fill(z, layer)
            det.append("zone net=%-6s %s prio=%d conn=%s gap=%.2f spoke=%.2f minw=%.2f islands=%s fill=%.0f mm^2 outlines=%d" % (
                z.GetNetname(), LNAME[layer], z.GetAssignedPriority(), {0: "none", 1: "thermal", 2: "solid", 3: "THT-thermal", -1: "inherit"}.get(z.GetPadConnection(), z.GetPadConnection()),
                TMM(z.GetThermalReliefGap()), TMM(z.GetThermalReliefSpokeWidth()), TMM(z.GetMinThickness()),
                {0: "always", 1: "never", 2: "area"}.get(z.GetIslandRemovalMode(), z.GetIslandRemovalMode()), area_mm2(fill), fill.OutlineCount()))
    A.add("ZON-1", "Zone inventory", "PASS" if m.zones else "N/A", "%d zones, %d teardrop zones" % (len(m.zones), len(m.tdrops)), det)
    # pours
    pours = {layer: [z for z in m.zones if z.GetNetCode() == gnd and z.IsOnLayer(layer)] for layer in (F, B)}
    outline = pcbnew.SHAPE_POLY_SET(); m.b.GetBoardPolygonOutlines(outline, False)
    det, bad = [], []
    for layer in (F, B):
        big = [z for z in pours[layer] if area_mm2(z.Outline()) > 0.5 * area_mm2(outline)]
        if not big:
            bad.append("no board-size GND pour on %s" % LNAME[layer])
        for z in big:
            det.append("GND pour %s priority %d" % (LNAME[layer], z.GetAssignedPriority()))
            if z.GetAssignedPriority() != min(o.GetAssignedPriority() for o in m.zones if o.IsOnLayer(layer)):
                bad.append("GND pour on %s is not the lowest priority on that layer" % LNAME[layer])
            for o in m.zones:
                if o is z or not o.IsOnLayer(layer) or o.GetNetCode() == gnd:
                    continue
                if inter_area(o.Outline(), z.Outline()) > 0 and o.GetAssignedPriority() <= z.GetAssignedPriority():
                    bad.append("%s zone (prio %d) does not out-rank the GND pour (prio %d) on %s" % (o.GetNetname(), o.GetAssignedPriority(), z.GetAssignedPriority(), LNAME[layer]))
    A.add("ZON-2", "GND pours on F.Cu and B.Cu at lowest priority; power zones out-rank them", "PASS" if not bad else A.lvl("complete"),
          "; ".join(bad) if bad else "ok", det + bad)
    # orphan islands and floating copper: per-net connectivity graph, a node is live only if it reaches a pad
    orph, floating = [], []
    for code in sorted({z.GetNetCode() for z in m.zones} | {t.GetNetCode() for t in m.segs + m.arcs + m.vias}):
        if code <= 0:
            continue
        for kind, desc in net_dead_items(m, code):
            (orph if kind == "island" else floating).append(desc)
    slivers = []
    for z in m.zones:
        for layer in (F, B):
            fl = m.zone_fill(z, layer)
            for i in range(fl.OutlineCount()):
                a = area_mm2(sub_poly(fl, i))
                if a < 0.1:
                    slivers.append("%s %s fill fragment %.3f mm^2 at %s (connected; merges with adjacent same-net copper in Gerber)" % (
                        z.GetZoneName() or z.GetNetname(), LNAME[layer], a, tuple(round(v, 2) for v in bbox_mm(sub_poly(fl, i).BBox()))))
    st = worst("PASS", A.lvl("always") if orph else "PASS", A.lvl("always") if floating else "PASS", "WARN" if slivers else "PASS")
    A.add("ZON-3", "0 orphan zone islands; no floating tracks/vias (no path to any pad); fill fragments < 0.1 mm^2 flagged", st,
          "%d orphan island(s), %d floating item(s), %d tiny fragment(s)" % (len(orph), len(floating), len(slivers)), orph + floating + slivers)
    # stale fills: refill a second in-memory copy and compare
    b2 = pcbnew.LoadBoard(board_path)
    before = {}
    for z in b2.Zones():
        for layer in (F, B):
            if z.IsOnLayer(layer):
                s = pcbnew.SHAPE_POLY_SET()
                if z.HasFilledPolysForLayer(layer):
                    s.Append(z.GetFilledPolysList(layer))
                before[(z.m_Uuid.AsString(), layer)] = area_mm2(s)
    stale = []
    if before:
        pcbnew.ZONE_FILLER(b2).Fill(b2.Zones())
        for z in b2.Zones():
            for layer in (F, B):
                if z.IsOnLayer(layer):
                    s = pcbnew.SHAPE_POLY_SET()
                    if z.HasFilledPolysForLayer(layer):
                        s.Append(z.GetFilledPolysList(layer))
                    a0, a1 = before.get((z.m_Uuid.AsString(), layer), 0.0), area_mm2(s)
                    if abs(a1 - a0) > max(0.5, 0.01 * a1):
                        stale.append("%s%s %s fill %.1f mm^2 saved vs %.1f mm^2 refilled" % (z.GetNetname(), " (teardrop)" if z.IsTeardropArea() else "", LNAME[layer], a0, a1))
    A.add("ZON-4", "Zone fills up to date (in-memory refill matches saved fill)", "N/A" if not before else ("PASS" if not stale else A.lvl("complete")),
          "%d stale" % len(stale), stale)
    # edge clearance 0.5 mm
    inner = inflate(outline, -(0.5 - 0.01))
    out = []
    for z in m.zones:
        for layer in (F, B):
            fill = m.zone_fill(z, layer)
            if fill.OutlineCount() == 0:
                continue
            t = copy_ps(fill); t.BooleanSubtract(inner)
            if area_mm2(t) > 0.001:
                out.append("%s %s: %.3f mm^2 of fill within 0.5 mm of the board edge, bbox %s" % (z.GetNetname(), LNAME[layer], area_mm2(t), tuple(round(v, 1) for v in bbox_mm(t.BBox()))))
    A.add("ZON-5", "Zone fill >= 0.5 mm from board edge", "N/A" if not m.zones else ("PASS" if not out else A.lvl("always")), "%d zone layer(s) too close" % len(out), out)
    # pad connections
    fails, warns, det = [], [], []
    for ref in SMD_POWER_REFS:
        f = m.fps.get(ref)
        for p in f.Pads():
            if not p.GetNumber() or not p.GetNetname():
                continue
            z = pad_in_zone_outline(m, p, F)
            if not z:
                continue
            cov = pad_zone_coverage(m, p, F)
            if cov < 0.98:
                fails.append("%s.%s (%s) in %s zone but only %.0f %% covered -> thermal/partial, want solid" % (ref, p.GetNumber(), p.GetNetname(), z.GetNetname(), 100 * cov))
            else:
                det.append("%s.%s solid (%.0f %%)" % (ref, p.GetNumber(), 100 * cov))
    for p in m.pads:
        if p.GetAttribute() != pcbnew.PAD_ATTRIB_PTH or not p.GetNetname():
            continue
        key = (p.GetParentFootprint().GetReference(), p.GetNumber())
        tot_w, solid_layers, spokes_desc = 0.0, [], []
        for layer in (F, B):
            z = pad_in_zone_outline(m, p, layer)
            if not z:
                continue
            cov = pad_zone_coverage(m, p, layer)
            if cov >= 0.98:
                solid_layers.append(LNAME[layer]); continue
            gap = max(TMM(z.GetThermalReliefGap()), TMM(p.GetLocalThermalGapOverride() or 0))
            ring = copy_ps(m.padpoly(p, layer, 0.6 * gap)); ring.BooleanSubtract(m.padpoly(p, layer))
            fill = m.zone_fill(z, layer)
            sp = copy_ps(fill); sp.BooleanIntersection(ring)
            n = sp.OutlineCount()
            w = area_mm2(sp) / (0.6 * gap) if gap > 0 else 0.0
            tot_w += w
            spokes_desc.append("%s %d spoke(s) total %.2f mm" % (LNAME[layer], n, w))
            if n < 2:
                fails.append("%s.%s %s: %d thermal spoke(s) (< 2)" % (key + (LNAME[layer], n)))
        if solid_layers:
            warns.append("%s.%s solid zone connection on %s (spec: THT thermals for hand soldering)" % (key + (solid_layers,)))
        if spokes_desc:
            det.append("%s.%s %s" % (key + ("; ".join(spokes_desc),)))
            if key in POWER_THT and tot_w < W_IPC_2A and not solid_layers:
                fails.append("%s.%s power THT pad total spoke width %.2f mm < %.1f mm (IPC 2 A)" % (key + (tot_w, W_IPC_2A)))
            elif key in POWER_THT and tot_w < W_POWER and not solid_layers:
                warns.append("%s.%s power THT pad total spoke width %.2f mm < %.1f mm (project)" % (key + (tot_w, W_POWER)))
    any_zone = bool(m.zones)
    A.add("ZON-6", "SMD power pads solid; THT pads thermal with >= 2 spokes (power THT total spokes >= 1.5 mm)",
          "N/A" if not any_zone else (A.lvl("always") if fails else ("WARN" if warns else "PASS")), "%d fail, %d warn" % (len(fails), len(warns)), fails + warns + det)


def chk_sw_proximity(A, m, tap_recs):
    sw = m.code("SW")
    swcu = {layer: m.copper(sw, layer) for layer in (F, B)}
    sens_items = []
    for t in m.segs + m.arcs:
        n = m.netname.get(t.GetNetCode(), "")
        if n in SENSE:
            sens_items.append(("sense", t))
        elif n in CTRL or n.startswith("Net-(J6-Pin_9") or n == "TRIG":
            sens_items.append(("ctrl", t))
    for net in ("VOUT", "VIN"):
        for rec in tap_recs.get(net, []):
            if ("R7", "1") in rec["tap_pads"] or ("R9", "1") in rec["tap_pads"]:
                sens_items += [("sense", t) for t in rec["segs"]]
    fails, warns, det = [], [], []
    mins = {}
    for kind, t in sens_items:
        layer, other = t.GetLayer(), (B if t.GetLayer() == F else F)
        seg = pcbnew.SEG(t.GetStart(), t.GetEnd())
        hw = TMM(t.GetWidth()) / 2
        d = (math.sqrt(max(swcu[layer].SquaredDistanceToSeg(seg), 0)) / 1e6 - hw) if swcu[layer].OutlineCount() else float("inf")
        cross = swcu[other].OutlineCount() and swcu[other].Collide(seg, FMM(hw))
        n = t.GetNetname()
        mins[n] = min(mins.get(n, float("inf")), d)
        lim_f, lim_w = (1.0, 3.0) if kind == "sense" else (0.5, 2.0)
        if cross:
            fails.append("%s crosses SW copper on the other layer: %s" % (n, m.track_desc(t)))
        if d < lim_f:
            fails.append("%s %.2f mm from SW copper (< %.1f): %s" % (n, d, lim_f, m.track_desc(t)))
        elif d < lim_w:
            warns.append("%s %.2f mm from SW copper (< %.1f): %s" % (n, d, lim_w, m.track_desc(t)))
    det = ["min edge gap to SW copper (same layer): " + ", ".join("%s %.2f" % (k, v) for k, v in sorted(mins.items()))] if mins else []
    A.add("SIG-2", "Sense/ADC/PWM/LSW tracks away from SW copper (judgement: sense >= 1 mm FAIL/3 mm WARN, ctrl 0.5/2 mm)",
          "N/A" if not sens_items else (A.lvl("always") if fails else ("WARN" if warns else "PASS")),
          "%d sensitive segment(s); %d fail, %d warn" % (len(sens_items), len(fails), len(warns)), det + fails + warns)
    # under inductor / diode bodies
    bodies = {r: m.fp_body(r) for r in ("L1", "L2", "D1")}
    fails, warns = [], []
    exempt = set(POWER) | {"GND"}
    for t in m.segs + m.arcs:
        n = m.netname.get(t.GetNetCode(), "")
        if n in exempt:
            continue
        tb = bbox_mm(t.GetBoundingBox())
        for r, bb in bodies.items():
            if bb and boxes_overlap(tb, bb):
                s = pcbnew.SHAPE_POLY_SET(); t.TransformShapeToPolygon(s, t.GetLayer(), 0, ERR, pcbnew.ERROR_INSIDE)
                if inter_area(s, box_poly(*bb)) > 1e-4:
                    (fails if n in SENSE else warns).append("%s under %s body: %s" % (n, r, m.track_desc(t)))
    A.add("SIG-3", "No signal tracks under L1/L2/D1 bodies (ROHM 7(d), 5)", A.lvl("always") if fails else ("WARN" if warns else "PASS"),
          "%d sense, %d other" % (len(fails), len(warns)), fails + warns)


def chk_sense(A, m, tap_recs):
    det, fails, warns = [], [], []
    for net, tap, okpads, warnpads in (("VOUT", ("R7", "1"), [("C6", "1"), ("C7", "1")], [("C8", "1")]),
                                       ("VIN", ("R9", "1"), [("C1", "1"), ("C2", "1"), ("C3", "1"), ("C4", "1"), ("C5", "1")], [])):
        recs = [r for r in tap_recs.get(net, []) if tap in r["tap_pads"]]
        if not recs:
            det.append("%s tap to %s.%s not routed (or not narrow)" % ((net,) + tap)); continue
        rec = recs[0]
        pad_src = [(w, e) for w, e in rec["src"] if w not in ("zone", "wide-track")]
        zoned_tp = [tp for tp in rec["tap_pads"] if tp != tap and pad_in_zone_outline(m, m.pad(*tp), F) is not None]
        if pad_src:
            ap = m.pxy(*pad_src[0][0].split("."))
        elif zoned_tp:
            ap = m.pxy(*zoned_tp[0]); rec["src_names"] = ["%s.%s (tap pad in %s zone)" % (zoned_tp[0] + (net,))]
        elif rec["src_pts"]:
            ap = rec["src_pts"][0]
        else:
            fails.append("%s tap to %s.%s does not attach to %s power copper" % ((net,) + tap + (net,))); continue
        d_ok = min(dist(ap, m.pxy(*p)) for p in okpads)
        d_w = min([dist(ap, m.pxy(*p)) for p in warnpads] or [99])
        names = rec["src_names"]
        desc = "%s tap to %s.%s attaches at (%.2f,%.2f) [%s], %.1f mm from nearest of %s" % ((net,) + tap + (ap[0], ap[1], ",".join(names), d_ok, ["%s.%s" % p for p in okpads]))
        acc = ACCEPTED_DEV.get(("SIG-4", net, "%.1f,%.1f" % ap))
        if d_ok <= 2.5:
            det.append("OK   " + desc)
        elif d_w <= 2.5:
            warns.append("WARN " + desc + " (spare/DNP cap)")
        elif acc:
            warns.append("WARN " + desc + " -- accepted deviation: " + acc)
        else:
            fails.append("BAD  " + desc + " -- not a Kelvin tap at the caps")
        det.append("%s tap length %.1f mm, width %.2f mm" % (net, sum(TMM(t.GetLength()) for t in rec["segs"]), rec["wmin"]))
        # a same-net zone swallows the track: the effective Kelvin point is where the tap leaves the fill
        fill = pcbnew.SHAPE_POLY_SET()
        for z in m.zones:
            if z.GetNetname() == net:
                fill.Append(m.zone_fill(z, F))
        if fill.OutlineCount():
            fill.Simplify()
            inside = sum(inter_area(fill, ps) / max(TMM(t.GetWidth()), 1e-6) for t in rec["segs"]
                         for ps in [(lambda s: (t.TransformShapeToPolygon(s, t.GetLayer(), 0, ERR, pcbnew.ERROR_INSIDE), s)[1])(pcbnew.SHAPE_POLY_SET())])
            det.append("%s tap runs %.1f mm inside %s zone fill" % (net, inside, net))
            if inside > 2.0:
                warns.append("%s tap is merged into the %s zone for %.1f mm -- Kelvin point is where it exits the fill" % (net, net, inside))
    st = A.lvl("always") if fails else ("WARN" if warns else ("PASS" if any(d.startswith("OK") for d in det) else A.lvl("complete")))
    unrouted = sum(1 for d in det if "not routed" in d)
    A.add("SIG-4", "VOUT tap is a Kelvin trace from C6/C7 pad 1; VIN tap from the input caps", st,
          "%d fail, %d warn, %d tap(s) not routed yet" % (len(fails), len(warns), unrouted), det + fails + warns)
    # filter caps close to ADC pins + sense routed length
    det = []
    d1 = dist(m.pxy("C10", "1"), m.pxy("J6", "11")); d2 = dist(m.pxy("C11", "1"), m.pxy("J6", "10"))
    det.append("C10.1-J6.11 %.1f mm, C11.1-J6.10 %.1f mm (placement)" % (d1, d2))
    L = {n: sum(TMM(t.GetLength()) for t in m.segs + m.arcs if t.GetNetname() == n) for n in SENSE}
    vs = {n: sum(1 for v in m.vias if v.GetNetname() == n) for n in SENSE}
    det.append("routed: " + ", ".join("%s %.1f mm (%d vias)" % (n, L[n], vs[n]) for n in SENSE))
    st = "PASS" if d1 <= 6 and d2 <= 6 and all(L[n] <= 15 for n in SENSE) else "WARN"
    A.add("SIG-5", "ADC filter caps C10/C11 close to J6.11/J6.10; ADC nets short (<= 15 mm judgement)", st, "; ".join(det))
    # PWM / LSW routes
    det, warns = [], []
    pv = sum(1 for v in m.vias if v.GetNetname() == "PWM")
    pl = sum(TMM(t.GetLength()) for t in m.segs + m.arcs if t.GetNetname() == "PWM")
    straight = dist(m.pxy("J5", "12"), m.pxy("R1", "1")) + dist(m.pxy("R1", "1"), m.pxy("TP5", "1"))
    det.append("PWM %.1f mm routed, %d vias (J5.12-R1.1 + TP5 stub straight-line %.1f mm)" % (pl, pv, straight))
    if pv:
        warns.append("PWM has %d via(s); spec: straight F.Cu" % pv)
    if pl > 1.5 * straight and pl > 0:
        warns.append("PWM route %.1f mm > 1.5x straight-line" % pl)
    j5y, j6y = m.pxy("J5", "1")[1], m.pxy("J6", "1")[1]
    lb = [t for t in m.segs + m.arcs if t.GetNetname() == "LSW_B"]
    between = any(j5y + 1.5 < (mmxy(t.GetStart())[1] + mmxy(t.GetEnd())[1]) / 2 < j6y - 1.5 for t in lb)
    det.append("LSW_B %d segs, runs between the socket rows: %s" % (len(lb), between))
    if lb and not between:
        warns.append("LSW_B does not run between the NUCLEO socket rows (spec)")
    A.add("SIG-7", "PWM straight J5.12->R1.1 (+TP5 stub), LSW_B between socket rows", "WARN" if warns else ("PASS" if pl or lb else "N/A"),
          "; ".join(det), warns)
    # ROHM: input and output cap grounds 1-2 cm apart (placement)
    dmin = min(dist(m.pxy(a, "2"), m.pxy(b, "2")) for a in ("C1", "C2", "C3", "C4") for b in ("C6", "C7", "C8"))
    A.add("PWR-9", "CIN and COUT grounds >= 10 mm apart (ROHM 3/6, placement)", "PASS" if dmin >= 10 else "WARN", "%.1f mm" % dmin)


def chk_teardrops(A, m):
    elig, have, miss = 0, 0, []
    td_polys = [(z.GetNetCode(), z.Outline()) for z in m.tdrops]
    items = []
    for v in m.vias:
        tr = [t for t in m.segs + m.arcs if t.GetNetCode() == v.GetNetCode() and dist(mmxy(v.GetPosition()), mmxy(t.GetStart())) < TMM(v.GetWidth(F)) / 2 + 1e-3 or
              t.GetNetCode() == v.GetNetCode() and dist(mmxy(v.GetPosition()), mmxy(t.GetEnd())) < TMM(v.GetWidth(F)) / 2 + 1e-3]
        tr = [t for t in tr if TMM(t.GetWidth()) < 0.9 * TMM(v.GetWidth(F))]
        if tr:
            items.append(("via %s" % v.GetNetname(), v.GetNetCode(), mmxy(v.GetPosition()), [(F, None), (B, None)], v, None))
    for p in m.pads:
        if not p.GetNetname():
            continue
        size = min(TMM(p.GetSize().x), TMM(p.GetSize().y))
        for layer in (F, B):
            if not p.IsOnLayer(layer):
                continue
            tr = [t for t in m.segs + m.arcs if t.GetNetCode() == p.GetNetCode() and t.GetLayer() == layer and TMM(t.GetWidth()) < 0.9 * size and
                  (m.padpoly(p, layer).Contains(t.GetStart(), -1, FMM(0.001)) or m.padpoly(p, layer).Contains(t.GetEnd(), -1, FMM(0.001)))]
            if tr and pad_in_zone_outline(m, p, layer) is None:      # KiCad default: no teardrop on pads inside a zone
                items.append(("pad %s.%s %s" % (p.GetParentFootprint().GetReference(), p.GetNumber(), LNAME[layer]), p.GetNetCode(), mmxy(p.GetPosition()), [(layer, None)], None, p))
    for name, code, c, layers, v, p in items:
        elig += 1
        probe = box_poly(c[0] - 0.3, c[1] - 0.3, c[0] + 0.3, c[1] + 0.3) if v is not None else m.padpoly(p, layers[0][0], 0.05)
        if any(nc == code and inter_area(probe, ol) > 0 for nc, ol in td_polys):
            have += 1
        else:
            miss.append("%s @(%.2f,%.2f) has no teardrop" % (name, c[0], c[1]))
    st = "N/A" if not elig else ("PASS" if not miss else A.lvl("complete"))
    A.add("TDR-1", "Teardrops on track-connected pads and vias (KiCad filters: track < 90 % of pad, not zone-connected)", st,
          "%d/%d eligible connections have teardrops; %d teardrop zones" % (have, elig, len(m.tdrops)), miss)


def body_poly(m, ref):
    """Component body as a polygon: the F.Fab circle for round parts, else the F.Fab bounding box (inductors 12.5 mm)."""
    f = m.fps[ref]
    circ = [g for g in f.GraphicalItems() if g.GetLayer() in (pcbnew.F_Fab, pcbnew.B_Fab) and g.GetClass() == "PCB_SHAPE" and g.GetShape() == pcbnew.SHAPE_T_CIRCLE]
    if circ and ref not in BODY_OVERRIDE:
        g = circ[0]; c = mmxy(g.GetCenter()); rr = TMM(g.GetRadius())
        s = pcbnew.SHAPE_POLY_SET(); s.NewOutline()
        for k in range(72):
            a = 2 * math.pi * k / 72; s.Append(FMM(c[0] + rr * math.cos(a)), FMM(c[1] + rr * math.sin(a)))
        return s
    bb = m.fp_body(ref)
    return box_poly(*bb) if bb else None


def texts_on_silk(m):
    """Yield (owner_ref or None, text item, layer, string, visible)."""
    out = []
    for d in m.b.GetDrawings():
        if d.GetClass() in ("PCB_TEXT", "PCB_TEXTBOX") and d.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            out.append((None, d, d.GetLayer(), str(d.GetShownText(False) if hasattr(d, "GetShownText") else d.GetText()), True))
    for ref, f in m.fps.items():
        for fld in f.GetFields():
            if fld.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
                out.append((ref, fld, fld.GetLayer(), str(fld.GetShownText(False)), fld.IsVisible()))
        for g in f.GraphicalItems():
            if g.GetClass() in ("PCB_TEXT", "PCB_TEXTBOX") and g.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
                out.append((ref, g, g.GetLayer(), str(g.GetShownText(False)), g.IsVisible() if hasattr(g, "IsVisible") else True))
    return out


def chk_silk(A, m, drc):
    lv = A.lvl("final")
    texts = [t for t in texts_on_silk(m) if t[4]]
    small = []
    for ref, t, layer, s, vis in texts:
        h, th = TMM(t.GetTextHeight()), TMM(t.GetEffectiveTextPenWidth())
        if h < 1.0 - 1e-3 or th < 0.18 - 1e-3:
            small.append("%s'%s' on %s h=%.2f stroke=%.2f @(%.1f,%.1f)" % (((ref + ":") if ref else "", s, pcbnew.BOARD.GetStandardLayerName(layer), h, th) + mmxy(t.GetPosition())))
    thin = []
    for g in list(m.b.GetDrawings()) + [g for f in m.fps.values() for g in f.GraphicalItems()]:
        if g.GetClass() == "PCB_SHAPE" and g.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS) and 0 < TMM(g.GetWidth()) < 0.15 - 1e-3:
            thin.append("silk line %.3f mm @(%.1f,%.1f)" % ((TMM(g.GetWidth()),) + mmxy(g.GetPosition())))
    A.add("SLK-1", "Silk text >= 1.0 mm high, >= 0.18 mm stroke (project; JLC 1.0 mm / 0.15 mm)", "PASS" if not small else lv,
          "%d small text(s) of %d visible texts" % (len(small), len(texts)), small)
    A.add("SLK-7", "Silk graphic lines >= 0.15 mm (JLC legend min; KLC footprints use 0.12 mm -> advisory)", "PASS" if not thin else "WARN",
          "%d silk line(s) thinner than 0.15 mm (mostly library outlines)" % len(thin), thin[:5])
    sv_all = [v for v in (drc or {}).get("violations", []) if v.get("type") in SILK_DRC]
    acc = [v for v in sv_all if v.get("type") == "silk_edge_clearance" and
           any(re.match(r"(Polygon|Line|Rectangle|Arc) of J[1-4] on F\.Silkscreen", i.get("description", "")) for i in v.get("items", []))]
    sv = [v for v in sv_all if v not in acc]
    A.add("SLK-2", "DRC silk: 0 overlaps, 0 silk on pads, 0 edge clips, 0 text-size/mirror issues (overhanging J1-J4 library silk clipped by the edge = accepted)",
          "PASS" if not sv_all else ("WARN" if not sv else lv),
          "%d: %s%s" % (len(sv), dict(collections.Counter(v["type"] for v in sv)), "; %d accepted (connector silk at the board edge)" % len(acc) if acc else ""),
          ["[%s] %s" % (v["type"], "; ".join("%s @(%.1f,%.1f)" % (i["description"], i["pos"]["x"], i["pos"]["y"]) for i in v["items"][:2])) for v in sv_all])
    # references visible and not under a body
    bodies = {r: m.fp_body(r) for r in m.fps}
    nucleo = None
    for d in m.b.GetDrawings():
        if d.GetLayer() == pcbnew.Dwgs_User and d.GetClass() == "PCB_SHAPE":
            bb = bbox_mm(d.GetBoundingBox())
            if bb[2] - bb[0] > 40 and bb[3] - bb[1] > 15:
                nucleo = bb; break
    bad, warn = [], []
    for ref, f in sorted(m.fps.items()):
        r = f.Reference()
        on_silk = r.IsVisible() and r.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS)
        if ref.startswith("TP"):
            if on_silk:
                warn.append("%s reference still on silk (spec: TPx refs to F.Fab, net name on silk)" % ref)
            continue
        if not on_silk:
            bad.append("%s reference not visible on a silk layer (%s, visible=%s)" % (ref, r.GetLayerName(), r.IsVisible())); continue
        tb = bbox_mm(r.GetBoundingBox())
        glyph = pcbnew.SHAPE_POLY_SET(); r.TransformShapeToPolygon(glyph, r.GetLayer(), 0, ERR, pcbnew.ERROR_INSIDE)
        for o, bb in bodies.items():
            if bb and boxes_overlap(tb, bb, 0.0):
                bp = body_poly(m, o)
                ov = inter_area(glyph, bp) if bp else 0.0
                if ov > 0.005:
                    bad.append("%s reference (%.1f,%.1f) glyphs overlap %s body by %.3f mm^2" % ((ref,) + mmxy(r.GetPosition()) + (o, ov)))
                elif bp is not None:
                    gap = min(math.sqrt(max(bp.SquaredDistance(glyph.COutline(i).CPoint(k), False), 0)) / 1e6
                              for i in range(glyph.OutlineCount()) for k in range(glyph.COutline(i).PointCount()))
                    if gap < 0.1:
                        warn.append("%s reference glyphs %.2f mm from the %s body edge (placement tolerance)" % (ref, gap, o))
        if nucleo and boxes_overlap(tb, nucleo, -0.05) and ref not in ("J5", "J6"):
            warn.append("%s reference under the NUCLEO outline (hidden while plugged)" % ref)
    A.add("SLK-3", "Every reference visible on silk, not under a part body (glyph polygons vs body)", "PASS" if not bad else lv,
          "%d hidden/covered, %d note(s)" % (len(bad), len(warn)), bad + warn)
    # required labels
    allt = [(ref, t, layer, s) for ref, t, layer, s, vis in texts]
    fronts = [(t, s.upper()) for ref, t, layer, s in allt if layer == pcbnew.F_SilkS]

    def near(ref, word, radius, layer=pcbnew.F_SilkS):
        bb = bbox_mm(m.fps[ref].GetBoundingBox(False))
        box = (bb[0] - radius, bb[1] - radius, bb[2] + radius, bb[3] + radius)
        return [(t, s) for r_, t, l_, s in allt if l_ == layer and word.upper() in s.upper() and boxes_overlap(bbox_mm(t.GetBoundingBox()), box)]

    miss = []
    for ref in sorted(r for r in m.fps if r.startswith("TP")):
        val = str(m.fps[ref].GetValue()).upper()
        if not near(ref, val, 3.0):
            miss.append("%s: no F.Silkscreen '%s' label within 3 mm" % (ref, val))
    for ref, words in CONN_LABELS.items():
        for w in words:
            if not near(ref, w, 8.0):
                miss.append("%s: no '%s' label within 8 mm" % (ref, w))
    for ref, w in (("J5", "CN3"), ("J6", "CN4")):
        if not near(ref, w, 8.0):
            miss.append("%s: no '%s' label" % (ref, w))
    if not any(re.search(r"BUCK|REV ?C", s) for t, s in fronts):
        miss.append("no title text (BUCK / REV C) on F.Silkscreen")
    def _joined(t0):
        c0 = mmxy(t0.GetPosition())
        return " ".join(s for t, s in fronts if abs(mmxy(t.GetPosition())[0] - c0[0]) < 6 and abs(mmxy(t.GetPosition())[1] - c0[1]) < 3)
    if not any("15V" in _joined(t).replace(" ", "") and "1.5A" in _joined(t).replace(" ", "") for t, s in fronts):
        miss.append("no '12V (MAX 15V) - I LIMIT 1.5A' text on F.Silkscreen")
    A.add("SLK-4", "Required labels: TP names, J1-J4 polarity, CN3/CN4, title, supply limit", "PASS" if not miss else lv, "%d missing" % len(miss), miss)
    # bottom labels, mirrored
    miss = []
    for ref in HAND_SOLDER:
        if ref not in m.fps:
            continue
        bb = bbox_mm(m.fps[ref].GetBoundingBox(False))
        box = (bb[0] - 4, bb[1] - 4, bb[2] + 4, bb[3] + 4)
        bt = [(t, s) for r_, t, l_, s in allt if l_ == pcbnew.B_SilkS and boxes_overlap(bbox_mm(t.GetBoundingBox()), box)]
        if not bt:
            miss.append("%s: no B.Silkscreen label within 4 mm" % ref)
        elif not all(t.IsMirrored() for t, s in bt):
            miss.append("%s: B.Silkscreen label not mirrored: %s" % (ref, [s for t, s in bt if not t.IsMirrored()]))
    A.add("SLK-5", "Mirrored B.Silkscreen labels for hand-soldered parts", "PASS" if not miss else lv, "%d missing/unmirrored" % len(miss), miss)
    # label-to-pin mapping for terminal blocks
    det, bad = [], []
    pin_pool = [q for r_ in list(CONN_LABELS) + [x for x in m.fps if x.startswith("TP")] for q in m.fps[r_].Pads()]
    for ref, words in CONN_LABELS.items():
        f = m.fps[ref]
        for w in words:
            for t, s in near(ref, w, 8.0):
                if "/" in s:
                    det.append("%s combined label '%s' -- check order manually" % (ref, s)); continue
                c = mmxy(t.GetPosition())
                # a label at the same height as a pin (vertical stack, labels beside the block) belongs to that pin
                p = min(pin_pool, key=lambda q: (abs(c[1] - mmxy(q.GetPosition())[1]) if abs(c[1] - mmxy(q.GetPosition())[1]) < 0.6 and
                                                 abs(c[0] - mmxy(q.GetPosition())[0]) < 9 else 50) + dist(c, mmxy(q.GetPosition())) / 100)
                if p.GetParentFootprint().GetReference() != ref:
                    continue
                want = LABEL_NET.get(w.upper())
                if want and p.GetNetname() != want:
                    bad.append("%s label '%s' nearest pad %s is %s (want %s)" % (ref, s, p.GetNumber(), p.GetNetname(), want))
                else:
                    det.append("%s '%s' -> pad %s %s" % (ref, s, p.GetNumber(), p.GetNetname()))
    A.add("SLK-6", "Connector labels sit next to the matching pin", "PASS" if not bad else lv, "%d mismatch(es)" % len(bad), bad + det)


def chk_manufacturing(A, m, base, pcb, run_dir, do_export):
    # footprint diff
    def snap(bd):
        return {f.GetReference(): (round(TMM(f.GetPosition().x), 3), round(TMM(f.GetPosition().y), 3), round(f.GetOrientationDegrees(), 2),
                                   f.GetLayerName(), f.GetFPIDAsString()) for f in bd.GetFootprints()}
    if base is None:
        A.add("MAN-1", "No footprint moved vs baseline", "WARN", "no baseline given")
    else:
        a, b = snap(base.b), snap(m.b)
        diff = ["%s %s -> %s" % (r, a.get(r), b.get(r)) for r in sorted(set(a) | set(b)) if a.get(r) != b.get(r)]
        A.add("MAN-1", "No footprint moved vs baseline", "PASS" if not diff else "FAIL", "%d footprints, %d changed" % (len(b), len(diff)), diff)
        def edge(bd):
            o = pcbnew.SHAPE_POLY_SET(); bd.GetBoardPolygonOutlines(o, False); return tuple(round(v, 3) for v in bbox_mm(o.BBox())), round(area_mm2(o), 2)
        e0, e1 = edge(base.b), edge(m.b)
        A.add("MAN-4", "Board outline unchanged", "PASS" if e0 == e1 else "FAIL", "now %s, baseline %s" % (e1, e0))
    # JLC SMD spacing
    if os.path.exists(JLC_SPACING):
        r = subprocess.run([KPY, "-I", JLC_SPACING, pcb], capture_output=True, text=True, timeout=300)
        mt = re.search(r"VIOLATIONS \((\d+)\)", r.stdout)
        n = int(mt.group(1)) if mt else -1
        A.add("MAN-2", "JLC SMD spacing check (jlc_spacing.py) = 0 violations", "PASS" if n == 0 else "FAIL",
              "%s violation(s)" % (n if n >= 0 else "unparsed"),
              [l.strip() for l in r.stdout.splitlines() if "required" in l or "VIOLATIONS" in l or "Tight" in l or "(min " in l][:20])
    else:
        A.add("MAN-2", "JLC SMD spacing check", "WARN", "script not found: %s" % JLC_SPACING)
    if not do_export:
        A.add("MAN-3", "Gerber + drill export", "N/A", "skipped (--no-export)"); return
    gd = os.path.join(run_dir, "gerbers"); os.makedirs(gd, exist_ok=True)
    r1 = subprocess.run([KCLI, "pcb", "export", "gerbers", "-o", gd + os.sep, pcb], capture_output=True, text=True, timeout=300)
    r2 = subprocess.run([KCLI, "pcb", "export", "drill", "-o", gd + os.sep, pcb], capture_output=True, text=True, timeout=300)
    files = sorted(os.listdir(gd))
    need = ["F_Cu", "B_Cu", "F_Mask", "B_Mask", "F_Silkscreen", "B_Silkscreen", "Edge_Cuts"]
    lacking = [n for n in need if not any(n in f for f in files)]
    drl = [f for f in files if f.lower().endswith(".drl")]
    ok = r1.returncode == 0 and r2.returncode == 0 and not lacking and drl
    A.add("MAN-3", "Gerber + drill export succeed", "PASS" if ok else "FAIL",
          "rc gerber=%d drill=%d, %d files, missing %s, drill files %s" % (r1.returncode, r2.returncode, len(files), lacking or "none", drl),
          [l for l in (r1.stderr + r2.stderr).splitlines() if l.strip()][:10])


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("board")
    ap.add_argument("--stage", default="S5", help="S0..S5 (default S5 = strictest)")
    ap.add_argument("--baseline", default=DEFAULT_BASELINE)
    ap.add_argument("--sch", default=None, help="schematic for parity (default: next to the board, else project copy)")
    ap.add_argument("--render", action="store_true", help="also render top/bottom PNGs into the run folder")
    ap.add_argument("--no-export", action="store_true")
    ap.add_argument("--max-details", type=int, default=12)
    args = ap.parse_args()
    stage = int(args.stage.upper().lstrip("S"))
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(HERE, "runs", "%s_S%d_%s" % (os.path.splitext(os.path.basename(args.board))[0], stage, stamp))
    os.makedirs(run_dir, exist_ok=True)
    pcb, notes = snapshot(args.board, run_dir, args.sch)
    sha = hashlib.sha256(open(pcb, "rb").read()).hexdigest()[:16]
    A = Audit(stage)
    print("check_layout: %s  stage S%d  snapshot %s  sha256[:16]=%s" % (os.path.abspath(args.board), stage, pcb, sha))
    for n in notes:
        print("  note: " + n)
    drc, log, rc = run_drc(pcb, run_dir)
    board = pcbnew.LoadBoard(pcb)
    m = Model(board)
    base = Model(pcbnew.LoadBoard(args.baseline)) if args.baseline and os.path.exists(args.baseline) else None
    print("  items: %d footprints, %d segments, %d arcs, %d vias, %d zones, %d teardrops" % (len(m.fps), len(m.segs), len(m.arcs), len(m.vias), len(m.zones), len(m.tdrops)))
    dru = os.path.join(os.path.dirname(pcb), "chk.kicad_dru")
    steps = [lambda: chk_drc(A, m, drc, log, rc, dru), lambda: chk_rules(A, m, os.path.join(os.path.dirname(pcb), "chk.kicad_pro")),
             lambda: chk_jlc_geometry(A, m), lambda: chk_hot_loop(A, m, base), lambda: chk_layers(A, m)]
    tap_holder = {}
    steps += [lambda: tap_holder.update(chk_widths(A, m, drc) or {}), lambda: chk_necks(A, m), lambda: chk_sw_area(A, m),
              lambda: chk_drive(A, m), lambda: chk_angles(A, m), lambda: chk_dangling(A, m), lambda: chk_vias(A, m),
              lambda: chk_zones(A, m, pcb), lambda: chk_sw_proximity(A, m, tap_holder), lambda: chk_sense(A, m, tap_holder),
              lambda: chk_teardrops(A, m), lambda: chk_silk(A, m, drc), lambda: chk_manufacturing(A, m, base, pcb, run_dir, not args.no_export)]
    for i, s in enumerate(steps):
        try:
            s()
        except Exception as e:  # a broken check must never look like a pass
            import traceback
            A.add("ERR-%d" % i, "checker exception", "FAIL", "%s: %s" % (type(e).__name__, e), traceback.format_exc().splitlines()[-4:])
    if args.render:
        for side in ("top", "bottom"):
            subprocess.run([KCLI, "pcb", "render", "--side", side, "--width", "1800", "--height", "1400", "--quality", "basic",
                            "--background", "opaque", "-o", os.path.join(run_dir, "render_%s.png" % side), pcb], capture_output=True, text=True, timeout=600)
    order = ["DRC", "RUL", "PWR", "DRV", "SIG", "GEO", "VIA", "ZON", "TDR", "SLK", "MAN", "ERR"]
    A.results.sort(key=lambda r: (order.index(r["id"].split("-")[0]) if r["id"].split("-")[0] in order else 99, r["id"]))
    cnt = collections.Counter(r["status"] for r in A.results)
    for r in A.results:
        print("%-4s  %-6s %s -- %s" % (r["status"], r["id"], r["title"], r["summary"]))
        for d in r["details"][:args.max_details]:
            print("              " + str(d))
        if len(r["details"]) > args.max_details:
            print("              ... %d more (see results.json)" % (len(r["details"]) - args.max_details))
    print("SUMMARY stage S%d: %d PASS, %d WARN, %d FAIL, %d N/A   (run folder %s)" % (stage, cnt["PASS"], cnt["WARN"], cnt["FAIL"], cnt["N/A"], run_dir))
    json.dump({"board": os.path.abspath(args.board), "sha256_16": sha, "stage": stage, "results": A.results, "drc_log": log},
              open(os.path.join(run_dir, "results.json"), "w", encoding="utf-8"), indent=1)
    sys.exit(1 if cnt["FAIL"] else 0)


if __name__ == "__main__":
    main()
