"""Placement/routing preview: courtyards, pads, tracks and ratsnest as SVG.

    python3.14 -I preview.py board.kicad_pcb out.svg [--no-gnd-rats]
Convert with: magick -density 150 out.svg out.png
"""
import math
import sys

import pcbnew

MM = pcbnew.ToMM
POWER = {"VIN": "#d62728", "SW": "#ff7f0e", "IP": "#8c564b", "VOUT": "#9467bd",
         "GND": "#7f7f7f", "+5V": "#e377c2", "NUC_3V3": "#17becf", "BOOT": "#1f77b4", "HO": "#1f77b4",
         "GATE": "#1f77b4"}


def mst(points):
    if len(points) < 2:
        return []
    done, edges = {0}, []
    while len(done) < len(points):
        best = None
        for i in done:
            for j in range(len(points)):
                if j in done:
                    continue
                d = math.dist(points[i], points[j])
                if best is None or d < best[0]:
                    best = (d, i, j)
        done.add(best[2])
        edges.append((points[best[1]], points[best[2]]))
    return edges


def main() -> None:
    board = pcbnew.LoadBoard(sys.argv[1])
    skip_gnd = "--no-gnd-rats" in sys.argv
    bb = board.GetBoardEdgesBoundingBox()
    x0, y0, w, h = MM(bb.GetX()) - 3, MM(bb.GetY()) - 3, MM(bb.GetWidth()) + 6, MM(bb.GetHeight()) + 6
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0} {y0} {w} {h}" width="{w*12}" height="{h*12}">',
         f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" fill="white"/>',
         f'<rect x="{MM(bb.GetX())}" y="{MM(bb.GetY())}" width="{MM(bb.GetWidth())}" height="{MM(bb.GetHeight())}" '
         'fill="#f4f7f0" stroke="black" stroke-width="0.15"/>']
    for z in board.Zones():
        if z.IsFilled():
            for i in range(z.GetFilledPolysList(z.GetFirstLayer()).OutlineCount()):
                poly = z.GetFilledPolysList(z.GetFirstLayer()).Outline(i)
                pts = " ".join(f"{MM(poly.CPoint(k).x)},{MM(poly.CPoint(k).y)}" for k in range(poly.PointCount()))
                col = "#cfe3ff" if z.GetLayerName() == "B.Cu" else "#ffd9cf"
                s.append(f'<polygon points="{pts}" fill="{col}" fill-opacity="0.5" stroke="none"/>')
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            p = t.GetPosition()
            s.append(f'<circle cx="{MM(p.x)}" cy="{MM(p.y)}" r="{MM(t.GetWidth(pcbnew.F_Cu))/2}" fill="#444"/>')
        else:
            col = "#c0392b" if t.GetLayerName() == "F.Cu" else "#2471a3"
            s.append(f'<line x1="{MM(t.GetStart().x)}" y1="{MM(t.GetStart().y)}" x2="{MM(t.GetEnd().x)}" '
                     f'y2="{MM(t.GetEnd().y)}" stroke="{col}" stroke-width="{MM(t.GetWidth())}" '
                     'stroke-linecap="round" opacity="0.8"/>')
    nets = {}
    for fp in board.GetFootprints():
        crt = fp.GetCourtyard(pcbnew.F_CrtYd)
        if crt.OutlineCount():
            c = crt.BBox()
            s.append(f'<rect x="{MM(c.GetX())}" y="{MM(c.GetY())}" width="{MM(c.GetWidth())}" '
                     f'height="{MM(c.GetHeight())}" fill="none" stroke="#e600e6" stroke-width="0.08"/>')
        for pad in fp.Pads():
            p, sz = pad.GetPosition(), pad.GetBoundingBox()
            net = pad.GetNetname()
            col = POWER.get(net, "#2ca02c" if net else "#cccccc")
            s.append(f'<rect x="{MM(sz.GetX())}" y="{MM(sz.GetY())}" width="{MM(sz.GetWidth())}" '
                     f'height="{MM(sz.GetHeight())}" fill="{col}" fill-opacity="0.75"/>')
            if net and not net.startswith("unconnected"):
                nets.setdefault(net, []).append((MM(p.x), MM(p.y)))
        pos = fp.GetPosition()
        s.append(f'<text x="{MM(pos.x)}" y="{MM(pos.y)}" font-size="1.4" text-anchor="middle" '
                 f'font-family="sans-serif" fill="#000">{fp.GetReference()}</text>')
    for net, pts in nets.items():
        if skip_gnd and net == "GND":
            continue
        col = POWER.get(net, "#2ca02c")
        for a, b in mst(pts):
            s.append(f'<line x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}" stroke="{col}" '
                     'stroke-width="0.12" stroke-dasharray="0.6,0.3"/>')
    s.append("</svg>")
    open(sys.argv[2], "w").write("\n".join(s))


if __name__ == "__main__":
    main()
