import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))
from jyotish_engine import compute_chart_data, _apply_ayanamsa

class TestAyanamsaSwitching(unittest.TestCase):
    def test_ayanamsa_differences(self):
        # REDACTED_DATE 14:45, REDACTED_PLACE
        year, month, day = REDACTED_YEAR, 4, 17
        hour, minute, second = 14, 45, 20
        lat, lon, tz = 36.466667, 114.2, 8

        # 1. Lahiri
        _apply_ayanamsa('lahiri')
        chart_lahiri = compute_chart_data(year, month, day, hour, minute, lat, lon, tz, second=second)
        sun_lahiri = chart_lahiri[0]['planets']['Sun']['degree_raw']

        # 2. Raman
        _apply_ayanamsa('raman')
        chart_raman = compute_chart_data(year, month, day, hour, minute, lat, lon, tz, second=second)
        sun_raman = chart_raman[0]['planets']['Sun']['degree_raw']

        # 3. KP
        _apply_ayanamsa('kp')
        chart_kp = compute_chart_data(year, month, day, hour, minute, lat, lon, tz, second=second)
        sun_kp = chart_kp[0]['planets']['Sun']['degree_raw']

        # Assertions
        self.assertNotEqual(sun_lahiri, sun_raman, "Lahiri and Raman longitudes must differ")
        self.assertNotEqual(sun_lahiri, sun_kp, "Lahiri and KP longitudes must differ")
        self.assertNotEqual(sun_raman, sun_kp, "Raman and KP longitudes must differ")

        self.assertTrue(abs(sun_lahiri - sun_raman) > 0.5, "Difference should be significant")

    def test_compute_chart_data_accepts_direct_ayanamsa_name(self):
        year, month, day = REDACTED_YEAR, 4, 17
        hour, minute, second = 14, 45, 20
        lat, lon, tz = 36.466667, 114.2, 8

        chart_lahiri = compute_chart_data(
            year, month, day, hour, minute, lat, lon, tz,
            second=second,
            ayanamsa_name='lahiri',
        )[0]
        chart_raman = compute_chart_data(
            year, month, day, hour, minute, lat, lon, tz,
            second=second,
            ayanamsa_name='raman',
        )[0]

        self.assertEqual(chart_raman['birth_info']['ayanamsa_name'], 'raman')
        self.assertLess(chart_raman['birth_info']['ayanamsa'], chart_lahiri['birth_info']['ayanamsa'])
        self.assertNotEqual(
            chart_lahiri['planets']['Sun']['degree_raw'],
            chart_raman['planets']['Sun']['degree_raw'],
        )

if __name__ == '__main__':
    unittest.main()
