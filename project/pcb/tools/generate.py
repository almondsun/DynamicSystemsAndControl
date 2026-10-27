#!/usr/bin/env python3
"""Generate editable KiCad files from the reviewed pin-level design."""
import csv, json, os, uuid, re
from pathlib import Path
import pcbnew as pcb
from design import PARTS, ROOT

LIB = Path(os.environ.get('KICAD_FOOTPRINT_DIR','/usr/share/kicad/footprints'))
def uid(s): return str(uuid.uuid5(uuid.NAMESPACE_URL,'unal-buck-revA/'+s))
def q(s): return json.dumps(str(s),ensure_ascii=False)
def pos(x,y): return pcb.VECTOR2I(pcb.FromMM(x),pcb.FromMM(y))
def fx(size=1): return f'(effects (font (size {size} {size})))'
ROOT_ID=uid('root')
PIN_NAMES={
 'U1': ['LO','COM','VCC','NC','VS','VB','HO','NC','VDD','HIN','SD','LIN','VSS','NC'],
 'U2': ['IN','GND','OUT'], 'Q1':['G','D','S'], 'Q2':['E','B','C'],
 'U3':['1A','1Y','2A','2Y','3A','3Y','GND','4Y','4A','5Y','5A','6Y','6A','VCC'],
 'U4':['1A','1B','1Y','2A','2B','2Y','GND','3Y','3A','3B','4Y','4A','4B','VCC'],
 'U5':['OUT1','IN1-','IN1+','GND','IN2+','IN2-','OUT2','VCC'],
 'U6':['OUT','GND','IN+','IN-','VS']}

def symbol_lib(p):
    pins=list(p['pins'].items()); half=(len(pins)+1)//2; height=max(5.08,half*2.54)
    chunks=[]; coords={}
    for i,(num,net) in enumerate(pins):
        left=i<half; j=i if left else i-half
        x=-12.7 if left else 12.7; y=height/2-2.54-j*2.54
        coords[num]=(x,y,180 if left else 0)
        typ='passive'
        if p['ref'].startswith('U'):
            if net is None: typ='output' if p['ref']=='U3' or (p['ref']=='U1' and num=='1') else 'no_connect'
            elif (p['ref'],num) in {('U1','7'),('U3','2'),('U4','3'),('U4','6'),('U4','8'),('U4','11'),('U6','1')}:typ='output'
            elif p['ref']=='U5' and num in ('1','7'):typ='open_collector'
            elif p['ref']=='U2' and num=='3':typ='power_out'
            elif net in ('VIN','+5V','GND','BOOT') and p['ref'] != 'U3':typ='power_in'
            else:typ='input'
        name=PIN_NAMES[p['ref']][int(num)-1] if p['ref'] in PIN_NAMES else net or 'NC'
        if len(pins)==2: name='~'
        chunks.append(f'(pin {typ} line (at {x} {y} {0 if left else 180}) (length 2.54) (name {q(name)} {fx(.85)}) (number {q(num)} {fx(.85)}))')
    graphic=f'(rectangle (start -10.16 {height/2}) (end 10.16 {-height/2}) (stroke (width .254) (type default)) (fill (type background)))'
    if len(pins)==2 and p['ref'][0] in 'RCLD':
        def line(points): return '(polyline (pts '+''.join(f'(xy {x} {y})' for x,y in points)+') (stroke (width .254) (type default)) (fill (type none)))'
        kind=p['ref'][0]; body=3.81 if kind in 'RL' else 1.27 if kind=='C' else 2.54
        graphic=line([(-10.16,0),(-body,0)])+line([(body,0),(10.16,0)])
        if kind=='R': graphic+=f'(rectangle (start -3.81 1.27) (end 3.81 -1.27) (stroke (width .254) (type default)) (fill (type none)))'
        elif kind=='C':
            graphic+=line([(-1.27,-3.81),(-1.27,3.81)])+line([(1.27,-3.81),(1.27,3.81)])
            if 'CP_' in p['footprint']:graphic+=line([(-5,2),(-3,2)])+line([(-4,1),(-4,3)])
        elif kind=='D':graphic+=line([(-2.54,-2.54),(-2.54,2.54)])+line([(2.54,-2.54),(-2.54,0),(2.54,2.54),(2.54,-2.54)])
        else:
            import math
            graphic+=line([(-3.81+7.62*j/40,1.8*abs(math.sin(j*math.pi/10))) for j in range(41)])
    sym=f'''(symbol "Buck:{p['ref']}" (pin_names (offset .5)) (in_bom yes) (on_board yes)
      (property "Reference" {q(p['ref'][0])} (at 0 {height/2+3} 0) {fx()})
      (property "Value" {q(p['value'])} (at 0 {-height/2-3} 0) {fx()})
      (symbol "{p['ref']}_0_1" {graphic})
      (symbol "{p['ref']}_1_1" {''.join(chunks)}))'''
    return sym,coords,height

