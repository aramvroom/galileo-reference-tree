import datetime
import unittest
from unittest.mock import patch

from gnss_monitor import constants
from main import getCurrentToW


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


if __name__ == '__main__':
    unittest.main()
