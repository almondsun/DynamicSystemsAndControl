#!/usr/bin/env python3
"""Import a routed session, add return copper, then save an editable board."""
import sys
from pathlib import Path
import pcbnew as pcb
from design import ROOT
from generate import pos
io=pcb.PCB_IO_KICAD_SEXPR(0)
b=io.LoadBoard(str(ROOT/'buck.kicad_pcb'),None)
if not pcb.ImportSpecctraSES(b,sys.argv[1]): raise RuntimeError('SES import failed')
gnd=b.FindNet('GND')
zone=pcb.ZONE(b);zone.SetLayer(pcb.B_Cu);zone.SetNet(gnd)
zone.SetLocalClearance(pcb.FromMM(.3));zone.SetThermalReliefGap(pcb.FromMM(.3));zone.SetThermalReliefSpokeWidth(pcb.FromMM(.6))
zone.SetPadConnection(pcb.ZONE_CONNECTION_THERMAL);zone.SetMinThickness(pcb.FromMM(.25))
zone.Outline().NewOutline()
for x,y in [(10.5,10.5),(108.5,10.5),(108.5,108.5),(10.5,108.5)]:zone.Outline().Append(pcb.FromMM(x),pcb.FromMM(y))
b.Add(zone)
pcb.ZONE_FILLER(b).Fill(b.Zones())
io.SaveBoard(str(ROOT/'buck.kicad_pcb'),b)
print('Imported routed session and filled bottom GND zone')