def schematic():
    all_libs=[]
    root=['(kicad_sch (version 20250114) (generator "eeschema")',f'(uuid {ROOT_ID}) (paper "A4") (title_block (title "Buck 12V / 6V - REVIEW ONLY") (rev "A") (company "UNAL Manizales")) (lib_symbols)']
    names={1:'Power stage',2:'Gate driver and supplies',3:'Independent protection',4:'STM32 interface and test points'}
    for section,name in names.items():
        sheet_id=uid(f'sheet{section}'); fn=f'buck_{section}.kicad_sch'
        root.append(f'''(sheet (at 30 {30+section*25}) (size 130 18) (stroke (width .1524) (type default)) (fill (color 0 0 0 0)) (uuid {sheet_id})
          (property "Sheetname" {q(name)} (at 30 {29+section*25} 0) {fx(1.27)})
          (property "Sheetfile" {q(fn)} (at 30 {50+section*25} 0) {fx(1.27)})
          (instances (project "buck" (path "/{ROOT_ID}" (page "{section+1}")))))''')
        parts=[p for p in PARTS if p['section']==section]; libs=[]; objects=[]
        for i,p in enumerate(parts):
            sym,coords,height=symbol_lib(p); libs.append(sym)
            x=50.8+(i%4)*99.06; y=35.56+(i//4)*43.18
            objects.append(f'''(symbol (lib_id "Buck:{p['ref']}") (at {x} {y} 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid {uid(p['ref'])})
              (property "Reference" {q(p['ref'])} (at {x} {y-height/2-4} 0) {fx(1.27)})
              (property "Value" {q(p['value'])} (at {x} {y+height/2+4} 0) {fx(.95)})
              (property "Footprint" {q(p['footprint'])} (at {x} {y} 0) (effects (font (size 1 1)) (hide yes)))
              (instances (project "buck" (path "/{ROOT_ID}/{sheet_id}" (reference {q(p['ref'])}) (unit 1)))))''')
            for num,net in p['pins'].items():
                dx,dy,angle=coords[num]; px=x+dx; py=y-dy
                if net is None:
                    objects.append(f'(no_connect (at {px} {py}) (uuid {uid(p["ref"]+num+"nc")}))'); continue
                endx=px+(-5.08 if dx<0 else 5.08)
                objects.append(f'(wire (pts (xy {px} {py}) (xy {endx} {py})) (stroke (width 0) (type default)) (uuid {uid(p["ref"]+num+"wire")}))')
                objects.append(f'(global_label {q(net)} (shape passive) (at {endx} {py} {angle}) (effects (font (size .85 .85)) (justify {"right" if dx<0 else "left"})) (uuid {uid(p["ref"]+num+"label")}))')
        # Intentional power sources: fused input, external controller 3V3, bootstrap charge.
        if section==1:
            libs.append('(symbol "Buck:PWR_FLAG" (power) (pin_names (offset 0)) (in_bom no) (on_board no) (property "Reference" "#FLG" (at 0 0 0) (effects (font (size 1 1)) (hide yes))) (property "Value" "PWR_FLAG" (at 0 3 0) (effects (font (size 1 1)))) (symbol "PWR_FLAG_1_1" (pin power_out line (at 0 0 90) (length 0) (name "pwr" (effects (font (size 1 1)))) (number "1" (effects (font (size 1 1)))))))')
            for i,net in enumerate(['VIN','GND','BOOT','+3V3']):
                x=40.64+i*88.9;y=210.82;ref=f'#FLG0{i+1}'
                objects.append(f'(symbol (lib_id "Buck:PWR_FLAG") (at {x} {y} 0) (unit 1) (in_bom no) (on_board no) (dnp no) (uuid {uid(ref)}) (property "Reference" "{ref}" (at {x} {y} 0) (effects (font (size 1 1)) (hide yes))) (property "Value" "PWR_FLAG" (at {x} {y-3} 0) {fx()}) (instances (project "buck" (path "/{ROOT_ID}/{sheet_id}" (reference "{ref}") (unit 1)))))')
                objects.append(f'(global_label "{net}" (shape passive) (at {x} {y} 0) {fx()} (uuid {uid(ref+"label")}))')
        (ROOT/fn).write_text(f'(kicad_sch (version 20250114) (generator "eeschema") (uuid {uid(fn)}) (paper "A3") (title_block (title {q(name+" - REV A / HOLD FABRICATION")}) (rev "A") (company "UNAL Manizales - Sistemas Dinamicos y Control")) (lib_symbols {"".join(libs)}) {"".join(objects)})\n')
        all_libs.extend(s.replace('"Buck:', '"', 1) for s in libs)
    root.append(f'(sheet_instances (path "/" (page "1"))))')
    (ROOT/'buck.kicad_sch').write_text('\n'.join(root))
    (ROOT/'Buck.kicad_sym').write_text('(kicad_symbol_lib (version 20250114) (generator "kicad_symbol_editor") '+''.join(all_libs)+')\n')
    (ROOT/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "Buck") (type "KiCad") (uri "${KIPRJMOD}/Buck.kicad_sym") (options "") (descr "Pin-level original design symbols")))\n')

