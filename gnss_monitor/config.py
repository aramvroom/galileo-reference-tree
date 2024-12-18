from dataclasses import dataclass
from typing import List

# Location to compute the visibilities at
@dataclass
class Location:
    latitude_deg: float     = 0.0       # Latitude in degrees
    longitude_deg: float    = 0.0       # Longitude in degrees
    altitude_m: float       = 0.0       # Altitude in meters


# Settings related to the NTRIP Client and Caster
@dataclass
class Ntrip:
    software_version: float = 0.3               # Version of this software to identify with
    software_name: str      = 'gnss_monitor'    # Name of this software to identify with
    address: str            = '127.0.0.1'       # URL of the caster
    port: int               = 2101              # Port of the caster
    mountpoint: str         = 'SOURCETABLE'     # Mount point to use
    use_ssl: bool           = False             # Use SSL for the connection
    ntrip_v2: bool          = False             # Make a NTRIP V2 Connection
    include_host_header: bool   = False         # Include host header, should be on for IBSS
    username_password: str      = 'anonymous:password'  # The username and password to connect with


# General settings related to the LED strip
@dataclass
class GeneralLEDSettings:
    led_count: int      = 100           # Number of LED pixels
    gpio_pin: int       = 18            # GPIO pin connected to the pixels (18 uses PWM, 10 uses SPI /dev/spidev0.0).
    led_freq_hz: int    = 800000        # LED signal frequency in hertz (usually 800kHz)
    dma_channel: int    = 10            # DMA channel to use for generating signal (try 10)
    led_max_brightness: int = 255       # Set to 0 for darkest and 255 for brightest
    invert_signal: bool     = False     # True to invert the signal (when using NPN transistor level shift)
    channel: int            = 0         # set to '1' for GPIOs 13, 19, 41, 45 or 53
    led_strip_type: str     = "WS2811_STRIP_RGB"    # The type of LED strip, see https://github.com/HarmvZ/rpi_ws281x_mock/blob/master/rpi_ws281x/rpi_ws281x_mock.py#L128
    update_interval: float    = 1.0         # Update interval of the LEDs in seconds


# Settings for the LEDs related to the satellites
@dataclass
class SatellitesLEDSettings:
    color_healthy: List[int]    = (0, 255, 0)               # [R,G,B] color to use for healthy satellites
    color_unhealthy: List[int]  = (255, 0, 0)               # [R,G,B] color to use for unhealthy satellites
    color_unknown: List[int]    = (255, 165, 0)               # [R,G,B] color to use for satellites with unknown health status
    color_plane: List[int]      = (255, 255, 255)           # [R,G,B] color to use to display the orbital plane
    brightness_early_late_plane: float = 0.5                # Brightness for the early and late LEDs in the orbital plane animation
    min_elev: float             = 0                         # Minimum elevation
    min_elev_brightness: int    = 127                       # Brightness corresponding to the minimum elevation
    max_elev: float             = 90                        # Maximum elevation
    max_elev_brightness: int    = 255                       # Brightness corresponding to the maximum elevation
    orbit_plane_a: List[int]    = (41, 42, 43, 44, 45)      # LED numbers corresponding to orbital plane A
    orbit_plane_b: List[int]    = (51, 52, 53, 54, 55)      # LED numbers corresponding to orbital plane B
    orbit_plane_c: List[int]    = (61, 62, 63, 64, 65)      # LED numbers corresponding to orbital plane C
    map_prns: List[int]         = (1, 2, 3)
    map_leds: List[int]         = (0, 1, 2)


# Settings related to the LED strip
@dataclass
class LEDs:
    general: GeneralLEDSettings         = GeneralLEDSettings      # General settings related to the LED strip
    satellites: SatellitesLEDSettings   = SatellitesLEDSettings   # Settings for the LEDs related to the satellites


# Class containing the complete configuration
@dataclass
class Config:
    location: Location  = Location     # The location to compute the visibilities for
    ntrip: Ntrip        = Ntrip        # Settings related to the NTRIP Client and Caster
    leds: LEDs          = LEDs         # Settings related to the LED strip
    verbose: bool   = False            # Run verbosely
    simulation_speed: int = 1          # Simulation speed (1 = realtime)
