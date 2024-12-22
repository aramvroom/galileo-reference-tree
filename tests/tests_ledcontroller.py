#  Copyright (c) 2024, Aram Vroom.
#
#  This software is licensed under the MIT License.
#  For details, see the LICENSE file in the project root.

import unittest
from unittest.mock import patch

from galileo_reference_tree import constants
from galileo_reference_tree.ledcontroller import *
from galileo_reference_tree.satephemeris import SatEphemeris


def mocked_count():
    return [1, 2]


class TestLedController(unittest.TestCase):
    def test_strip_type_to_int(self):
        # Prepare
        strip_type = "SK6812_STRIP"
        expected_int = 0x00081000

        # Execute
        found_int = strip_type_to_int(strip_type)

        # Verify
        self.assertEqual(found_int, expected_int)

    def test_strip_type_to_int_error(self):
        # Execute
        with self.assertRaises(KeyError):
            strip_type_to_int(None)

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
        azelev = [[0] * 2] * 1  # Initialize azimuth and elevation for 1 satellite
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
        azelev = [[0] * 2] * 1  # Initialize azimuth and elevation for 1 satellite
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
        azelev = [[0] * 2] * 1  # Initialize azimuth and elevation for 1 satellite
        azelev[sat_idx][1] = 90
        ledcontroller = LedController(constants.MAX_SATS, [], azelev, LEDs)
        expected_color = LEDs.satellites.color_healthy

        # Execute
        ledcontroller.set_sat_led(sat_idx, signal_unhealthy)
        found_color_rgb = ledcontroller.ledstrip.getPixelColorRGB(ledcontroller.get_led_idx(sat_idx))

        # Verify
        self.assertEqual((found_color_rgb.r, found_color_rgb.g, found_color_rgb.b), expected_color)

    def test_set_sat_led_unhealthy(self):
        # Prepare
        signal_unhealthy = True
        sat_idx = 0
        azelev = [[0] * 2] * 1  # Initialize azimuth and elevation for 1 satellite
        azelev[sat_idx][1] = 90
        ledcontroller = LedController(constants.MAX_SATS, [], azelev, LEDs)
        expected_color = LEDs.satellites.color_unhealthy

        # Execute
        ledcontroller.set_sat_led(sat_idx, signal_unhealthy)
        found_color_rgb = ledcontroller.ledstrip.getPixelColorRGB(ledcontroller.get_led_idx(sat_idx))

        # Verify
        self.assertEqual((found_color_rgb.r, found_color_rgb.g, found_color_rgb.b), expected_color)

    def test_show_plane(self):
        # Prepare
        led_indices = (5, 6, 7, 8, 9)
        ledcontroller = LedController(constants.MAX_SATS, [], [], LEDs)
        early_late_color = tuple([round(i * LEDs.satellites.brightness_early_late_plane) for i in
                                  LEDs.satellites.color_plane])
        prompt_color = LEDs.satellites.color_plane

        expected_color_5 = (0, 0, 0)
        expected_color_6 = (0, 0, 0)
        expected_color_7 = early_late_color
        expected_color_8 = prompt_color
        expected_color_9 = early_late_color

        # Execute
        with patch("itertools.count", side_effect=mocked_count):
            ledcontroller.show_plane(led_indices)

        # Verify
        found_color_5 = ledcontroller.ledstrip.getPixelColorRGB(5)
        found_color_6 = ledcontroller.ledstrip.getPixelColorRGB(6)
        found_color_7 = ledcontroller.ledstrip.getPixelColorRGB(7)
        found_color_8 = ledcontroller.ledstrip.getPixelColorRGB(8)
        found_color_9 = ledcontroller.ledstrip.getPixelColorRGB(9)

        self.assertEqual((found_color_5.r, found_color_5.g, found_color_5.b), expected_color_5)
        self.assertEqual((found_color_6.r, found_color_6.g, found_color_6.b), expected_color_6)
        self.assertEqual((found_color_7.r, found_color_7.g, found_color_7.b), expected_color_7)
        self.assertEqual((found_color_8.r, found_color_8.g, found_color_8.b), expected_color_8)
        self.assertEqual((found_color_9.r, found_color_9.g, found_color_9.b), expected_color_9)

    def test_update_leds(self):
        # Prepare
        ephem = SatEphemeris
        ephem.signalHealth = 0
        azelev = [[0] * 2] * 1  # Initialize azimuth and elevation for 1 satellite
        azelev[0][1] = 90
        max_sats = 1
        expected_color = LEDs.satellites.color_healthy  # Brightness is max because 90 degree elevation

        ledcontroller = LedController(max_sats, [ephem], azelev, LEDs)

        # Execute
        with patch("itertools.count", side_effect=mocked_count):
            ledcontroller.update_leds()
            found_pixel_color = ledcontroller.ledstrip.getPixelColorRGB(0)

        # Verify
        self.assertEqual((found_pixel_color.r, found_pixel_color.g, found_pixel_color.b), expected_color)


if __name__ == '__main__':
    unittest.main()
