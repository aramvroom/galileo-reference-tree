import itertools
import time
from itertools import cycle

from rpi_ws281x import PixelStrip, Color

from gnss_monitor.config import LEDs


def strip_type_to_int(strip_type: str):
    """
    Converts a given strip type string to its corresponding integer value.

    This function maps a string representation of an LED strip type to its associated
    integer constant based on predefined mappings. The input string must match one
    of the keys in the predefined dictionary, otherwise it will result in a KeyError.

    Parameters:
        strip_type (str): The string representation of the LED strip type. Must match one of the keys in the strip_dictionary.

    Returns:
        int: The corresponding integer value of the supplied strip type.

    Raises:
        KeyError:
            If the provided strip_type does not exist in the strip_dictionary.
    """
    strip_dictionary = {"SK6812_STRIP_RGBW": 0x18100800,
                        "SK6812_STRIP_RBGW": 0x18100008,
                        "SK6812_STRIP_GRBW": 0x18081000,
                        "SK6812_STRIP_GBRW": 0x18080010,
                        "SK6812_STRIP_BRGW": 0x18001008,
                        "SK6812_STRIP_BGRW": 0x18000810,
                        "SK6812_SHIFT_WMASK": 0xf0000000,
                        "WS2811_STRIP_RGB": 0x00100800,
                        "WS2811_STRIP_RBG": 0x00100008,
                        "WS2811_STRIP_GRB": 0x00081000,
                        "WS2811_STRIP_GBR": 0x00080010,
                        "WS2811_STRIP_BRG": 0x00001008,
                        "WS2811_STRIP_BGR": 0x00000810,
                        "WS2812_STRIP": 0x00081000,
                        "SK6812_STRIP": 0x00081000,
                        "SK6812W_STRIP": 0x18081000}
    return strip_dictionary[strip_type]


def rotate_list(l, n):
    """
        Cyclically rotates the elements of a list left by a specified number of positions.

        Args:
            l (list): The list to be rotated.
            n (int): The number of positions to rotate the list left by.

        Returns:
            list: The resulting list after rotation by `n` positions.
    """
    return l[n:] + l[:n]


