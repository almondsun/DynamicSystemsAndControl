import unittest
from capture import decode
class CaptureTests(unittest.TestCase):
    def fixture(self):
        return ['OK','tick_100us,vo_mV,vref_mV,dprime_10000,mode']+[f'{100+k},6000,6000,5000,3' for k in range(512)]+['END']
    def test_preserves_ticks_and_units(self):
        rows=decode(self.fixture());self.assertEqual(rows[511]['tick_100us'],611);self.assertEqual(rows[0]['vo_mV'],6000)
    def test_rejects_dropped_record(self):
        lines=self.fixture();del lines[10]
        with self.assertRaises(ValueError):decode(lines)
    def test_rejects_repeated_timestamp(self):
        lines=self.fixture();lines[10]=lines[9]
        with self.assertRaises(ValueError):decode(lines)
    def test_rejects_hardware_fault_capture(self):
        lines=self.fixture();lines[10]='108,6000,6000,5000,4'
        with self.assertRaises(ValueError):decode(lines)
if __name__=='__main__':unittest.main()
