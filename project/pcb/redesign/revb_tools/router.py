"""Small two-layer grid router for the Rev B board (python3.14 with KiCad pcbnew, numpy, scipy).

Copper of every placed item is rasterised on a 0.1 mm grid per layer. A route for net N may
use cells whose distance to other-net copper exceeds clearance + half width (computed with a
Euclidean distance transform) and whose distance to the board edge exceeds the edge clearance.
A* uses 8-neighbour moves, a cost multiplier on B.Cu and a fixed via cost. KiCad DRC remains
the authority: this module only proposes geometry.
"""
import heapq
import math

import numpy as np
import pcbnew
from scipy import ndimage

MM = pcbnew.ToMM
LAYERS = (pcbnew.F_Cu, pcbnew.B_Cu)
SQ2 = math.sqrt(2.0)
# Rasterisation error of a 0.1 mm grid (half cell diagonal) plus a little slack.
MARGIN = 0.09


def polygons(item, layer):
    ps = pcbnew.SHAPE_POLY_SET()
    item.TransformShapeToPolygon(ps, layer, 0, pcbnew.FromMM(0.005), pcbnew.ERROR_OUTSIDE)
    out = []
    for i in range(ps.OutlineCount()):
        ol = ps.Outline(i)
        out.append(np.array([(MM(ol.CPoint(k).x), MM(ol.CPoint(k).y)) for k in range(ol.PointCount())]))
    return out


