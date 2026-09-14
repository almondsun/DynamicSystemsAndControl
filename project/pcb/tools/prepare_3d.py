#!/usr/bin/env python3
"""Download official package geometry and attach it without rerouting the board.

Run with local_env.sh and /usr/bin/python. Inductor envelope is provisional.
"""
import hashlib
import json
import math
from pathlib import Path
import urllib.request
import pcbnew as pcb

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / 'models'
MODELS.mkdir(exist_ok=True)
if not hasattr(pcb.SwigPyIterator, 'next'):
    pcb.SwigPyIterator.next = pcb.SwigPyIterator.__next__
board = pcb.LoadBoard(str(ROOT / 'buck.kicad_pcb'))
sources = {}
for fp in board.GetFootprints():
    updated=[]
    for model in fp.Models():
        rel = model.m_Filename.split('}/', 1)[-1]
        if rel.startswith('models/'):
            rel = rel[len('models/'):]
        if rel == 'inductor-provisional.wrl':
            updated.append(model)
            continue
        target = MODELS / rel
        url = 'https://raw.githubusercontent.com/KiCad/kicad-packages3D/master/' + rel
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            with urllib.request.urlopen(url, timeout=60) as response:
                target.write_bytes(response.read())
        model.m_Filename = '${KIPRJMOD}/models/' + rel
        updated.append(model)
        sources[rel] = {'url': url, 'sha256': hashlib.sha256(target.read_bytes()).hexdigest()}
    fp.Models().clear()
    for model in updated:
        fp.Add3DModel(model)

# VRML units are 0.1 inch. A 25 mm diameter, 10 mm thick toroid envelope,
# standing vertically with its centre between pads. This is NOT a vendor model.
points = []
faces = []
for i in range(64):
    a = 2 * math.pi * i / 64
    for j in range(16):
        b = 2 * math.pi * j / 16
        radius = 8.5 + 4 * math.cos(b)
        points.append(((5 + radius * math.cos(a))/2.54, 5*math.sin(b)/2.54,
                       (13 + radius * math.sin(a))/2.54))
        faces.append((i*16+j, ((i+1)%64)*16+j, ((i+1)%64)*16+(j+1)%16, i*16+(j+1)%16))
wrl = '#VRML V2.0 utf8\nShape { appearance Appearance { material Material { diffuseColor 0.65 0.32 0.08 ambientIntensity 0.4 emissiveColor 0.05 0.025 0.005 } } geometry IndexedFaceSet { solid TRUE creaseAngle 0.6 coord Coordinate { point [\n'
wrl += ',\n'.join(' '.join(map(str,p)) for p in points)
wrl += '] } coordIndex [\n' + ',\n'.join(' '.join(map(str,reversed(f)))+ ' -1' for f in faces) + '] } }\n'
target = MODELS / 'inductor-provisional.wrl'
target.write_text(wrl)
for fp in board.GetFootprints():
    if fp.GetReference() in ('L1','L2') and not fp.Models():
        model = pcb.FP_3DMODEL()
        model.m_Filename = '${KIPRJMOD}/models/inductor-provisional.wrl'
        fp.Add3DModel(model)
pcb.PCB_IO_KICAD_SEXPR(0).SaveBoard(str(ROOT / 'buck.kicad_pcb'), board)
sources[target.name] = {'source': 'Generated provisional envelope; diameter 25 mm, thickness 10 mm, pitch 10 mm; supplier geometry unverified', 'sha256': hashlib.sha256(target.read_bytes()).hexdigest()}
(MODELS / 'manifest.json').write_text(json.dumps(sources, indent=2)+'\n')
print('Attached local 3D models; electrical and routing checks must be rerun.')
