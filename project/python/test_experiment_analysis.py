"""Synthetic numerical tests only; these are not laboratory measurements."""
import unittest
import numpy as np
from scipy.signal import StateSpace, lsim
from analyze_experiment import predict


class CaptureValidation(unittest.TestCase):
    def setUp(self):
        self.p = dict(Vin=12., L_H=660e-6, C_F=20e-6, R_ohm=6.,
                      step_time_s=.01, initial_current_A=1.)
        self.d = np.zeros(201, dtype=[(n,float) for n in
            ['time_s','voltage_V','dprime','load_ohm','reference_V']])
        self.d['time_s'] = np.arange(201)*1e-4
        self.d['voltage_V'] = 6
        self.d['dprime'] = np.where(self.d['time_s']<.01,.5,.6)
        self.d['load_ohm'] = self.d['reference_V'] = 6

    def test_known_state_space_response(self):
        L,C,R = self.p['L_H'],self.p['C_F'],6
        sys = StateSpace([[0,-1/L],[1/C,-1/(R*C)]],[[12/L],[0]],[[0,1]],[[0]])
        _, expected, _ = lsim(sys,1-self.d['dprime'],self.d['time_s'],X0=[1,6],interp=False)
        np.testing.assert_allclose(predict(self.d,self.p),expected,atol=1e-10)
        self.assertAlmostEqual(expected[-1],4.8,places=7)

    def test_reject_bad_data(self):
        for field,value in [('time_s',-1.),('dprime',1.2),('voltage_V',np.nan),('load_ohm',0.)]:
            bad = self.d.copy(); bad[field][2] = value
            with self.assertRaises(ValueError):
                predict(bad,self.p)


if __name__ == '__main__':
    unittest.main()