class Grid:
    def __init__(self, board, pitch=0.1, edge_clearance=0.5):
        self.board, self.g = board, pitch
        bb = board.GetBoardEdgesBoundingBox()
        self.x0, self.y0 = MM(bb.GetX()), MM(bb.GetY())
        self.nx = int(math.ceil(MM(bb.GetWidth()) / pitch)) + 1
        self.ny = int(math.ceil(MM(bb.GetHeight()) / pitch)) + 1
        self.owner = np.zeros((2, self.ny, self.nx), np.int32)
        self.smd = np.zeros((self.ny, self.nx), bool)
        self.thru = np.zeros((self.ny, self.nx), bool)
        self.keep = {}  # name -> (layer mask (2,ny,nx), predicate(netname)->blocked)
        inside = np.zeros((self.ny, self.nx), bool)
        inside[1:-1, 1:-1] = True
        self.edge_dist = ndimage.distance_transform_edt(inside) * pitch
        self.edge_clearance = edge_clearance
        for fp in board.GetFootprints():
            for pad in fp.Pads():
                self.add_item(pad, pad.GetNetCode())
                if pad.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
                    for poly in polygons(pad, pcbnew.F_Cu):
                        self.smd |= self.fill(poly)
        for t in board.GetTracks():
            self.add_item(t, t.GetNetCode())

    # ---------------------------------------------------------------- geometry
    def cell(self, x, y):
        return int(round((y - self.y0) / self.g)), int(round((x - self.x0) / self.g))

    def xy(self, iy, ix):
        return self.x0 + ix * self.g, self.y0 + iy * self.g

    def fill(self, poly):
        mask = np.zeros((self.ny, self.nx), bool)
        xs, ys = poly[:, 0], poly[:, 1]
        i0, j0 = self.cell(xs.min(), ys.min())
        i1, j1 = self.cell(xs.max(), ys.max())
        i0, j0 = max(i0 - 1, 0), max(j0 - 1, 0)
        i1, j1 = min(i1 + 2, self.ny), min(j1 + 2, self.nx)
        if i0 >= i1 or j0 >= j1:
            return mask
        gx = self.x0 + np.arange(j0, j1) * self.g
        gy = self.y0 + np.arange(i0, i1) * self.g
        X, Y = np.meshgrid(gx, gy)
        inside = np.zeros(X.shape, bool)
        n = len(poly)
        for k in range(n):
            xa, ya = poly[k]
            xb, yb = poly[(k + 1) % n]
            cond = (ya > Y) != (yb > Y)
            with np.errstate(divide="ignore", invalid="ignore"):
                xc = (xb - xa) * (Y - ya) / (yb - ya) + xa
            inside ^= cond & (X < xc)
        mask[i0:i1, j0:j1] = inside
        return mask

    def add_item(self, item, net):
        through = item.IsOnLayer(pcbnew.F_Cu) and item.IsOnLayer(pcbnew.B_Cu)
        for li, layer in enumerate(LAYERS):
            if not item.IsOnLayer(layer):
                continue
            for poly in polygons(item, layer):
                m = self.fill(poly)
                self.owner[li][m] = net if net > 0 else -2
                if through:
                    self.thru |= m

    def components(self, net):
        """Label copper of one net; layers join only through vias and plated pads."""
        eight = np.ones((3, 3), bool)
        lab0, n0 = ndimage.label(self.owner[0] == net, structure=eight)
        lab1, n1 = ndimage.label(self.owner[1] == net, structure=eight)
        parent = list(range(n0 + n1 + 1))

        def find(a):
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a
        both = self.thru & (lab0 > 0) & (lab1 > 0)
        for a, b in zip(lab0[both], lab1[both]):
            parent[find(int(a))] = find(int(b) + n0)
        roots = np.array([find(i) for i in range(n0 + n1 + 1)])
        comp = np.zeros((2, self.ny, self.nx), np.int32)
        comp[0] = np.where(lab0 > 0, roots[lab0], 0)
        comp[1] = np.where(lab1 > 0, roots[np.where(lab1 > 0, lab1 + n0, 0)], 0)
        return comp

    def add_keepout(self, name, x0, y0, x1, y1, layers, blocks):
        m = np.zeros((2, self.ny, self.nx), bool)
        i0, j0 = self.cell(x0, y0)
        i1, j1 = self.cell(x1, y1)
        for li in layers:
            m[li, max(i0, 0):i1 + 1, max(j0, 0):j1 + 1] = True
        self.keep[name] = (m, blocks)

    # ----------------------------------------------------------------- routing
    def free_maps(self, net, netname, half, clear, via_r, sw_net=0, sw_clear=0.0):
        g = self.g
        free = np.zeros((2, self.ny, self.nx), bool)
        for li in range(2):
            other = (self.owner[li] != 0) & (self.owner[li] != net)
            dist = ndimage.distance_transform_edt(~other) * g
            ok = dist > clear + half + MARGIN
            if sw_net and net != sw_net:
                dsw = ndimage.distance_transform_edt(self.owner[li] != sw_net) * g
                ok &= dsw > sw_clear + half + MARGIN
            free[li] = ok
        free &= self.edge_dist > self.edge_clearance + half
        for mask, blocks in self.keep.values():
            if blocks(netname):
                free &= ~mask
        via_ok = np.ones((self.ny, self.nx), bool)
        for li in range(2):
            other = (self.owner[li] != 0) & (self.owner[li] != net)
            via_ok &= ndimage.distance_transform_edt(~other) * g > clear + via_r + MARGIN
        via_ok &= ndimage.distance_transform_edt(~self.smd) * g > via_r + 0.25
        via_ok &= self.edge_dist > self.edge_clearance + via_r
        for mask, blocks in self.keep.values():
            if blocks(netname):
                via_ok &= ~(mask[0] | mask[1])
        return free, via_ok

    def astar(self, free, via_ok, src_mask, tgt, b_cost=2.5, via_cost=35.0, max_expand=400_000):
        sources = [tuple(int(v) for v in c) for c in np.argwhere(src_mask & free)]
        tcells = np.argwhere(tgt)
        if len(tcells) == 0:
            return None
        # Heuristic: Chebyshev-octile distance to the target bounding box.
        ty0, tx0 = tcells[:, 1].min(), tcells[:, 2].min()
        ty1, tx1 = tcells[:, 1].max(), tcells[:, 2].max()

        def h(iy, ix):
            dy = max(ty0 - iy, 0, iy - ty1)
            dx = max(tx0 - ix, 0, ix - tx1)
            return max(dx, dy) + (SQ2 - 1) * min(dx, dy)

        best = {}
        prev = {}
        heap = []
        for s in sources:
            best[s] = 0.0
            heapq.heappush(heap, (h(s[1], s[2]), 0.0, s))
        moves = [(-1, 0, 1.0), (1, 0, 1.0), (0, -1, 1.0), (0, 1, 1.0),
                 (-1, -1, SQ2), (-1, 1, SQ2), (1, -1, SQ2), (1, 1, SQ2)]
        expanded = 0
        while heap:
            f, gcost, s = heapq.heappop(heap)
            if gcost > best.get(s, math.inf):
                continue
            li, iy, ix = s
            if tgt[s]:
                path = [s]
                while path[-1] in prev:
                    path.append(prev[path[-1]])
                return path[::-1]
            expanded += 1
            if expanded > max_expand:
                return None
            mult = 1.0 if li == 0 else b_cost
            for dy, dx, c in moves:
                ny_, nx_ = iy + dy, ix + dx
                if not (0 <= ny_ < self.ny and 0 <= nx_ < self.nx):
                    continue
                n = (li, ny_, nx_)
                if not free[n]:
                    continue
                if dy and dx and not (free[li, iy + dy, ix] and free[li, iy, ix + dx]):
                    continue
                ng = gcost + c * mult
                if ng < best.get(n, math.inf):
                    best[n] = ng
                    prev[n] = s
                    heapq.heappush(heap, (ng + h(ny_, nx_), ng, n))
            if via_ok[iy, ix]:
                n = (1 - li, iy, ix)
                if free[n]:
                    ng = gcost + via_cost
                    if ng < best.get(n, math.inf):
                        best[n] = ng
                        prev[n] = s
                        heapq.heappush(heap, (ng + h(iy, ix), ng, n))
        return None


