"""Synthetic-only tests; no Downloads access and no design imports."""
import csv
import json
from pathlib import Path
import tempfile
import time
import unittest
import zipfile

import organize_vendor_assets as app


class OrganizerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.inbox = self.base / 'inbox'
        self.inbox.mkdir()
        self.root = self.base / 'output'
        app.initialize(self.root)
        self.configure([{'mpn': 'TEST-123', 'bom_reference': 'TEST_U1',
                         'aliases': ['UNIQUE_ALIAS'], 'lcsc': '', 'origin': 'synthetic'}])
        self.organizer = app.Organizer(self.root, self.inbox, 0)

    def configure(self, parts):
        (self.root / 'components.json').write_text(json.dumps({'components': parts}), encoding='utf-8')

    def put(self, name, data):
        path = self.inbox / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def batch(self):
        self.organizer.scan()
        self.organizer.scan()
        return self.organizer.rows

    def test_categories_identity_and_corruption(self):
        self.put('TEST-123_datasheet.pdf', b'%PDF-1.7\nsynthetic\n%%EOF')
        self.put('TEST-123.kicad_sym', b'(kicad_symbol_lib (version 20231120))')
        self.put('UNIQUE_ALIAS.kicad_mod', b'(footprint "TEST" (layer "F.Cu"))')
        self.put('TEST-123.step', b'ISO-10303-21;\nEND-ISO-10303-21;')
        self.put('TEST-123_bad.stp', b'broken')
        self.put('unrelated.pdf', b'%PDF-1.7\n%%EOF')
        self.put('TEST-1234.kicad_sym', b'(kicad_symbol_lib)')
        self.put('TEST-123_family.pdf', b'%PDF-1.7\n%%EOF')
        self.put('TEST-123.kicad_mod.crdownload', b'(footprint "TEST")')
        rows = self.batch()
        self.assertEqual(len(rows), 8)
        self.assertEqual({r['category'] for r in rows if r['classification_status'] == 'classified'},
                         {'datasheet', 'symbol', 'footprint', '3d'})
        self.assertEqual(sum(r['classification_status'] == 'pending_review' for r in rows), 4)
        for row in rows:
            self.assertEqual(app.digest(Path(row['source_path'])), row['sha256'])
            self.assertEqual(app.digest(self.root / row['destination']), row['sha256'])

    def test_idempotence_duplicates_and_same_name(self):
        self.put('a/TEST-123.kicad_sym', b'(kicad_symbol_lib)')
        self.put('b/TEST-123.kicad_sym', b'(kicad_symbol_lib (version 1))')
        self.put('TEST-123_copy.kicad_sym', b'(kicad_symbol_lib)')
        rows = self.batch()
        self.assertEqual(len(rows), 3)
        self.assertEqual(len({r['destination'] for r in rows}), 2)
        self.batch()
        self.assertEqual(len(rows), 3)
        restored = app.Organizer(self.root, self.inbox, 0)
        restored.scan()
        restored.scan()
        self.assertEqual(len(restored.rows), 3)

    def test_ambiguous_zip_and_config_reload(self):
        self.configure([{'mpn': 'TEST-123', 'aliases': ['SHARED']},
                        {'mpn': 'TEST-456', 'aliases': ['SHARED']}])
        self.put('SHARED.kicad_sym', b'(kicad_symbol_lib)')
        with zipfile.ZipFile(self.inbox / 'TEST-123.zip', 'w') as archive:
            archive.writestr('../escape.kicad_mod', '(footprint "test")')
        self.put('TEST-456.zip', b'broken ZIP')
        rows = self.batch()
        self.assertTrue(all(r['classification_status'] == 'pending_review' for r in rows))
        self.assertTrue(any('ambiguous' in r['detail'] for r in rows))
        self.assertFalse((self.base / 'escape.kicad_mod').exists())
        self.configure([{'mpn': 'TEST-123', 'aliases': ['SHARED']}])
        self.batch()
        self.assertTrue(any(r['classification_status'] == 'classified' for r in rows))

    def test_download_stability_and_overwrite_refusal(self):
        source = self.put('TEST-123.kicad_sym', b'(kicad_symbol_lib)')
        self.organizer.settle = 100
        self.batch()
        self.assertEqual(self.organizer.rows, [])
        self.organizer.settle = 0
        self.batch()
        destination = self.root / self.organizer.rows[0]['destination']
        destination.write_bytes(b'user modified copy')
        self.assertRaises(ValueError, app.copy_verified, source, destination.parent.parent, app.digest(source))
        self.assertEqual(source.read_bytes(), b'(kicad_symbol_lib)')

    def test_invalid_configuration_and_mpn_encoding(self):
        self.configure([{'mpn': 'TEST-123'}, {'mpn': 'test-123'}])
        self.assertRaises(ValueError, app.load_config, self.root)
        self.assertEqual(app.safe_folder('MPN/EXACT'), 'MPN%2FEXACT')
        self.assertNotEqual(app.safe_folder('CON'), 'CON')


if __name__ == '__main__':
    unittest.main()
