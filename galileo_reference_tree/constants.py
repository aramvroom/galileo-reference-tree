#  Copyright (c) 2024, Aram Vroom.
#
#  This software is licensed under the MIT License.
#  For details, see the LICENSE file in the project root.

from math import pi

# Loop intervals
PROPAGATION_INTERVAL = 0.1  # Update interval in seconds for the satellite coordinates
PLOTTING_INTERVAL = 0.1  # Update interval in seconds for the skyplot and LED plot

# Natural & WGS84 Constants
MU_EARTH = 3.986004418e14  # Standard gravitational parameter in m^3/s^2
ROT_RATE_EARTH = 7292115.0e-11  # Rotation rate in radians
SEC_IN_HOUR = 3600  # Number of seconds in an hour
HOURS_IN_DAY = 24  # Number of hours in a day
DAYS_IN_WEEK = 7  # Number of days in a week
SEC_IN_WEEK = DAYS_IN_WEEK * HOURS_IN_DAY * SEC_IN_HOUR  # Number of seconds in a week
SPEED_OF_LIGHT = 2.99792458e8  # Speed of light in m/s
WGS84_SEMI_MAJOR_AXIS = 6378137  # Semi-major axis of the WGS84 ellipsoid
WGS84_FIRST_ECCENTRICITY_SQUARED = 6.69437999014e-3  # First eccentricity squared of the WGS84 ellipsoid
RAD_TO_DEG = 180 / pi  # Radians to degrees
DEG_TO_RAD = pi / 180  # Degrees to radians

# Constellation constants
DF_GALILEO_EPH = 1046  # RTCM message number for Galileo Ephemeris data
MAX_SATS = 36  # Maximum number of satellites to mode
GPS_WEEKS_ROLLOVER = 1024  # Number of weeks before a GPS rollover
TLE_MAX_AGE = 10  # Maximum data age in days at which to check for new TLE data
