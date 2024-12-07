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
        azelev = [[0]*2]*1  # Initialize azimuth and elevation for 1 satellite
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
        azelev = [[0]*2]*1  # Initialize azimuth and elevation for 1 satellite
        azelev[0][1] = -45
        ledcontroller = LedController(constants.MAX_SATS, [], azelev, config)
        expected_brightness = 0

        # Execute
        found_brightness = ledcontroller.get_brightness(0)

        # Verify
        self.assertEqual(found_brightness, expected_brightness)

    def test_set_sat_led_healthy(self):
        # Prepare
        signal_unhealthy = False
        sat_idx = 0
        azelev = [[0]*2]*1  # Initialize azimuth and elevation for 1 satellite
        azelev[sat_idx][1] = 90
        ledcontroller = LedController(constants.MAX_SATS, [], azelev, LEDs)
        expected_color = LEDs.satellites.color_healthy

        # Execute
        ledcontroller.set_sat_led(sat_idx,signal_unhealthy)
        found_color_rgb = ledcontroller.ledstrip.getPixelColorRGB(ledcontroller.get_led_idx(sat_idx))

        # Verify
        self.assertEqual((found_color_rgb.r, found_color_rgb.g, found_color_rgb.b), expected_color)

    def test_set_sat_led_unhealthy(self):
        # Prepare
        signal_unhealthy = True
        sat_idx = 0
        azelev = [[0]*2]*1  # Initialize azimuth and elevation for 1 satellite
        azelev[sat_idx][1] = 90
        ledcontroller = LedController(constants.MAX_SATS, [], azelev, LEDs)
        expected_color = LEDs.satellites.color_unhealthy

        # Execute
        ledcontroller.set_sat_led(sat_idx,signal_unhealthy)
        found_color_rgb = ledcontroller.ledstrip.getPixelColorRGB(ledcontroller.get_led_idx(sat_idx))

        # Verify
        self.assertEqual((found_color_rgb.r, found_color_rgb.g, found_color_rgb.b), expected_color)


if __name__ == '__main__':
    unittest.main()
