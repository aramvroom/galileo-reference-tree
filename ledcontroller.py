import time

from rpi_ws281x import PixelStrip, Color
import constants


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

        min_idx = min(led_indices)
        max_idx = max(led_indices)
        num_in_range = max_idx - min_idx
        while True:
            for mid_idx, mid_led in enumerate(led_indices):
                self.ledstrip.setPixelColor(mid_led, mid_color)

                reset_led_idx = mid_led + 2
                if reset_led_idx >= max_idx:
                    reset_led_idx -= num_in_range
                self.ledstrip.setPixelColor(reset_led_idx, reset_color)

                reset_led_idx = mid_led - 2
                if reset_led_idx < min_idx:
                    reset_led_idx += num_in_range
                self.ledstrip.setPixelColor(reset_led_idx, reset_color)

                early_led_idx = mid_led + 1
                if early_led_idx > max_idx:
                    early_led_idx -= num_in_range
                self.ledstrip.setPixelColor(early_led_idx, early_late_color)

                late_led_idx = mid_led - 1
                if late_led_idx < min_idx:
                    late_led_idx += num_in_range
                self.ledstrip.setPixelColor(late_led_idx, early_late_color)
                time.sleep(1)

    def theaterChase(self, color, wait_ms=50, iterations=10):
        """Movie theater light style chaser animation."""
        for j in range(iterations):
            for q in range(3):
                for i in range(0, self.ledstrip.numPixels(), 3):
                    self.ledstrip.setPixelColor(i + q, color)
                self.ledstrip.show()
                time.sleep(wait_ms / 1000.0)
                for i in range(0, self.ledstrip.numPixels(), 3):
                    self.ledstrip.setPixelColor(i + q, 0)

    def update_leds(self):
        while True:
            for satIdx in range(self.max_sats):
                if len(self.azelev[satIdx]) and self.azelev[satIdx][1] >= 0:
                    self.set_sat_led(satIdx, self.ephemeris[satIdx].signalHealth)
            self.ledstrip.show()
            time.sleep(constants.LED_UPDATE_INTERVAL)
