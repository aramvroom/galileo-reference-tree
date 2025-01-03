#  Copyright (c) 2024, Aram Vroom.
#
#  This software is licensed under the MIT License.
#  For details, see the LICENSE file in the project root.

import datetime
from math import pi, sqrt, sin, cos, floor, ceil, atan2

from astropy.coordinates import GCRS, CartesianRepresentation, ITRS
from astropy.time import Time
from skyfield.api import load
from skyfield.sgp4lib import EarthSatellite

from galileo_reference_tree import constants


def correct_wn_for_rollover(wn):
    """
    Corrects a week number for rollovers caused by the limited range of the GPS WN field.

    This function adjusts the given week number such that it is within the nearest rollover of the current week number

    Parameters:
        wn (int): The input week number that needs to be corrected.

    Returns:
        int: The corrected GPS week number accounting for any rollovers.
    """
    # Get current week number
    gps_time_now = Time(datetime.datetime.now(datetime.UTC), format='datetime').to_value('gps')
    wn_now = floor(gps_time_now / constants.SEC_IN_WEEK)

    # Compute the number of rollovers between the input WN and the current WN
    rollovers = (wn_now - wn) / constants.GPS_WEEKS_ROLLOVER

    # Round towards zero
    if rollovers >= 0:
        rollovers = floor(rollovers)
    else:
        rollovers = ceil(rollovers)

    # Update WN
    wn_corrected = wn + rollovers * constants.GPS_WEEKS_ROLLOVER

    return wn_corrected


