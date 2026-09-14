"""Document contract checks using the actual saved coursework evidence."""
import json
from pathlib import Path
import re
import unittest
import numpy as np
from report_content import AUTHORS, reports
from build_reports import document, extrema_indices, validate_numbers

ROOT=Path(__file__).resolve().parents[1]

class ReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m=json.loads((ROOT/'results/matlab/results.json').read_text())
        cls.a=json.loads((ROOT/'results/simulation/results.json').read_text())

    def test_numerical_design_matches_sources(self):
        result=validate_numbers(self.m,self.a)
        self.assertAlmostEqual(result['plant_magnitude_at_crossover_V'],12.085663179055134)
        bad=json.loads(json.dumps(self.a)); bad['parameters']['L']*=2
        with self.assertRaisesRegex(ValueError,'Inconsistent source parameter'):
            validate_numbers(self.m,bad)

    def test_equations_references_authors_and_pending_status(self):
        specs=list(reports(self.m,self.a))
        self.assertEqual([s[0] for s in specs],[1,2,3,4])
        for spec in specs:
            tex,md=document(*spec)
            self.assertIn(r'\documentclass[conference,letterpaper]{IEEEtran}',tex)
            self.assertIn('$$',md)
            self.assertNotRegex(md,r'\\(?:cite|eqref|ref)\{')
            for name,email in AUTHORS:
                self.assertIn(name,tex); self.assertIn(email,tex)
            labels=re.findall(r'\\label\{([^}]+)\}',tex)
            self.assertEqual(len(labels),len(set(labels)))
            for ref in re.findall(r'\\(?:eqref|ref)\{([^}]+)\}',tex):
                self.assertIn(ref,labels)
            self.assertNotRegex(tex,r'[₀-₉⁰¹²³⁴⁵⁶⁷⁸⁹]')
            if spec[0] in (2,4):
                self.assertIn('Pendiente',tex)
                self.assertIn('experimental',tex)

    def test_display_reduction_preserves_spikes_and_endpoints(self):
        y=np.sin(np.linspace(0,20,10000)); y[321]=17; y[6789]=-21
        idx=extrema_indices(y,100)
        self.assertIn(321,idx); self.assertIn(6789,idx)
        self.assertEqual(idx[0],0); self.assertEqual(idx[-1],len(y)-1)
        self.assertTrue(np.all(np.diff(idx)>0))
        self.assertLessEqual(len(idx),202)

    def test_hardware_figures_and_distinct_evidence(self):
        specs={s[0]:s for s in reports(self.m,self.a)}
        tex,md=document(*specs[2])
        self.assertIn(r'\includegraphics[width=\columnwidth]{assets/pcb-3d.png}',tex)
        self.assertIn('![pcb-3d](assets/pcb-3d.png)',md)
        self.assertIn('no es una fotografía',tex)
        self.assertIn('envolvente provisional',tex)
        for spec in specs.values():
            for block in spec[-1]:
                if block.asset:
                    self.assertTrue((ROOT/'pcb/release/report-assets'/block.asset).is_file())
        tex,_=document(*specs[4])
        self.assertIn('STM32F103C8T6',tex)
        self.assertNotIn('El arranque gradual debe integrarse',tex)
        self.assertIn('Pendiente en MCU',tex)
        tex,_=document(*specs[3])
        self.assertIn('no reproduce la recomendación usual',tex)
        self.assertIn('Resultados adicionales estimados; no medidos',tex)

if __name__=='__main__': unittest.main()