def simplify(path):
    """Collapse runs of identical direction; keep layer-change points."""
    pts = [path[0]]
    for a, b, c in zip(path, path[1:], path[2:]):
        if a[0] != b[0] or b[0] != c[0]:
            pts.append(b)
            continue
        if (b[1] - a[1], b[2] - a[2]) != (c[1] - b[1], c[2] - b[2]):
            pts.append(b)
    pts.append(path[-1])
    out = []
    for p in pts:
        if not out or out[-1] != p:
            out.append(p)
    return out


def emit(board, grid, path, net, width, via_dia, via_drill, start_xy=None, end_xy=None, anchor_w=None):
    """Create tracks/vias for a cell path; returns created items.

    start_xy/end_xy anchor the ends at pad centres: a cell centre near a rounded pad corner can
    fall outside the real pad, and KiCad then sees no connection.
    """
    pts = simplify(path)
    items = []
    netinfo = board.FindNet(board.GetNetInfo().GetNetItem(net).GetNetname()) if net else None
    segs = list(zip(pts, pts[1:]))
    if start_xy is not None:
        segs.insert(0, (("xy", *start_xy, pts[0][0]), pts[0]))
    if end_xy is not None:
        segs.append((pts[-1], ("xy", *end_xy, pts[-1][0])))
    for a, b in segs:
        if a[0] == "xy" or b[0] == "xy":
            layer = a[3] if a[0] == "xy" else b[3]
            xa, ya = (a[1], a[2]) if a[0] == "xy" else grid.xy(a[1], a[2])
            xb, yb = (b[1], b[2]) if b[0] == "xy" else grid.xy(b[1], b[2])
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(float(xa)), pcbnew.FromMM(float(ya))))
            t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(float(xb)), pcbnew.FromMM(float(yb))))
            t.SetWidth(pcbnew.FromMM(min(width, anchor_w or width)))
            t.SetLayer(LAYERS[layer])
            t.SetNet(netinfo)
            board.Add(t)
            items.append(t)
            continue
        if a[0] != b[0]:
            via = pcbnew.PCB_VIA(board)
            x, y = grid.xy(a[1], a[2])
            via.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(float(x)), pcbnew.FromMM(float(y))))
            via.SetWidth(pcbnew.FromMM(via_dia))
            via.SetDrill(pcbnew.FromMM(via_drill))
            via.SetNet(netinfo)
            board.Add(via)
            items.append(via)
            continue
        if (a[1], a[2]) == (b[1], b[2]):
            continue
        t = pcbnew.PCB_TRACK(board)
        xa, ya = grid.xy(a[1], a[2])
        xb, yb = grid.xy(b[1], b[2])
        t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(float(xa)), pcbnew.FromMM(float(ya))))
        t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(float(xb)), pcbnew.FromMM(float(yb))))
        t.SetWidth(pcbnew.FromMM(width))
        t.SetLayer(LAYERS[a[0]])
        t.SetNet(netinfo)
        board.Add(t)
        items.append(t)
    for it in items:
        grid.add_item(it, net)
    return items


_CELL_CACHE = {}


def item_cells(grid, item):
    key = (item.m_Uuid.AsString(), item.GetPosition().x, item.GetPosition().y)
    if key in _CELL_CACHE:
        return _CELL_CACHE[key]
    cells = []
    for li, layer in enumerate(LAYERS):
        if not item.IsOnLayer(layer):
            continue
        for poly in polygons(item, layer):
            for iy, ix in np.argwhere(grid.fill(poly)):
                cells.append((li, int(iy), int(ix)))
    _CELL_CACHE[key] = cells
    return cells
