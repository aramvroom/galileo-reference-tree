from math import pi

CLIENT_VERSION = 0.3
USER_AGENT = "NTRIP JCMBsoftPythonClient/%.1f" % CLIENT_VERSION
SLEEP_TIME_FACTOR = 2  # How much the sleep time increases with each failed attempt
MAX_RECONNECTS = 1
MAX_RECONNECT_TIMEOUT = 1200
NTRIP_INTERVAL = 1  # So the first one is 1 second
PROPAGATION_INTERVAL = 0.2
PLOTTING_INTERVAL = 0.5

# Natural & WGS84 Constants
MU_EARTH = 3.986004418e14
ROT_RATE_EARTH = 7292115.0e-11
SEC_IN_WEEK = 24 * 3600 * 7
SPEED_OF_LIGHT = 2.99792458e8
WGS84_SEMI_MAJOR_AXIS = 6378137
WGS84_FIRST_ECCENTRICITY_SQUARED = 6.69437999014e-3
RAD_TO_DEG = 180 / pi
DEG_TO_RAD = pi / 180

DF_GALILEO_EPH = 1046

OWN_LAT_DEG = 52
OWN_LON_DEG = 4
OWN_ALT_M = 0
MAX_SATS = 36

# Caster settings
INCLUDE_HOST_HEADER = False  # Include host header, should be on for IBSS
USE_SSL = False  # Use SSL for the connection
CASTER_URL = "ntrip.kadaster.nl"  # URL of the caster
CASTER_PORT = 2101  # Port of the caster
MOUNTPOINT = "BCEP00KAD0"  # Mount point to use
USE_NTRIP_V2 = False  # Make a NTRIP V2 Connection
VERBOSE = False  # Connect in verbose mode
WRITE_HEADER = False  # Write header to stderr

# General LED strip configuration:
LED_COUNT = 45  # Number of LED pixels.
LED_PIN = 18  # GPIO pin connected to the pixels (18 uses PWM!).
# LED_PIN = 10        # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10  # DMA channel to use for generating signal (try 10)
LED_MAX_BRIGHTNESS = 255  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False  # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 0  # set to '1' for GPIOs 13, 19, 41, 45 or 53

# Satellite LED strip configuration
COLOR_HEALTHY = [0, 255, 0]
COLOR_UNHEALTHY = [255, 0, 0]

MIN_ELEV_VALUE = 0
MIN_ELEV_BRIGHTNESS = 100
MAX_ELEV_VALUE = 90
MAX_ELEV_BRIGHTNESS = 255
