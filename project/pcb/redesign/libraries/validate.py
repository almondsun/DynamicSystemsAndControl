"""Read-only validation of project-local Buck_SMD libraries. Python 3.11+."""
from pathlib import Path
import hashlib,json,re,sys
from _sexpr import parse,children,first,prop,pin_signature,walk

def validate():
 lib=Path(__file__).resolve().parent;pcb=lib.parent;data=json.loads((lib/'integration_data.json').read_text(encoding='utf8'))
 symbols=children(parse((lib/'symbols/Buck_SMD.kicad_sym').read_text(encoding='utf8')),'symbol')
 names=[str(s[1]) for s in symbols];assert len(names)==len(set(n.casefold() for n in names))==9
 for table_name,uri in [('sym-lib-table','${KIPRJMOD}/libraries/symbols/Buck_SMD.kicad_sym'),('fp-lib-table','${KIPRJMOD}/libraries/footprints/Buck_SMD.pretty')]:
  tree=parse((pcb/table_name).read_text(encoding='utf8'));entries=children(tree,'lib');registered=[str(first(e,'name')[1]) for e in entries]
  assert len(registered)==len(set(n.casefold() for n in registered)),table_name
  assert children(parse(data['original_tables'][table_name]),'lib')==[e for e in entries if first(e,'name')[1]!='Buck_SMD'],table_name
  entry=next(e for e in entries if first(e,'name')[1]=='Buck_SMD');assert first(entry,'uri')[1]==uri
  assert Path(str(first(entry,'uri')[1]).replace('${KIPRJMOD}',str(pcb))).exists()
 fps={p.stem:parse(p.read_text(encoding='utf8')) for p in (lib/'footprints/Buck_SMD.pretty').glob('*.kicad_mod')}
 assert len(fps)==25
 geometries={};same_geometry=[];model_paths=set();warnings=[]
 for name,fp in fps.items():
  assert str(fp[1])==name,name
  expected=data['footprints'][name];pads=children(fp,'pad')
  assert {str(p[1]) for p in pads}=={p['number'] for p in expected['pads']},name
  assert all(p[2]=='smd' and set(first(p,'layers')[1:])=={'F.Cu','F.Paste','F.Mask'} for p in pads),name
  assert all(all(float(v)>0 for v in first(p,'size')[1:]) for p in pads),name
  assert not expected['geometry_changed']
  if not expected['courtyard']:warnings.append(name+': courtyard absent in supplier footprint')
  if not expected['silkscreen']:warnings.append(name+': silkscreen absent in supplier footprint')
  for m in children(fp,'model'):
   path=str(m[1]);assert path.startswith('${KIPRJMOD}/libraries/3dmodels/'),path
   target=Path(path.replace('${KIPRJMOD}',str(pcb)));assert target.is_file(),path;model_paths.add(target)
   assert first(first(m,'scale'),'xyz')[1:]==['1','1','1']
  geometry=[x for x in fp[2:] if not(isinstance(x,list) and x[0] in {'tags','fp_text','property','model','generator','version'})]
  h=hashlib.sha256(json.dumps(geometry,sort_keys=True).encode()).hexdigest()
  if h in geometries:same_geometry.append([geometries[h],name])
  else:geometries[h]=name
 for s in symbols:
  name=str(s[1]);original=data['source_symbols'][name]
  assert pin_signature(s)==sorted(tuple(v) for v in original['pins']),name
  assert prop(s,'Reference')[2]==original['reference'] and prop(s,'Value')[2]==original['value']
  for field in ['Footprint','ki_fp_filters']:
   for identifier in str(prop(s,field)[2]).split():
    namespace,fpname=identifier.split(':',1);assert namespace=='Buck_SMD' and fpname in fps,(name,identifier)
  fpname=str(prop(s,'Footprint')[2]).split(':')[1]
  assert {p[0] for p in pin_signature(s)}=={str(p[1]) for p in children(fps[fpname],'pad')},name
  assert str(prop(s,'Datasheet')[2]).startswith('https://'),name
 hashes={};duplicates=[]
 for p in (lib/'3dmodels').iterdir():
  h=hashlib.sha256(p.read_bytes()).hexdigest()
  assert h==data['models'][p.name]['sha256'],p
  if h in hashes:duplicates.append([hashes[h],p.name])
  hashes[h]=p.name
 assert not duplicates
 for name,info in data['datasheets'].items():assert hashlib.sha256((lib/'datasheets'/name).read_bytes()).hexdigest()==info['sha256']
 for row in data['provenance']:
  p=pcb/row['destination'];assert p.exists(),p
  # The symbol container is shared by all nine input files.
  assert hashlib.sha256(p.read_bytes()).hexdigest()==row['destination_sha256'],p
 return {'symbols':len(symbols),'footprints':len(fps),'stored_models':len(hashes),'linked_unique_models':len(model_paths),'unlinked_models':[p.name for p in (lib/'3dmodels').iterdir() if p not in model_paths],'same_geometry_pairs':same_geometry,'warnings':warnings,'preserved_pin_names_types_and_numbers':True,'existing_table_entries_preserved':True,'active_paths_portable':True,'electrical_approval':False}

if __name__=='__main__':
 print(json.dumps(validate(),ensure_ascii=False,indent=2))
