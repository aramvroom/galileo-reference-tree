#  Copyright (c) 2025, Aram Vroom.
#
#  This software is licensed under the MIT License.
#  For details, see the LICENSE file in the project root.
#
#  This software is licensed under the MIT License.
#  For details, see the LICENSE file in the project root.
#
#  This software is licensed under the MIT License.
#  For details, see the LICENSE file in the project root.
from dataclass_binder import Binder
from rpi_ws281x import PixelStrip, Color

from galileo_reference_tree.config import Config
from galileo_reference_tree.ledcontroller import strip_type_to_int

LED_HIGHLIGHT_INTERVAL = 10
LED_COLOR_HIGHLIGHT = [255, 255, 255]
LED_COLOR_A = [255, 0, 0]
LED_COLOR_B = [0, 255, 0]
LED_COLOR_C = [0, 0, 255]
LED_COLOR_RESET = [0, 0, 0]

def set_led_colors(led_strip, led_indices, color_rgb_array):
    color_object = Color(*color_rgb_array)
    for index in led_indices:
        led_strip.setPixelColor(index, color_object)
    strip.show()


if __name__ == '__main__':
    """
    This script can highlight every Nth LED and the configured orbital planes in order to aid with setting 
    up the Christmas tree. 
    
    Important Note: this file should be copied to the same directory as the main.py of the Galileo Reference Tree in
    order to function correctly.
    """

    # Read the configuration file
    config = Binder(Config).parse_toml("./config.toml")
    led_config = config.leds

    # Create the PixelStrip object
    strip = PixelStrip(led_config.general.led_count, led_config.general.gpio_pin,
                       led_config.general.led_freq_hz, led_config.general.dma_channel,
                       led_config.general.invert_signal, led_config.general.led_max_brightness,
                       led_config.general.channel, strip_type_to_int(led_config.general.led_strip_type))
    strip.begin()

    # Reset all LEDs at the start
    set_led_colors(strip, range(0, led_config.general.led_count), LED_COLOR_RESET)

    # Highlight every Nth LED
    print("Displaying LEDs with an interval of {}.".format(LED_HIGHLIGHT_INTERVAL))
    set_led_colors(strip, range(0, led_config.general.led_count, LED_HIGHLIGHT_INTERVAL), LED_COLOR_HIGHLIGHT)
    input("Press any key to continue to orbital plane highlight...")

    # Highlight orbital planes
    print("Highlighting orbital planes.")
    plane_color = Color(*LED_COLOR_A)
    set_led_colors(strip, config.leds.satellites.orbit_plane_a, LED_COLOR_A)
    set_led_colors(strip, config.leds.satellites.orbit_plane_b, LED_COLOR_B)
    set_led_colors(strip, config.leds.satellites.orbit_plane_c, LED_COLOR_C)
    input("Press any key to reset all LEDs...")

    # Reset all LEDs at the end
    set_led_colors(strip, range(0, led_config.general.led_count), LED_COLOR_RESET)
