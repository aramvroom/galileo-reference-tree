import unittest
from gnss_monitor.transform import lla2ecef, ecef2enu, ecef2aer


class TestTransform(unittest.TestCase):

    def test_lla2ecef(self):
        # Prepare
        lat, lon, alt = 52.0, 4.0, 50.0
        expected_x, expected_y, expected_z = 3925406, 274491, 5002843

        # Execute
        x, y, z = lla2ecef(lat, lon, alt)

        # Verify
        self.assertAlmostEqual(x, expected_x, delta=1)   # Expected values accurate to the meter
        self.assertAlmostEqual(y, expected_y, delta=1)
        self.assertAlmostEqual(z, expected_z, delta=1)

    def test_geodetic2aer(self):
        # Prepare
        x, y, z = lla2ecef(52.0, 4.0, 50.0)  # Observer's location
        target_lat, target_lon, target_alt = 53.0, 5.0, 100.0  # Target's location
        expected_az, expected_elev, expected_r = 211.7926184361850, -0.607305726367828, 130358.5598826873   # From Octave

        # Execute
        found_az, found_elev, found_range = ecef2aer(x, y, z, target_lat, target_lon, target_alt)

        # Verify
        self.assertAlmostEqual(found_az, expected_az)
        self.assertAlmostEqual(found_elev, expected_elev)
        self.assertAlmostEqual(found_range, expected_r)

    def test_ecef2enu(self):
        # Prepare
        ref_lat, ref_lon = 52.0, 4.0  # Reference point
        dx, dy, dz = 1000.0, 2000.0, 3000.0  # Offset in ECEF
        expected_east, expected_north, expected_up = 1925.371626775511, 950.9555240773523, 3064.086762814848

        # Execute
        east, north, up = ecef2enu(dx, dy, dz, ref_lat, ref_lon)

        # Verify
        self.assertAlmostEqual(east, expected_east)
        self.assertAlmostEqual(north, expected_north)
        self.assertAlmostEqual(up, expected_up)

if __name__ == "__main__":
    unittest.main()
