import itertools
import time
from itertools import cycle

from rpi_ws281x import PixelStrip, Color

from gnss_monitor.config import LEDs


def rotate_list(l, n):
    return l[n:] + l[:n]


class LedController(object):
    def __init__(self, max_sats, ephemeris, azelev, led_config: LEDs):
        strip = PixelStrip(led_config.general.led_count, led_config.general.gpio_pin,
                           led_config.general.led_freq_hz, led_config.general.dma_channel,
                           led_config.general.invert_signal, led_config.general.led_max_brightness,
                           led_config.general.channel, led_config.general.led_strip_type)
        strip.begin()
        self.ledstrip = strip
        self.max_sats = max_sats
        self.ephemeris = ephemeris
        self.azelev = azelev
        self.config = led_config

    def get_led_idx(self, sat_idx):
        return sat_idx

    def get_brightness(self, sat_idx):
        elev = self.azelev[sat_idx][1]

        a = (self.config.satellites.max_elev_brightness -  self.config.satellites.min_elev_brightness) / \
            (self.config.satellites.max_elev - self.config.satellites.min_elev)
        b = self.config.satellites.min_elev_brightness

        brightness = a * elev + b
        if brightness < 0:
            brightness = 0
        return brightness

    def set_sat_led(self, sat_idx, signal_health):
        if not signal_health:
            led_color = self.config.satellites.color_healthy
        else:
            led_color = self.config.satellites.color_unhealthy

        brightness = self.get_brightness(sat_idx) / self.config.general.led_max_brightness
        led_color_with_elev = [round(i * brightness) for i in led_color]
        color = Color(*led_color_with_elev)
        self.ledstrip.setPixelColor(self.get_led_idx(sat_idx), color)

    def show_plane(self, led_indices):
        mid_color = Color(*self.config.satellites.color_plane)
        color_with_brightness = [round(i * self.config.satellites.brightness_early_late_plane) for i in self.config.satellites.color_plane]
        early_late_color = Color(*color_with_brightness)
        reset_color = Color(0, 0, 0)

        very_early_cycle_plane = cycle(led_indices)
        early_cycle_plane = cycle(rotate_list(led_indices, 1))
        prompt_cycle_plane = cycle(rotate_list(led_indices, 2))
        late_cycle_plane = cycle(rotate_list(led_indices, 3))
        very_late_cycle_plane = cycle(rotate_list(led_indices, 4))

        for _ in itertools.count():
            self.ledstrip.setPixelColor(next(very_early_cycle_plane) - 1, reset_color)
            self.ledstrip.setPixelColor(next(early_cycle_plane) - 1, early_late_color)
            self.ledstrip.setPixelColor(next(prompt_cycle_plane) - 1, mid_color)
            self.ledstrip.setPixelColor(next(late_cycle_plane) - 1, early_late_color)
            self.ledstrip.setPixelColor(next(very_late_cycle_plane) - 1, reset_color)
            time.sleep(1)

    def update_leds(self):
        for _ in itertools.count():
            for satIdx in range(self.max_sats):
                if len(self.azelev[satIdx]) and self.azelev[satIdx][1] >= 0:
                    self.set_sat_led(satIdx, self.ephemeris[satIdx].signalHealth)
            self.ledstrip.show()
            time.sleep(self.config.general.update_interval)