def board():
    b=pcb.BOARD(); nets={}; io=pcb.PCB_IO_KICAD_SEXPR()
    b.GetTitleBlock().SetTitle('BUCK REV A - FABRICATION ON HOLD')
    b.GetTitleBlock().SetRevision('A')
    for n in sorted({n for p in PARTS for n in p['pins'].values() if n}):
        ni=pcb.NETINFO_ITEM(b,n); b.Add(ni);nets[n]=ni
    for p in PARTS:
        for num,net in p['pins'].items():
            if net is None:
                name=PIN_NAMES.get(p['ref'],['NC']*14)[int(num)-1]
                n=f'unconnected-({p["ref"]}-{name}-Pad{num})'
                ni=pcb.NETINFO_ITEM(b,n);b.Add(ni);nets[n]=ni
    local=ROOT/'Buck.pretty';local.mkdir(exist_ok=True)
    # Provisional lead geometry, 25 mm maximum body, 10 mm pitch.
    fp=pcb.FOOTPRINT(b); fp.SetReference('L');fp.SetValue('330uH VERIFY')
    for num,x in [('1',-5),('2',5)]:
        pad=pcb.PAD(fp);pad.SetNumber(num);pad.SetShape(pcb.PAD_SHAPE_CIRCLE);pad.SetAttribute(pcb.PAD_ATTRIB_PTH);pad.SetPosition(pos(x,0));pad.SetSize(pos(3,3));pad.SetDrillSize(pos(1.3,1.3));pad.SetLayerSet(pcb.PAD.PTHMask());fp.Add(pad)
    for layer,rad in [(pcb.F_SilkS,12.5),(pcb.F_Fab,12.5),(pcb.F_CrtYd,13)]:
        shape=pcb.PCB_SHAPE(fp);shape.SetShape(pcb.SHAPE_T_CIRCLE);shape.SetCenter(pos(0,0));shape.SetEnd(pos(rad,0));shape.SetLayer(layer);shape.SetWidth(pcb.FromMM(.15));fp.Add(shape)
    # Save with an explicit library name independent of reference/value.
    fp.SetFPID(pcb.LIB_ID('Buck','Inductor_25mm_P10mm_VERIFY'));io.FootprintSave(str(local),fp)
    for p in PARTS:
        lib,name=p['footprint'].split(':');path=local if lib=='Buck' else LIB/(lib+'.pretty')
        f=io.FootprintLoad(str(path),name)
        if f is None: raise RuntimeError(p['footprint'])
        f.SetReference(p['ref']);f.SetValue(p['value']);f.SetFPID(pcb.LIB_ID(lib,name));f.SetPosition(pos(*p['xy']));f.SetOrientationDegrees(p['rotation'])
        f.SetExcludedFromBOM(False)
        if lib=='Buck':
            label=pcb.PCB_TEXT(f);label.SetText(p['ref']);label.SetPosition(pos(*p['xy']));label.SetTextSize(pos(1,1));label.SetTextThickness(pcb.FromMM(.15));label.SetLayer(pcb.F_Fab);f.Add(label)
        f.SetPath(pcb.KIID_PATH('/'+ROOT_ID+'/'+uid(f'sheet{p["section"]}')+'/'+uid(p['ref'])))
        for pad in f.Pads():
            net=p['pins'].get(pad.GetNumber())
            if net:pad.SetNet(nets[net])
            else:
                pinname=PIN_NAMES.get(p['ref'],['NC']*14)[int(pad.GetNumber())-1]
                pad.SetNet(nets[f'unconnected-({p["ref"]}-{pinname}-Pad{pad.GetNumber()})'])
        f.Reference().SetTextSize(pos(.8,.8));f.Reference().SetTextThickness(pcb.FromMM(.12));f.Value().SetVisible(False)
        for ref,xy in {'C1':(15.5,25),'R2':(37,23),'D1':(42,29),'R1':(56.5,25)}.items():
            if p['ref']==ref:f.Reference().SetPosition(pos(*xy));f.Reference().SetTextAngle(pcb.EDA_ANGLE(0,pcb.DEGREES_T))
        b.Add(f)
    for a,z in [((10,10),(109,10)),((109,10),(109,109)),((109,109),(10,109)),((10,109),(10,10))]:
        edge=pcb.PCB_SHAPE();edge.SetShape(pcb.SHAPE_T_SEGMENT);edge.SetStart(pos(*a));edge.SetEnd(pos(*z));edge.SetLayer(pcb.Edge_Cuts);edge.SetWidth(pcb.FromMM(.05));b.Add(edge)
    for text,x,y in [('BUCK REV A - 12V / 10kHz',70,42),('HOLD FAB: VERIFY L1/L2',58,107),('12V',22,15)]:
        t=pcb.PCB_TEXT(b);t.SetText(text);t.SetPosition(pos(x,y));t.SetTextSize(pos(.9,.9));t.SetTextThickness(pcb.FromMM(.13));t.SetLayer(pcb.F_SilkS);b.Add(t)
    settings=b.GetDesignSettings();settings.m_CopperEdgeClearance=pcb.FromMM(.3);settings.m_MinClearance=pcb.FromMM(.2);settings.m_TrackMinWidth=pcb.FromMM(.2)
    pcb.PCB_IO_KICAD_SEXPR(0).SaveBoard(str(ROOT/'buck.kicad_pcb'),b,None)
    if not pcb.ExportSpecctraDSN(b,str(ROOT/'buck.dsn')):raise RuntimeError('DSN export failed')
    dsn=(ROOT/'buck.dsn').read_text();power={'VIN','GND','SW','LMID','IP','VOUT'}
    start=dsn.index('(class kicad_default');end=dsn.index('(circuit',start)
    tokens=dsn[start:end].split()[2:];signals=[n for n in tokens if n not in power]
    dsn=dsn[:start]+'(class kicad_default '+' '.join(signals)+'\n      '+dsn[end:]
    dsn=dsn.replace('(width 200)','(width 300)').replace('(clearance 200)','(clearance 250)')
    dsn=dsn.replace('  )\n  (wiring','    (class power '+' '.join(sorted(power))+' (circuit (use_via "Via[0-1]_600:300_um")) (rule (width 600) (clearance 250)))\n  )\n  (wiring')
    dsn=dsn.replace('Via[0-1]_600:300_um','Via[0-1]_1200:600_um').replace('(circle F.Cu 600)', '(circle F.Cu 1200)').replace('(circle B.Cu 600)', '(circle B.Cu 1200)')
    (ROOT/'buck.dsn').write_text(dsn)

