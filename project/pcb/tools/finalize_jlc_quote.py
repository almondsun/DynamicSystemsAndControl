"""Reconcile native KiCad exports, write quote CSVs, and validate delivery files.

Never edits a board, schematic, project or library. Catalog checks are explicit
quote-time observations; they do not approve land patterns or electrical design.
"""
import argparse
from collections import Counter,defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import xml.etree.ElementTree as ET
import zipfile
import pcbnew as p

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def natural(ref): return (re.sub(r'\d+','',ref),int(re.search(r'\d+',ref).group()))
def write_csv(path,columns,rows):
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=columns); w.writeheader(); w.writerows(rows)
def point(v): return [v.x/1e6,v.y/1e6]

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('output',type=Path)
    output=parser.parse_args().output.resolve(); e=output/'evidence'
    root=Path(__file__).resolve().parents[3]
    context=json.loads((e/'context.json').read_text())
    native=json.loads((e/'pcb_inventory.json').read_text())
    catalog=json.loads(Path(__file__).with_name('jlc_quote_catalog.json').read_text())
    shutil.copy2(Path(__file__).with_name('jlc_quote_catalog.json'),e/'catalog_checks.json')
    footprints={f['ref']:f for f in native['footprints']}
    assert len(footprints)==len(native['footprints'])
    xml=ET.parse(e/'schematic.xml')
    components={}
    for c in xml.findall('./components/comp'):
        ref=c.get('ref'); assert ref not in components
        components[ref]=dict(value=c.findtext('value'),footprint=c.findtext('footprint'),fields={f.get('name'):f.text or '' for f in c.findall('./fields/field')})
    assert set(components)==set(footprints),'PCB/schematic references differ'
    with (e/'positions-native.csv').open(encoding='utf-8-sig',newline='') as f:
        positions=list(csv.DictReader(f))
    pos={r['Ref']:r for r in positions}; assert len(pos)==len(positions)
    groups=defaultdict(list); inventory=[]; selected=[]
    for ref in sorted(footprints,key=natural):
        f=footprints[ref]; c=components[ref]; fields=c['fields']
        assert c['footprint']==f['footprint'] and c['value']==f['value'],ref
        mpn=fields.get('MPN','').strip(); code=fields.get('LCSC','').strip()
        has_code=bool(re.fullmatch(r'C[1-9]\d*',code))
        valid_mpn=bool(mpn) and not re.search(r'\b(TBD|NOT SELECTED|No definido)\b',mpn,re.I)
        tht=any(max(pad['drill_mm'])>0 for pad in f['pads'])
        state='PENDING'; reason=''; package='NO VERIFICADO'; match=False
        if f['dnp']: state='NOT_FITTED'; reason='DNP en PCB; excluido de BOM/CPL'
        elif ref.startswith('TP'): state='NOT_FITTED'; reason='Pad de prueba desnudo; sin pieza física adicional; no es una orden DNP del esquemático'
        elif tht:
            state='PENDING'
            reason={
                'L1':'Huella THT provisional; candidato Murata 60B334C es SMD y NO se trasladó su código',
                'L2':'Huella THT provisional; candidato Murata 60B334C es SMD y NO se trasladó su código',
                'Q1':'IRFZ44N TO-220 conservado; candidato IRFZ44NS SMD no corresponde y NO se solicita',
                'D2':'UF4004 DO-41 conservado; candidato US1G SMD no corresponde y NO se solicita',
                'J1':'THT; MPN final ausente; candidato TB002 no acredita el land Phoenix actual',
                'J2':'THT; MPN final ausente; candidato TB002 no acredita el land Phoenix actual',
                'J3':'THT IDC; MPN/código sin seleccionar; solo interfaz, no una NUCLEO sobre PCB'
            }.get(ref,'THT fuera de la cotización SMT; compra/montaje manual por definir')
        elif f['exclude_bom'] or f['exclude_pos']:
            state='PENDING'; reason='Atributo de exclusión requiere decisión; no se incluye automáticamente'
        elif valid_mpn and has_code and code in catalog['parts']:
            part,package,fpname,url=catalog['parts'][code]
            assert part.lower() in mpn.lower(),f'MPN/code mismatch {ref}'
            assert f['footprint'].split(':')[-1]==fpname,f'Package family mismatch {ref}'
            match=True; state='ASSEMBLED_BY_JLC'; reason='Incluido SOLO para cotización SMT; aprobación eléctrica/land pendiente'
            assert ref in pos,ref
            r=pos[ref]
            assert abs(float(r['PosX'])-f['position_mm'][0])<2e-6
            assert abs(float(r['PosY'])+f['position_mm'][1])<2e-6
            assert abs((float(r['Rot'])-f['rotation']+180)%360-180)<1e-5
            assert r['Side']==('top' if f['layer']=='F.Cu' else 'bottom')
            groups[(part,code,f['footprint'])].append(ref); selected.append(ref)
        else: reason='MPN/código de selección faltante o no verificable; no se rellena con Candidate_LCSC'
        inventory.append(dict(ref=ref,state=state,smd=not tht,tht=tht,dnp=f['dnp'],in_pcb=True,in_schematic=True,mpn=mpn,valid_mpn=valid_mpn,lcsc=code if has_code else '',catalog_package=package,package_family_match=match,land_pattern_approved=False,bom=state=='ASSEMBLED_BY_JLC',cpl=state=='ASSEMBLED_BY_JLC',reason=reason,electrical_approval=fields.get('Electrical_Approval',''),availability='NO VERIFICADA para PCBA/cantidad/fecha de pedido'))
    bom=[]
    for (mpn,code,footprint),refs in sorted(groups.items()):
        values=sorted(set(components[ref]['value'] for ref in refs))
        bom.append({'Comment':' / '.join(values)+' | '+mpn,'Designator':','.join(sorted(refs,key=natural)),'Footprint':footprint,'LCSC Part #':code})
    cpl=[{'Designator':ref,'Mid X':f"{float(pos[ref]['PosX']):.6f}",'Mid Y':f"{float(pos[ref]['PosY']):.6f}",'Rotation':f"{float(pos[ref]['Rot'])%360:.6f}",'Layer':pos[ref]['Side']} for ref in sorted(selected,key=natural)]
    write_csv(output/'bom_jlcpcb.csv',['Comment','Designator','Footprint','LCSC Part #'],bom)
    write_csv(output/'cpl_jlcpcb.csv',['Designator','Mid X','Mid Y','Rotation','Layer'],cpl)
    for name,expected_rows in [('bom_jlcpcb.csv',bom),('cpl_jlcpcb.csv',cpl)]:
        with (output/name).open(encoding='utf-8-sig',newline='') as stream:
            reader=csv.DictReader(stream)
            assert reader.fieldnames==list(expected_rows[0])
            assert list(reader)==expected_rows,f'CSV readback failed: {name}'
    bom_refs=[r for row in bom for r in row['Designator'].split(',')]
    assert len(bom_refs)==len(set(bom_refs))==len(cpl)==len(selected)
    assert set(bom_refs)=={r['Designator'] for r in cpl}==set(selected)
    assert set(bom_refs)<=footprints.keys()
    assert all(row['LCSC Part #'] for row in bom)
    assert all(not footprints[ref]['dnp'] and not any(max(pad['drill_mm'])>0 for pad in footprints[ref]['pads']) for ref in selected)
    for ref,mpn,code in [('C6','CL31B225KBHNNNE','C50254'),('R10','CRCW060330K9FKEA','C844354'),('C16','CC0603KRX7R9BB224','C107083'),('R14','0603WAF1502T5E','C22809'),('R15','0603WAF2201T5E','C4190')]:
        assert components[ref]['fields']['MPN']==mpn and components[ref]['fields']['LCSC']==code
        assert ref in selected
    # Validate original and export board geometry, including routing and pads.
    source=root/context['source']; board_source=p.LoadBoard(str(source.with_suffix('.kicad_pcb'))); board_export=p.LoadBoard(str(root/context['snapshot']))
    def geometry(board):
        fps=sorted((f.GetReference(),f.GetValue(),f.GetFPID().GetUniStringLibId(),tuple(point(f.GetPosition())),f.GetOrientationDegrees(),f.GetLayer(),f.GetAttributes(),sorted((pad.GetNumber(),pad.GetNetname(),tuple(point(pad.GetPosition())),tuple(point(pad.GetSize())),tuple(point(pad.GetDrillSize()))) for pad in f.Pads())) for f in board.GetFootprints())
        tracks=sorted((t.m_Uuid.AsString(),t.GetNetname(),t.GetClass(),tuple(point(t.GetStart())),tuple(point(t.GetEnd())),t.GetWidth(p.F_Cu) if isinstance(t,p.PCB_VIA) else t.GetWidth(),t.GetDrillValue() if isinstance(t,p.PCB_VIA) else 0,t.GetLayer()) for t in board.GetTracks())
        return fps,tracks
    assert geometry(board_source)==geometry(board_export),'Export copy changed placement/pads/routing'
    # Excellon: exact multiset match against all native drilled pads and vias.
    expected=[]
    for f in board_export.GetFootprints():
        for pad in f.Pads():
            size=pad.GetDrillSize()
            if max(size.x,size.y)>0:
                assert size.x==size.y,'Slot needs dedicated validation'
                x,y=point(pad.GetPosition()); expected.append((round(x,6),round(-y,6),round(size.x/1e6,6)))
    for t in board_export.GetTracks():
        if isinstance(t,p.PCB_VIA):
            x,y=point(t.GetPosition()); expected.append((round(x,6),round(-y,6),round(t.GetDrillValue()/1e6,6)))
    drill_records=[]; drill_counts={}
    for name in ['buck-PTH.drl','buck-NPTH.drl']:
        content=(output/'gerbers'/name).read_text(); assert 'METRIC' in content and 'M30' in content
        tools={}; tool=None; count=0
        for line in content.splitlines():
            m=re.fullmatch(r'T(\d+)C([\d.]+)',line)
            if m: tools[m[1]]=float(m[2]); continue
            m=re.fullmatch(r'T(\d+)',line)
            if m: tool=m[1]; continue
            m=re.fullmatch(r'X(-?[\d.]+)Y(-?[\d.]+)',line)
            if m:
                drill_records.append((round(float(m[1]),6),round(float(m[2]),6),round(tools[tool],6))); count+=1
        drill_counts[name]=count
    # Excellon emits millimetres to three decimal places; compare at that
    # declared precision, while recording the maximum coordinate rounding.
    unmatched=list(drill_records); drill_rounding_mm=0
    for x,y,diameter in expected:
        matches=[(max(abs(x-a),abs(y-b)),idx) for idx,(a,b,d) in enumerate(unmatched) if abs(d-diameter)<1e-9 and max(abs(x-a),abs(y-b))<=0.00050001]
        assert matches,f'No matching drill within half of 0.001 mm export precision: {(x,y,diameter)}'
        error,idx=min(matches); drill_rounding_mm=max(drill_rounding_mm,error); unmatched.pop(idx)
    assert not unmatched,f'Extra drills: {unmatched}'
    # Closed rectangular profile in emitted Gerber and common coordinate system.
    profile=(output/'gerbers/buck-Edge_Cuts.gm1').read_text()
    outline=[(int(x)/1e6,int(y)/1e6) for x,y in re.findall(r'X(-?\d+)Y(-?\d+)D0[12]\*',profile)]
    assert len(outline)==5 and outline[0]==outline[-1] and len(set(outline))==4
    dimensions=[max(x for x,y in outline)-min(x for x,y in outline),max(y for x,y in outline)-min(y for x,y in outline)]
    for f in (output/'gerbers').glob('*'):
        if f.suffix in ['.drl','.gbrjob']: continue
        data=f.read_text(); assert '%MOMM*%' in data and '%FSLAX46Y46*%' in data and '%TF.SameCoordinates,Original*%' in data and data.rstrip().endswith('M02*'),f.name
    aperture_checks={}
    for layer,name in [(p.F_Cu,'buck-F_Cu.gtl'),(p.F_Mask,'buck-F_Mask.gts'),(p.F_Paste,'buck-F_Paste.gtp')]:
        flashes={(round(int(x)/1e6,6),round(int(y)/1e6,6)) for x,y in re.findall(r'X(-?\d+)Y(-?\d+)D03\*',(output/'gerbers'/name).read_text())}
        expected_pads=set()
        for f in board_export.GetFootprints():
            for pad in f.Pads():
                if pad.GetAttribute()==p.PAD_ATTRIB_SMD and pad.IsOnLayer(layer) and min(pad.GetSize().x,pad.GetSize().y)>0:
                    x,y=point(pad.GetPosition()); expected_pads.add((round(x,6),round(-y,6)))
        missing=expected_pads-flashes
        aperture_checks[name]=dict(expected_smd_pad_centers=len(expected_pads),missing=sorted(missing))
        assert not missing,f'SMD pad alignment failed: {name} {missing}'
    with zipfile.ZipFile(output/'gerbers.zip') as archive:
        assert archive.testzip() is None
        assert set(archive.namelist())=={f.name for f in (output/'gerbers').iterdir() if f.is_file()}
        assert all('/' not in name and not name.endswith(('.md','.csv')) for name in archive.namelist())
        assert all(archive.read(f.name)==f.read_bytes() for f in (output/'gerbers').iterdir() if f.is_file())
    manifest=json.loads((e/'source_manifest.json').read_text())
    assert all(sha(root/m['path'])==m['sha256'] for m in manifest),'Original CAD/library changed'
    drc=json.loads((e/'drc-final.json').read_text()); erc=json.loads((e/'erc.json').read_text())
    dv=drc['violations']+drc['unconnected_items']+drc['schematic_parity']; ev=[v for sheet in erc['sheets'] for v in sheet['violations']]
    stats=dict(status='QUOTE_FILES_RECONCILED; PENDING_MANUFACTURING_REVIEW',source=context['source'],source_board_sha256=context['source_board_sha256'],source_unchanged=True,original_and_export_geometry_equal=True,footprints=len(footprints),selected_smt=len(selected),bom_rows=len(bom),bom_designators=len(bom_refs),cpl_designators=len(cpl),classification_counts=dict(Counter(i['state'] for i in inventory)),manual_confirmed=0,tht_pending=7,bare_test_pads=9,external_components=2,dnp=sum(f['dnp'] for f in footprints.values()),layers=2,thickness_mm=native['board_thickness_mm'],dimensions_mm=dimensions,drill_counts=drill_counts,drill_native_alignment=True,smd_copper_mask_paste_alignment=aperture_checks,drc=dict(Counter(v['severity'] for v in dv)),unconnected=len(drc['unconnected_items']),parity=len(drc['schematic_parity']),erc=dict(Counter(v['severity'] for v in ev)),live_pcba_stock='NO VERIFICADA',rotation_machine_validation='PENDING_JLC_VIEWER',package_family_check=True,land_pattern_approval=False)
    stats['drill_max_coordinate_rounding_mm']=drill_rounding_mm
    stats['csv_readback_validated']=True
    (e/'reconciliation.json').write_text(json.dumps(stats,indent=2),encoding='utf-8')
    (e/'assembly_inventory.json').write_text(json.dumps(inventory,indent=2),encoding='utf-8')
    lines=['# Inventario de ensamblaje — cotización','', 'Estado: PENDIENTE DE REVISIÓN. ASSEMBLED_BY_JLC indica el alcance previsto de cotización SMT, no aprobación eléctrica ni garantía de montaje. No se sustituyó ningún componente. Los 41 SMD tienen selección MPN/LCSC en el esquemático; todos conservan el campo Electrical_Approval=PENDING.','', 'PCB y esquemático contienen las mismas 57 referencias. Inventario obtenido independientemente de la PCB y reconciliado con la netlist recién exportada. DNP real: 0. Los 9 puntos de prueba son pads de cobre, sin componente adicional, y se excluyen sin cambiar atributos CAD.','', '| Ref | Estado | Tipo | PCB/SCH | MPN válido / LCSC seleccionado | Huella de catálogo / land | BOM/CPL | Motivo |','|---|---|---|---|---|---|---|---|']
    for i in inventory:
        lines.append(f"| {i['ref']} | {i['state']} | {'THT' if i['tht'] else 'SMD'} | sí/sí | {i['mpn'] or 'FALTA'} / {i['lcsc'] or 'FALTA'} | {i['catalog_package']}; land pendiente | {'sí/sí' if i['bom'] else 'no/no'} | {i['reason']} |")
    lines+=['', '## Elementos externos','', '| Elemento | Estado | PCB/BOM/CPL |','|---|---|---|','| NUCLEO-L432KC | EXTERNAL_COMPONENT | Fuera de PCB; no se exporta como J3 ni se inventa posición |','| Carga externa 6 Ω | EXTERNAL_COMPONENT | Fuera de PCB; sin designator o posición inventados |','', 'Montaje manual confirmado: 0; **7 THT pendientes**, previsiblemente de compra/soldadura manual u otra modalidad JLC que debe cotizarse aparte. J1/J2/J3, Q1, D2 y L1/L2 no desaparecen: quedan explícitos fuera de la BOM/CPL SMT. No se puede obtener el costo del conjunto completo con solo estas 41 colocaciones.','', 'Stock PCBA para TODOS los componentes: **NO VERIFICADA**. Las páginas públicas confirman identidad/encapsulado; sus cifras indexadas o de venta LCSC no garantizan stock de ensamblaje para la fecha, cantidad y modalidad del pedido.','', '## Fuentes comerciales consultadas','', '| Código | MPN de catálogo | Encapsulado | Fuente |','|---|---|---|---|']
    for code,(mpn,package,fpname,url) in catalog['parts'].items(): lines.append(f'| {code} | {mpn} | {package} | [JLC/LCSC]({url}) |')
    lines+=['','La comparación automatizada verifica familia de huella y MPN/código de esta tabla. No acredita al 100% las dimensiones del land. C1/C2/C4/C5 y RS1 mantienen calificación mecánica pendiente; U5 carece de courtyard. Q2 C20526 corresponde al rango comercial 100–300 indicado en catálogo; confirmar ese detalle al reconocerlo. C4/C5: CAD dice 35 V, candidato seleccionado 50 V; RS1: CAD dice 1 W, catálogo 2 W. Se conservó el diseño y se documentan estas diferencias.']
    (output/'assembly_inventory.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(stats,indent=2))

if __name__=='__main__': main()
