from math import pi

CLIENT_VERSION = 0.3
USER_AGENT = "NTRIP JCMBsoftPythonClient/%.1f" % CLIENT_VERSION
SLEEP_TIME_FACTOR = 2  # How much the sleep time increases with each failed attempt
MAX_RECONNECTS = 1
MAX_RECONNECT_TIMEOUT = 1200
NTRIP_INTERVAL = 1  # So the first one is 1 second
PROPAGATION_INTERVAL = 0.1
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
INCLUDE_HOST_HEADER = False         # Include host header, should be on for IBSS
USE_SSL = False                     # Use SSL for the connection
CASTER_URL = "ntrip.kadaster.nl"    # URL of the caster
CASTER_PORT = 2101                  # Port of the caster
MOUNTPOINT = "BCEP00KAD0"           # Mount point to use
USE_NTRIP_V2 = False                # Make a NTRIP V2 Connection
VERBOSE = False                     # Connect in verbose mode
WRITE_HEADER = False                # Write header to stderr