def main():
    schematic();board()
    with (ROOT/'bom.csv').open('w') as f:
        w=csv.writer(f);w.writerow(['Reference','Value','Footprint','Quantity','Qualification'])
        for p in PARTS:w.writerow([p['ref'],p['value'],p['footprint'],1,p['note']])
    (ROOT/'design.json').write_text(json.dumps(PARTS,indent=2)+'\n')
    entries=['(lib (name "Buck") (type "KiCad") (uri "${KIPRJMOD}/Buck.pretty") (options "") (descr "Project-specific provisional inductor geometry"))']
    for lib in sorted({p['footprint'].split(':')[0] for p in PARTS}-{'Buck'}):
        entries.append(f'(lib (name "{lib}") (type "KiCad") (uri "${{KICAD10_FOOTPRINT_DIR}}/{lib}.pretty") (options "") (descr "KiCad standard library"))')
    (ROOT/'fp-lib-table').write_text('(fp_lib_table (version 7) '+''.join(entries)+')\n')
    base={'name':'Default','clearance':.25,'track_width':.3,'via_diameter':1.2,'via_drill':.6,'microvia_diameter':.3,'microvia_drill':.1,'diff_pair_width':.3,'diff_pair_gap':.25,'diff_pair_via_gap':.25}
    power=dict(base,name='Power',track_width=.6)
    (ROOT/'buck.kicad_pro').write_text(json.dumps({'meta':{'filename':'buck.kicad_pro','version':1},'net_settings':{'classes':[base,power], 'netclass_patterns':[{'netclass':'Power','pattern':n} for n in ['VIN','GND','SW','LMID','IP','VOUT']], 'meta':{'version':4}}},indent=2))
if __name__=='__main__':main()
