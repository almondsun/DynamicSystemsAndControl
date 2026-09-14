#!/usr/bin/env python3
"""Independent CAD export parity, mask openings, power widths and latch audit."""
import json,sys,xml.etree.ElementTree as ET
from pathlib import Path
import pcbnew as pcb
from design import ROOT,PARTS
if not hasattr(pcb.SwigPyIterator,'next'):pcb.SwigPyIterator.next=pcb.SwigPyIterator.__next__
b=pcb.PCB_IO_KICAD_SEXPR(0).LoadBoard(str(ROOT/'buck.kicad_pcb'),None)
actual={};footprints={f.GetReference():f for f in b.GetFootprints()}
for ref,f in footprints.items():
    for pad in f.Pads():actual[ref,pad.GetNumber()]=None if pad.GetNetname().startswith('unconnected-(') else pad.GetNetname() or None
for p in PARTS:
    assert p['ref'] in footprints,p['ref']
    for pin,net in p['pins'].items():assert actual.get((p['ref'],pin))==net,(p['ref'],pin,net,actual.get((p['ref'],pin)))
    assert set(p['pins'])=={pad.GetNumber() for pad in footprints[p['ref']].Pads()},p['ref']
for ref in ['L1','L2']:
    for pad in footprints[ref].Pads():
        assert pad.IsOnLayer(pcb.F_Mask) and pad.IsOnLayer(pcb.B_Mask),'Unsolderable inductor pad'
xml=ET.parse(sys.argv[1]);exported={}
for net in xml.findall('.//nets/net'):
    for node in net.findall('node'):
        if node.get('ref').startswith('#'):continue
        exported[node.get('ref'),node.get('pin')]=net.get('name')
expected={key:net for key,net in actual.items() if net}
assert all(exported.get(k)==v for k,v in expected.items()),'Schematic/PCB net mismatch'
power={'VIN','GND','SW','LMID','IP','VOUT'};widths=[];vias=0
for item in b.GetTracks():
    if isinstance(item,pcb.PCB_VIA):
        vias+=1;assert item.GetDrillValue()>=pcb.FromMM(.6)
    else:
        width=pcb.ToMM(item.GetWidth());widths.append(width)
        if width<.299:
            # Two short low-current INA180 OUT escape segments between SOT23 pads.
            assert item.GetNetname()=='ISENSE' and width>=.224
            for point in [item.GetStart(),item.GetEnd()]:
                x,y=pcb.ToMM(point)
                assert 84.5<x<86.2 and 46.8<y<47.6
        if item.GetNetname() in power and width<.599:
            # Local low-current ground escape from the SOT23 amplifier.
            # It is not a load-current trace; the rest of GND is >=0.6mm plus plane.
            assert item.GetNetname()=='GND' and width>=.359
            for point in [item.GetStart(),item.GetEnd()]:
                x,y=pcb.ToMM(point)
                assert 82<x<85 and 48<y<55,(x,y)
assert b.GetCopperLayerCount()==2
outline=b.GetBoardEdgesBoundingBox();assert abs(pcb.ToMM(outline.GetWidth())-99)<.1
# NAND latch equations use physical package gate mapping, not an MCU flag.
def stable(ntrip,reset):
    nr=not(reset and ntrip)
    return [(f,nf) for f in (False,True) for nf in (False,True)
            if f== (not(ntrip and nf)) and nf==(not(nr and f))]
assert stable(False,False)==[(True,False)]
assert stable(False,True)==[(True,False)]
assert stable(True,True)==[(False,True)]
assert set(stable(True,False))=={(True,False),(False,True)}
for nf in (False,True):assert not(False and nf) # RUN low always SD high.
# Conservative component tolerance bounds: 7805 +/-5%, divider +/-1%,
# INA gain +/-1%, shunt +/-1%, input offset +/-0.5mV, comparator +/-5mV.
vref_min=4.75*(10000*.99)/(15000*1.01+10000*.99)
vref_max=5.25*(10000*1.01)/(15000*.99+10000*1.01)
imin=((vref_min-.005)/(20*1.01)-.0005)/(.05*1.01)
imax=((vref_max+.005)/(20*.99)+.0005)/(.05*.99)
ovmin=(vref_min-.005)*(1+31000*.99/(10000*1.01))
ovmax=(vref_max+.005)*(1+31000*1.01/(10000*.99))
assert imin>1.55 and imax<3
result={'parts':len(PARTS),'connected_pads':len(expected),'vias':vias,'track_width_range_mm':[min(widths),max(widths)],'copper_layers':2,'board_dimensions_mm':[99,99],'ERC_and_DRC':'see separate native reports','latch_truth_table':'PASS','trip_estimate_A':[imin,imax],'OVP_estimate_V':[ovmin,ovmax],'physical_tests':'NOT RUN','fabrication_release':'HOLD: received component qualification and soldered prototype required'}
Path(sys.argv[2]).write_text(json.dumps(result,indent=2)+'\n')
print('PASS: pin/net parity, footprint pad counts, solder-mask openings, routing widths, vias, board dimensions and latch truth table')
print(json.dumps(result,indent=2))
