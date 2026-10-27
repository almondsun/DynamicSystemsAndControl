"""Read-only check of final source hashes, backup and preserved CAD snapshots."""
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET
import zipfile

evidence = Path(__file__).resolve().parent
repo = Path(__file__).resolve().parents[4]
load = lambda name: json.loads((evidence / name).read_text(encoding='utf-8'))
summary = load('verification.json')
before, after = load('board-before.json'), load('board-after.json')
original = {t['uuid']: t for t in before['tracks']}
current = {t['uuid']: t for t in after['tracks']}
assert all(current.get(uid) == t for uid, t in original.items())
approved = {t['uuid']: t for t in summary.get('approved_additions', [])}
assert set(current) - set(original) == set(approved)
assert all(current[uid] == t for uid, t in approved.items())
assert [(f['uuid'], f['pos'], f['angle'], f['pads']) for f in before['footprints']] == [(f['uuid'], f['pos'], f['angle'], f['pads']) for f in after['footprints']]
assert [g for g in before['drawings'] if g['layer'] in ['F.Cu', 'B.Cu']] == [g for g in after['drawings'] if g['layer'] in ['F.Cu', 'B.Cu']]
def endpoints(name):
    return sorted((n.get('name'), sorted((p.get('ref'), p.get('pin')) for p in n)) for n in ET.parse(evidence / name).findall('./nets/net'))
assert endpoints('schematic-before.xml') == endpoints('schematic-after.xml')
for path, expected in summary['final_source_sha256'].items():
    assert hashlib.sha256((repo / path).read_bytes()).hexdigest() == expected, path
backup = repo / 'artifacts/pcb-final-20261026-235708/initial-cad.zip'
assert hashlib.sha256(backup.read_bytes()).hexdigest() == summary['backup_sha256']
with zipfile.ZipFile(backup) as archive:
    for entry in load('backup-manifest.json'):
        assert hashlib.sha256(archive.read(entry['path'].replace('\\', '/'))).hexdigest() == entry['sha256']
print('PASS: backup verified; placement, pads, routing, copper polygons and netlist preserved; final source hashes match.')
print('DRC remains BLOCKED:', summary['drc_after']['counts'])
