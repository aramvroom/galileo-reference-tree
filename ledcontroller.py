import time

from rpi_ws281x import PixelStrip, Color
import constants
from itertools import cycle


def rotate_list(l, n):
    return l[n:] + l[:n]


class LedController(object):
    def __init__(self, max_sats, ephemeris, azelev):
        strip = PixelStrip(constants.LED_COUNT, constants.LED_PIN,
                           constants.LED_FREQ_HZ, constants.LED_DMA,
                           constants.LED_INVERT, constants.LED_MAX_BRIGHTNESS,
                           constants.LED_CHANNEL)
        strip.begin()
        self.ledstrip = strip
        self.max_sats = max_sats
        self.ephemeris = ephemeris
        self.azelev = azelev

    def get_led_idx(self, sat_idx):
        return sat_idx

    def get_brightness(self, sat_idx):
        elev = self.azelev[sat_idx][1]

        a = (constants.MAX_ELEV_BRIGHTNESS - constants.MIN_ELEV_BRIGHTNESS) / \
            (constants.MAX_ELEV_VALUE - constants.MIN_ELEV_VALUE)
        b = constants.MIN_ELEV_BRIGHTNESS

        brightness = a * elev + b
        if brightness < 0:
            brightness = 0
        return brightness

    def set_sat_led(self, sat_idx, signal_health):
        if not signal_health:
            ledColor = constants.COLOR_HEALTHY
        else:
            ledColor = constants.COLOR_UNHEALTHY

        brightness = self.get_brightness(sat_idx) / constants.LED_MAX_BRIGHTNESS
        ledColorWithElev = [round(i * brightness) for i in ledColor]
        color = Color(*ledColorWithElev)
        self.ledstrip.setPixelColor(self.get_led_idx(sat_idx), color)

    def show_plane(self, led_indices):
        mid_color = Color(255, 255, 255)
        early_late_color = Color(127, 127, 127)
        reset_color = Color(0, 0, 0)

        very_early_cycle_plane = cycle(led_indices)
        early_cycle_plane = cycle(rotate_list(led_indices, 1))
        prompt_cycle_plane = cycle(rotate_list(led_indices, 2))
        late_cycle_plane = cycle(rotate_list(led_indices, 3))
        very_late_cycle_plane = cycle(rotate_list(led_indices, 4))

        for prompt_led in prompt_cycle_plane:
            self.ledstrip.setPixelColor(next(very_early_cycle_plane) - 1, reset_color)
            self.ledstrip.setPixelColor(next(early_cycle_plane) - 1, early_late_color)
            self.ledstrip.setPixelColor(prompt_led - 1, mid_color)
            self.ledstrip.setPixelColor(next(late_cycle_plane) - 1, early_late_color)
            self.ledstrip.setPixelColor(next(very_late_cycle_plane) - 1, reset_color)
            time.sleep(1)

    def update_leds(self):
        while True:
            for satIdx in range(self.max_sats):
                if len(self.azelev[satIdx]) and self.azelev[satIdx][1] >= 0:
                    self.set_sat_led(satIdx, self.ephemeris[satIdx].signalHealth)
            self.ledstrip.show()
            time.sleep(constants.LED_UPDATE_INTERVAL)
