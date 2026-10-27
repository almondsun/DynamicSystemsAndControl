"""Read-only KiCad source export for a JLCPCB quote; never regenerate the CAD.

Run with the Python bundled with KiCad. Every run creates a new output revision.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from datetime import datetime, timezone
import pcbnew as p

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--project',type=Path,required=True)
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[3]
    source=args.project.resolve()
    assert source.suffix=='.kicad_pro' and source.is_file()
    project=source.parent
    production=project/'production'
    output=production/'jlcpcb-quote-2026-10'
    revision=1
    while output.exists():
        revision+=1; output=production/f'jlcpcb-quote-2026-10-r{revision:02d}'
    output.mkdir(parents=True)
    evidence=output/'evidence'; evidence.mkdir()
    run=root/'artifacts'/('jlcpcb-quote-'+datetime.now().strftime('%Y%m%d-%H%M%S'))
    snapshot=run/'source'; snapshot.mkdir(parents=True)
    files=[f for f in project.iterdir() if f.is_file() and (f.suffix in ['.kicad_pcb','.kicad_sch','.kicad_pro','.kicad_dru','.kicad_sym'] or f.name in ['fp-lib-table','sym-lib-table'])]
    for name in ['Buck.pretty','libraries','models']:
        folder=project/name
        if folder.exists(): files.extend(f for f in folder.rglob('*') if f.is_file())
    manifest=[]
    for f in files:
        rel=f.relative_to(project); dest=snapshot/rel; dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(f,dest)
        assert digest(f)==digest(dest)
        manifest.append(dict(path=f.relative_to(root).as_posix(),snapshot=rel.as_posix(),sha256=digest(f)))
    (evidence/'source_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    board=snapshot/(source.stem+'.kicad_pcb')
    sch=snapshot/(source.stem+'.kicad_sch')
    cli=Path(p.__file__).resolve().parents[3]/'kicad-cli.exe'
    if not cli.exists(): cli=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')
    commands=[]
    def command(*arguments):
        result=subprocess.run([str(cli),*map(str,arguments)],capture_output=True,text=True,encoding='utf-8',errors='replace')
        commands.append(dict(command=[str(cli),*map(str,arguments)],returncode=result.returncode,stdout=result.stdout,stderr=result.stderr))
        print(result.stdout,end='',flush=True)
        if result.stderr: print(result.stderr,end='',flush=True)
        (evidence/'commands.json').write_text(json.dumps(commands,indent=2),encoding='utf-8')
        return result
    command('version')
    command('pcb','drc',board,'--schematic-parity','--refill-zones','--save-board','--severity-all','--all-track-errors','--format','json','--output',evidence/'drc-export.json')
    command('sch','erc',sch,'--severity-all','--format','json','--output',evidence/'erc.json')
    command('sch','export','netlist',sch,'--format','kicadxml','--output',evidence/'schematic.xml')
    drc=json.loads((evidence/'drc-export.json').read_text(encoding='utf-8'))
    violations=drc['violations']+drc['unconnected_items']+drc['schematic_parity']
    error_count=sum(v['severity']=='error' for v in violations)
    (output/'validation_report.md').write_text('# Preflight de exportación\n\n'+f'Errores DRC: {error_count}. Reconciliación comercial y de CSV pendiente. No liberado a fabricación.\n',encoding='utf-8')
    b=p.LoadBoard(str(board))
    layers=['F.Cu','B.Cu','F.Mask','B.Mask','F.Silkscreen','B.Silkscreen','F.Paste','B.Paste','Edge.Cuts']
    assert b.GetCopperLayerCount()==2,'Review layer selection for this stackup'
    command('pcb','export','gerbers',board,'--layers',','.join(layers),'--output',str(output/'gerbers')+'/')
    command('pcb','export','drill',board,'--format','excellon','--drill-origin','absolute','--excellon-units','mm','--excellon-zeros-format','decimal','--excellon-separate-th','--generate-report','--report-path',evidence/'drill-report.txt','--output',str(output/'gerbers')+'/')
    command('pcb','export','pos',board,'--format','csv','--units','mm','--output',evidence/'positions-native.csv')
    command('pcb','export','svg',board,'--layers','F.Cu,F.Silkscreen,Edge.Cuts','--mode-single','--fit-page-to-board','--exclude-drawing-sheet','--output',evidence/'front-native.svg')
    command('pcb','export','svg',board,'--layers','B.Cu,B.Silkscreen,Edge.Cuts','--mode-single','--fit-page-to-board','--exclude-drawing-sheet','--mirror','--output',evidence/'back-native.svg')
    footprints=[]
    for f in b.GetFootprints():
        fields={x.GetName():x.GetText() for x in f.GetFields()}
        pads=[]
        for pad in f.Pads():
            pos=pad.GetPosition(); size=pad.GetSize(); drill=pad.GetDrillSize()
            pads.append(dict(number=pad.GetNumber(),net=pad.GetNetname(),position_mm=[pos.x/1e6,pos.y/1e6],size_mm=[size.x/1e6,size.y/1e6],drill_mm=[drill.x/1e6,drill.y/1e6],type=int(pad.GetAttribute())))
        pos=f.GetPosition()
        footprints.append(dict(ref=f.GetReference(),value=f.GetValue(),footprint=f.GetFPID().GetUniStringLibId(),uuid=f.m_Uuid.AsString(),position_mm=[pos.x/1e6,pos.y/1e6],rotation=f.GetOrientationDegrees(),layer=f.GetLayerName(),attributes=f.GetAttributes(),dnp=f.IsDNP(),exclude_bom=f.IsExcludedFromBOM(),exclude_pos=f.IsExcludedFromPosFiles(),fields=fields,pads=pads))
    box=b.GetBoardEdgesBoundingBox(); size=box.GetSize()
    inventory=dict(footprints=footprints,dimensions_including_edge_stroke_mm=[size.x/1e6,size.y/1e6],copper_layers=b.GetCopperLayerCount(),board_thickness_mm=b.GetDesignSettings().GetBoardThickness()/1e6,aux_origin_mm=[b.GetDesignSettings().GetAuxOrigin().x/1e6,b.GetDesignSettings().GetAuxOrigin().y/1e6])
    (evidence/'pcb_inventory.json').write_text(json.dumps(inventory,indent=2),encoding='utf-8')
    command('pcb','drc',board,'--schematic-parity','--severity-all','--all-track-errors','--format','json','--output',evidence/'drc-final.json')
    assert all(digest(root/m['path'])==m['sha256'] for m in manifest),'Original source changed during export'
    context=dict(output=output.relative_to(root).as_posix(),run=run.relative_to(root).as_posix(),snapshot=board.relative_to(root).as_posix(),source=source.relative_to(root).as_posix(),utc=datetime.now(timezone.utc).isoformat(),source_unchanged=True,source_board_sha256=digest(project/board.name),export_board_sha256=digest(board),error_count=error_count)
    (evidence/'context.json').write_text(json.dumps(context,indent=2),encoding='utf-8')
    (root/'artifacts/jlcpcb-quote-current.txt').write_text(str(output),encoding='utf-8')
    print('OUTPUT:',output,flush=True)

if __name__=='__main__': main()