class LedController(object):
    """
    Controls and manages an LED strip for visualizing satellite tracking.

    This class provides methods to initialize and configure an LED strip for representing satellite information
    such as position, elevation, and signal health. It maps satellites to specific LEDs, adjusts LED brightness
    based on elevation, sets LED colors based on signal status, and animates patterns for representing satellite
    orbital planes. The class operates with an internal mapping of satellites to LEDs and supports real-time
    control of LED states.

    Attributes:
        max_sats (int): The maximum number of satellites supported.
        ephemeris (list[SatEphemeris]): Ephemeris data used for satellite information and signal health.
        azelev: Azimuth and elevation data for satellite tracking.
        config (LEDs): Configuration for LED properties and system settings.
        prn_to_led_map (dict): Maps satellite IDs to LED indices.
        ledstrip: The initialized LED strip object ready for control.
    """

    def __init__(self, max_sats, ephemeris, azelev, led_config: LEDs):
        """
        Initializes the LedController

        This constructor sets up the mapping of satellite IDs to LED indices, and initializes an LED strip with
        given configuration parameters to control the lighting.

        Parameters:
            max_sats: The maximum number of satellites supported by this configuration.
            ephemeris (list[SatEphemeris]): Satellite ephemerides
            azelev (list[list[float]): Azimuth and elevation data.
            led_config (LEDs config object): LED configuration details, including properties for mapping satellites and LED strip settings.

        Raises:
            None
        """
        self.max_sats = max_sats
        self.ephemeris = ephemeris
        self.azelev = azelev
        self.config = led_config

        # Create dictionary to map PRN to LED indices
        self.prn_to_led_map = {led_config.satellites.map_prns[i]: led_config.satellites.map_leds[i] for i in
                               range(len(led_config.satellites.map_prns))}

        # Create LED strip
        strip = PixelStrip(led_config.general.led_count, led_config.general.gpio_pin,
                           led_config.general.led_freq_hz, led_config.general.dma_channel,
                           led_config.general.invert_signal, led_config.general.led_max_brightness,
                           led_config.general.channel, strip_type_to_int(led_config.general.led_strip_type))
        strip.begin()
        self.ledstrip = strip

    def get_led_idx(self, sat_idx):
        """
        Determines the LED index corresponding to a given satellite index.

        The function maps a satellite index to an LED index using the configured mapping.
        If the mapping does not contain the satellite PRN, a default value of -1 is returned.

        Parameters:
            sat_idx (int): The index of the satellite for which the LED index
            is to be determined.

        Returns:
            int: The mapped LED index corresponding to the satellite index.
            If no mapping is found, returns -1.
        """
        sat_prn = sat_idx + 1
        try:
            led_idx = self.prn_to_led_map[sat_prn]
        except KeyError:
            led_idx = -1
        return led_idx

    def get_brightness(self, sat_idx):
        """
        Calculates the brightness level for a specific satellite based on its elevation.

        The computation uses a linear interpolation between the satellite's elevation angle and
        the brightness range defined in the configuration. If the computed brightness is
        negative, it is set to zero.

        Parameters:
            sat_idx (int): Index of the satellite for which to compute the brightness.

        Returns:
            float: Calculated brightness level for the given satellite.
        """
        elev = self.azelev[sat_idx][1]

        a = (self.config.satellites.max_elev_brightness - self.config.satellites.min_elev_brightness) / \
            (self.config.satellites.max_elev - self.config.satellites.min_elev)
        b = self.config.satellites.min_elev_brightness

        brightness = a * elev + b
        if brightness < 0:
            brightness = 0
        return brightness

    def set_sat_led(self, sat_idx, signal_health):
        """
        Sets the color of the satellite LED based on the elevation and signal health.

        The method evaluates the satellite's elevation against the minimum elevation
        threshold and assigns a LED color according to the signal health status if the
        satellite is considered visible. It also adjusts the brightness of the LED based
        on its computed brightness value and sets the LED color on the LED strip if the LED
        index is valid.

        Parameters:
            sat_idx (int): The index of the satellite whose LED is to be set.
            signal_health (int): The signal health status of the satellite. Acceptable
                values are 0 (healthy), -1 (unknown), and any other value representing
                unhealthy status.

        Raises:
            No explicit errors are raised by this method.
        """
        if self.azelev[sat_idx][1] < self.config.satellites.min_elev:
            led_color = [0, 0, 0]
        elif signal_health == 0:
            led_color = self.config.satellites.color_healthy
        elif signal_health == -1:
            led_color = self.config.satellites.color_unknown
        else:
            led_color = self.config.satellites.color_unhealthy

        brightness = self.get_brightness(sat_idx) / self.config.general.led_max_brightness
        led_color_with_elev = [round(i * brightness) for i in led_color]
        color = Color(*led_color_with_elev)
        led_idx = self.get_led_idx(sat_idx)
        # Catch the case where the LED index is not found
        if led_idx >= 0:
            self.ledstrip.setPixelColor(led_idx, color)

    def show_plane(self, led_indices):
        """
        Updates and controls the display of LED patterns representing an orbital plane
        on an LED strip. The method ensures that the LEDs specified for satellites are
        excluded from the operation and performs cyclic LED activation with a configured
        colors and brightness. The sequence and timing are controlled also based on configuration settings.

        Parameters:
            led_indices (list[int]): A list of indices corresponding to LEDs
                                     to be used for the plane effect.
        """
        # Only keep the LED indices which are not already satellites
        led_indices = [x for x in led_indices if x not in self.config.satellites.map_leds]

        mid_color = Color(*self.config.satellites.color_plane)
        color_with_brightness = [round(i * self.config.satellites.brightness_early_late_plane) for i in
                                 self.config.satellites.color_plane]
        early_late_color = Color(*color_with_brightness)
        reset_color = Color(0, 0, 0)

        very_early_cycle_plane = cycle(led_indices)
        early_cycle_plane = cycle(rotate_list(led_indices, 1))
        prompt_cycle_plane = cycle(rotate_list(led_indices, 2))
        late_cycle_plane = cycle(rotate_list(led_indices, 3))
        very_late_cycle_plane = cycle(rotate_list(led_indices, 4))

        for _ in itertools.count():
            self.ledstrip.setPixelColor(next(very_early_cycle_plane), reset_color)
            self.ledstrip.setPixelColor(next(early_cycle_plane), early_late_color)
            self.ledstrip.setPixelColor(next(prompt_cycle_plane), mid_color)
            self.ledstrip.setPixelColor(next(late_cycle_plane), early_late_color)
            self.ledstrip.setPixelColor(next(very_late_cycle_plane), reset_color)
            time.sleep(self.config.general.plane_interval)

    def update_leds(self):
        """
        Updates LED states for satellites based on their signal health status and displays the
        changes. This function iterates indefinitely, updating the LED strip at a fixed interval.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        for _ in itertools.count():
            for satIdx in range(self.max_sats):
                if len(self.azelev[satIdx]):
                    self.set_sat_led(satIdx, self.ephemeris[satIdx].signalHealth)
            self.ledstrip.show()
            time.sleep(self.config.general.update_interval)