class SatEphemeris(object):
    """
    Represents satellite ephemeris data, storing necessary orbital and clock parameters for
    position and velocity propagation.

    The SatEphemeris class encapsulates satellite orbital data and methods for propagating satellite
    positions using ephemeris or Two-Line Element (TLE) sets.

    Attributes:
        gst (int): GPS system time in seconds.
        prn (int): Satellite identifier
        signalHealth (int): Signal health status; defaults to -1 for unknown.
        dataValidity (int): Data validity flag.
        wn (int): GPS week number.
        iodNav (int): Issue of Data
        iDot (float): Rate of change of inclination in radians/second.
        toc (int): Time of clock, expressed in seconds.
        af2 (float): Clock drift rate.
        af1 (float): Clock drift.
        af0 (float): Clock bias.
        crs (float): Sine harmonic correction to orbital radius.
        deltaN (float): Mean motion difference in radians/second.
        m0 (float): Mean anomaly at reference time in radians.
        cuc (float): Cosine harmonic correction to argument of latitude.
        ecc (float): Eccentricity.
        cus (float): Sine harmonic correction to argument of latitude.
        a (float): Semi-major axis.
        toe (int): Time of ephemeris, expressed in seconds.
        cic (float): Cosine harmonic correction to angle of inclination.
        Omega0 (float): Longitude of ascending node of orbit plane in radians.
        cis (float): Sine harmonic correction to angle of inclination.
        i0 (float): Inclination at reference time in radians.
        crc (float): Cosine harmonic correction to orbital radius.
        omega (float): Argument of perigee in radians.
        OmegaDot (float): Rate of change of right ascension of ascending node in radians/second.
        tle (EarthSatellite): A Two-Line Element set representing the satellite.
    """

    def __init__(self):
        """
        Initialization method for the SatEphemeris class
        """
        self.gst = 0
        self.prn = 0
        self.signalHealth = -1  # Unknown signal health
        self.dataValidity = 0
        self.wn = 0
        self.iodNav = 0
        self.iDot = 0
        self.toc = 0
        self.af2 = 0
        self.af1 = 0
        self.af0 = 0
        self.crs = 0
        self.deltaN = 0
        self.m0 = 0
        self.cuc = 0
        self.ecc = 0
        self.cus = 0
        self.a = 0
        self.toe = 0
        self.cic = 0
        self.Omega0 = 0
        self.cis = 0
        self.i0 = 0
        self.crc = 0
        self.omega = 0
        self.OmegaDot = 0
        self.tle: EarthSatellite = None

    def map_to_ephemeris(self, rtcm):
        """
        Maps the provided RTCM object to ephemeris parameters by extracting and transforming
        data fields. It processes various orbital and clock correction parameters, as well as
        signal health and data validity.

        Parameters:
            rtcm (RTCM): An RTCM object containing fields required for ephemeris mapping.
        """
        self.gst = rtcm.DF289 * constants.SEC_IN_WEEK + rtcm.DF293
        self.prn = rtcm.DF252
        self.signalHealth = rtcm.DF287
        self.dataValidity = rtcm.DF288
        self.wn = correct_wn_for_rollover(rtcm.DF289)
        self.iodNav = rtcm.DF290
        self.iDot = rtcm.DF292 * pi
        self.toc = rtcm.DF293
        self.af2 = rtcm.DF294
        self.af1 = rtcm.DF295
        self.af0 = rtcm.DF296
        self.crs = rtcm.DF297
        self.deltaN = rtcm.DF298 * pi
        self.m0 = rtcm.DF299 * pi
        self.cuc = rtcm.DF300
        self.ecc = rtcm.DF301
        self.cus = rtcm.DF302
        self.a = rtcm.DF303 * rtcm.DF303
        self.toe = rtcm.DF304
        self.cic = rtcm.DF305
        self.Omega0 = rtcm.DF306 * pi
        self.cis = rtcm.DF307
        self.i0 = rtcm.DF308 * pi
        self.crc = rtcm.DF309
        self.omega = rtcm.DF310 * pi
        self.OmegaDot = rtcm.DF311 * pi

    def propagate(self, wn, tow):
        """
        Propagates the satellite's position and velocity based on available navigation data.

        This method determines the correct propagation approach based on whether the
        satellite has Two-Line Element (TLE) data or ephemeris data. If TLE data exists
        and no ephemeris is available, it uses TLE propagation. Otherwise, if ephemeris data is
        available, it propagates using ephemeris. If neither data is present, a runtime
        exception is raised.

        Parameters:
            wn (int): GPS week number to propagate to
            tow (float): Time of week in seconds to propagate to

        Returns:
            tuple[float, float, float]: The (x, y, z) position of the satellite in ECEF coordinates,
                given in meters.

        Raises:
            RuntimeError: Raised when no data (TLE or ephemeris) is available for propagation.
        """
        if self.wn == 0 and self.tle is not None:
            return self.propagate_tle(wn, tow)
        elif self.wn > 0:
            return self.propagate_ephemeris(tow)
        else:
            raise RuntimeError("Attempted to propagate satellite without ephemeris or TLE")

    def propagate_tle(self, wn, tow):
        """
        Propagates a TLE (Two-Line Element set) for a satellite to compute its position in ECEF
        (Earth-Centered Earth-Fixed) coordinates.

        This function takes a GPS week number and time of week to determine the satellite's position
        at the specified time by propagating its TLE. The position is returned in the ECEF coordinate
        frame, expressed in meters.

        Parameters:
            wn (int): GPS week number.
            tow (float): Time of week in seconds.

        Returns:
            tuple[float, float, float]: The (x, y, z) position of the satellite in ECEF coordinates,
                given in meters.
        """
        # Initialize timescale object
        ts = load.timescale()

        # Create astropy time
        astropy_time = Time(wn * constants.SEC_IN_WEEK + tow, format='gps')

        time = ts.from_astropy(astropy_time)

        # Get satellite position in ECI (GCRS in Skyfield terminology)
        geocentric = self.tle.at(time)
        x_eci, y_eci, z_eci = geocentric.position.m

        # Create a GCRS (ECI) representation in Astropy
        gcrs = GCRS(
            CartesianRepresentation(x_eci, y_eci, z_eci, unit="m"),
            obstime=astropy_time,
        )

        # Transform from GCRS (ECI) to ITRS (ECEF)
        itrs = gcrs.transform_to(ITRS(obstime=astropy_time))

        # Extract ECEF coordinates
        x_ecef = itrs.x.to("m").value
        y_ecef = itrs.y.to("m").value
        z_ecef = itrs.z.to("m").value

        return x_ecef, y_ecef, z_ecef

    def propagate_ephemeris(self, tow):
        """
        Propagates the orbital ephemeris to compute the satellite's position in the ECEF frame at a given time.

        This method calculates the position of a satellite in the Earth-Centered, Earth-Fixed (ECEF) coordinate
        system at a specified time of week (TOW) based on its ephemeris parameters. Source:
        Subirana, J., Hernandez-Pajares, M., Zornoza, J., European Space Agency, & Fletcher, K. (2013).
        GNSS Data Processing Volume 1. ESA Communications.

        Parameters:
            tow (float): Time of week (TOW) in seconds for which the satellite's position is to be computed.

        Returns:
            tuple[float, float, float]: The computed ECEF coordinates (x, y, z) of the satellite in meters.
        """
        # Time from the ephemerides reference epoch
        tk = tow - self.toe

        # Update time difference in case of week rollover
        if tk > constants.SEC_IN_WEEK / 2:
            tk -= constants.SEC_IN_WEEK
        elif tk < -constants.SEC_IN_WEEK / 2:
            tk += constants.SEC_IN_WEEK

        # Compute mean anomaly
        Mk = self.m0 + (sqrt(constants.MU_EARTH) / sqrt(self.a ** 3) + self.deltaN) * tk

        # Compute the eccentric anomaly
        Ek = self.getEccentricAnomaly(Mk)

        # Compute the true anomaly
        vk = atan2(sqrt(1 - self.ecc ** 2) * sin(Ek), (cos(Ek) - self.ecc))

        # Compute argument of latitude from the argument of perigee, true anomaly and the corrections
        uk = self.omega + vk + self.cuc * cos(2 * (self.omega + vk)) + self.cus * sin(2 * (self.omega + vk))

        # Compute radial distance, considering corrections
        rk = self.a * (1 - self.ecc * cos(Ek)) + self.crc * cos(2 * (self.omega + vk)) + self.crs * sin(
            2 * (self.omega + vk))

        # Compute inclinations from the inclination at the reference time and the corrections
        ik = self.i0 + self.iDot * tk + self.cic * cos(2 * (self.omega + vk)) + self.cis * sin(2 * (self.omega + vk))

        # Compute longitude of the ascending node w.r.t Greenwich
        Omega = self.Omega0 + (self.OmegaDot - constants.ROT_RATE_EARTH) * tk - constants.ROT_RATE_EARTH * self.toe

        # Transform to ECEF coordinates
        x = rk * cos(uk) * cos(Omega) - rk * sin(uk) * cos(ik) * sin(Omega)
        y = rk * cos(uk) * sin(Omega) + rk * sin(uk) * cos(ik) * cos(Omega)
        z = rk * sin(uk) * sin(ik)

        return x, y, z

    def getEccentricAnomaly(self, mean_anomaly):
        """
        Calculate the eccentric anomaly for a given mean anomaly

        Parameters:
            mean_anomaly (float): The mean anomaly, expressed in radians, for which
            the eccentric anomaly will be calculated.

        Returns:
            float: The calculated eccentric anomaly corresponding to the given mean
            anomaly.
        """
        eccentric_anomaly = mean_anomaly  # Initial guess
        for _ in range(20):  # Iterate to solve eccentric anomaly numerically
            eccentric_anomaly = mean_anomaly + self.ecc * sin(eccentric_anomaly)
        return eccentric_anomaly
