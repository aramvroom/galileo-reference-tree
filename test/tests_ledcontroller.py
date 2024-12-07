import unittest

from gnss_monitor.ledcontroller import *
from gnss_monitor import constants
from gnss_monitor.config import LEDs

class TestLedController(unittest.TestCase):

    def test_rotate_list_left(self):
        # Prepare
        list_before = [1, 2, 3]
        rotate_amount = 1
        expected_list_after = [2, 3, 1]

        # Execute
        found_list = (rotate_list(list_before, rotate_amount))

        # Verify
        self.assertEqual(found_list, expected_list_after)


    def test_rotate_list_right(self):
        # Prepare
        list_before = [1, 2, 3]
        rotate_amount = -1
        expected_list_after = [3, 1, 2]

        # Execute
        found_list = (rotate_list(list_before, rotate_amount))

        # Verify
        self.assertEqual(found_list, expected_list_after)


    def test_get_led_idx(self):
        # Prepare
        ledcontroller = LedController(constants.MAX_SATS, [], [], LEDs)
        sat_idx = 1
        expected_led_idx = 1

        # Execute
        found_idx = ledcontroller.get_led_idx(sat_idx)

        # Verify
        self.assertEqual(found_idx, expected_led_idx)

    def test_get_brightness(self):
        # Prepare
        n_sats = 1
        n_vars = 2 # Azimuth and elevation
        azelev =  [[0]*n_vars]*n_sats
        azelev[0][1] = 45
        ledcontroller = LedController(constants.MAX_SATS, [], azelev, LEDs)
        expected_brightness = 191

        # Execute
        found_brightness = ledcontroller.get_brightness(0)

        # Verify
        self.assertEqual(found_brightness, expected_brightness)

    def test_get_brightness_negative(self):
        # Prepare
        config = LEDs
        config.satellites.min_elev_brightness = 0
        n_sats = 1
        n_vars = 2 # Azimuth and elevation
        azelev =  [[0]*n_vars]*n_sats
        azelev[0][1] = -45
        ledcontroller = LedController(constants.MAX_SATS, [], azelev, config)
        expected_brightness = 0

        # Execute
        found_brightness = ledcontroller.get_brightness(0)

        # Verify
        self.assertEqual(found_brightness, expected_brightness)

if __name__ == '__main__':
    unittest.main()
