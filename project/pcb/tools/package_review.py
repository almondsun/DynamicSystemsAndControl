#!/usr/bin/env python3
"""Stage evidence and create a reproducible list of files for team review."""
import hashlib,json,shutil,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parents[1]
evidence=REPO/'artifacts/buck-pcb-validation'
release=ROOT/'release'
for folder in ['simulation','routing','logs']:(release/folder).mkdir(exist_ok=True)
for p in (evidence/'simulation').glob('*.csv'):shutil.copy2(p,release/'simulation'/p.name)
shutil.copy2(evidence/'simulation/results.json',release/'simulation/results.json')
shutil.copy2(evidence/'buck.ses',release/'routing/buck.ses')
for name in ['export.log','routing.log','gerber-check.log','generate-final.log','firmware-final.log','simulation-final.log','drill-report.txt']:
    shutil.copy2(evidence/name,release/'logs'/name)
files=[]
for folder in [ROOT,REPO/'project/firmware',REPO/'project/hardware',REPO/'project/reports/final',REPO/'project/python',REPO/'project/results']:
    files.extend(p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.zip','.pyc'} and p.name!='package-manifest.json')
files=sorted(files)
manifest={str(p.relative_to(REPO)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
mp=release/'package-manifest.json';mp.write_text(json.dumps({'status':'REVIEW ONLY; fabrication on hold','sha256':manifest},indent=2)+'\n')
path=release/'buck-team-review.zip'
with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
    for p in files+[mp]:z.write(p,p.relative_to(REPO))
with zipfile.ZipFile(path) as z:
    assert z.testzip() is None
    for name,digest in manifest.items():assert hashlib.sha256(z.read(name)).hexdigest()==digest
print(f'PASS: {len(files)} files + manifest, ZIP CRC and SHA-256 verified, {path.stat().st_size} bytes')
print(path)
