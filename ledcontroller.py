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

        brightness = a*elev + b
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

    def update_leds(self):
        for satIdx in range(self.max_sats):
            if len(self.azelev[satIdx]) and self.azelev[satIdx][1] >= 0:
                self.set_sat_led(satIdx, self.ephemeris[satIdx].signalHealth)
            self.ledstrip.show()
