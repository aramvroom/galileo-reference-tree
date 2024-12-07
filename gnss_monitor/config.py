from dataclasses import dataclass
from typing import List

# Location to compute the visibilities at
@dataclass
class Location:
    latitude_deg: float
    longitude_deg: float
    altitude_m: float


# Settings related to the NTRIP Client and Caster
@dataclass
class Ntrip:
    software_version: float         # Version of this software to identify with
    software_name: str              # Name of this software to identify with
    address: str                    # URL of the caster
    port: int                       # Port of the caster
    mountpoint: str                 # Mount point to use
    use_ssl: bool                   # Use SSL for the connection
    ntrip_v2: bool                  # Make a NTRIP V2 Connection
    include_host_header: bool       # Include host header, should be on for IBSS
    username_password: str          # The username and password to connect with


# General settings related to the LED strip
@dataclass
class GeneralLEDSettings:
    led_count: int                  # Number of LED pixels
    gpio_pin: int                   # GPIO pin connected to the pixels (18 uses PWM, 10 uses SPI /dev/spidev0.0).
    led_freq_hz: float              # LED signal frequency in hertz (usually 800kHz)
    dma_channel: int                # DMA channel to use for generating signal (try 10)
    led_max_brightness: int         # Set to 0 for darkest and 255 for brightest
    invert_signal: bool             # True to invert the signal (when using NPN transistor level shift)
    channel: int                    # set to '1' for GPIOs 13, 19, 41, 45 or 53
    led_strip_type: str             # The type of LED strip, see https://github.com/HarmvZ/rpi_ws281x_mock/blob/master/rpi_ws281x/rpi_ws281x_mock.py#L128
    update_interval: int            # Update interval of the LEDs in seconds


# Settings for the LEDs related to the satellites
@dataclass
class SatellitesLEDSettings:
    color_healthy: List[int]        # [R,G,B] color to use for healthy satellites
    color_unhealthy: List[int]      # [R,G,B] color to use for unhealthy satellites
    min_elev: float                 # Minimum elevation
    min_elev_brightness: int        # Brightness corresponding to the minimum elevation
    max_elev: float                 # Maximum elevation
    max_elev_brightness: int        # Brightness corresponding to the maximum elevation
    orbit_plane_a: List[int]        # LED numbers corresponding to orbital plane A
    orbit_plane_b: List[int]        # LED numbers corresponding to orbital plane B
    orbit_plane_c: List[int]        # LED numbers corresponding to orbital plane C


# Settings related to the LED strip
@dataclass
class LEDs:
    general: GeneralLEDSettings         # General settings related to the LED strip
    satellites: SatellitesLEDSettings   # Settings for the LEDs related to the satellites


# Class containing the complete configuration
@dataclass
class Config:
    location: Location              # The location to compute the visibilities for
    ntrip: Ntrip                    # Settings related to the NTRIP Client and Caster
    leds: LEDs                      # Settings related to the LED strip
    verbose: bool                   # Run verbosely
