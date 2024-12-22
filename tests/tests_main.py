#  Copyright (c) 2024, Aram Vroom.
#
#  This software is licensed under the MIT License.
#  For details, see the LICENSE file in the project root.

import datetime
import unittest
from unittest.mock import patch, MagicMock

from galileo_reference_tree import constants
from galileo_reference_tree.config import Location
from main import getCurrentToW, propagate_all


class TestMainFunctions(unittest.TestCase):
    def test_getCurrentToW(self):
        # Prepare
        fixed_utc_now = datetime.datetime(2024, 12, 7, 0, 0, 0, tzinfo=datetime.timezone.utc)
        expected_wn = 2343
        expected_tow = 6 * constants.SEC_IN_HOUR * constants.HOURS_IN_DAY + 18  # Plus the number of current leap seconds

        # Execute
        with patch('main.get_utc_now', return_value=fixed_utc_now):
            found_wn, found_tow = getCurrentToW()

        # Verify
        self.assertEqual(found_wn, expected_wn)
        self.assertEqual(found_tow, expected_tow)

    @patch('main.constants.MAX_SATS', 5)
    @patch('main.constants.PROPAGATION_INTERVAL', 0.01)
    @patch('main.getCurrentToW')
    @patch('main.ecef2aer')
    def test_propagate_all(self, mock_ecef2aer, mock_getCurrentToW):
        # Prepare
        mock_getCurrentToW.return_value = (2000, 432000)
        mock_ecef2aer.side_effect = lambda x, y, z, lat, lon, alt: (x + 1, y + 2, z + 3)

        simulation_speed = 2
        all_ephem = [MagicMock() for _ in range(5)]
        for i, eph in enumerate(all_ephem):
            eph.toe = (i % 2 == 0)
            eph.propagate.side_effect = lambda wn, tow: (wn + 10, tow + 20, 30)

        all_azelev = [[0, 0] for _ in range(5)]
        location = Location(latitude_deg=50.0, longitude_deg=8.0, altitude_m=200.0)

        # Execute and verify (run only one loop using time.sleep mock)
        with patch('main.time.sleep', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                propagate_all(all_ephem, all_azelev, location, simulation_speed)

        for i, eph in enumerate(all_ephem):
            if eph.toe:
                eph.propagate.assert_called_once_with(2000, 432000)

if __name__ == '__main__':
    unittest.main()
