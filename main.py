# !/usr/bin/env -S python3 -u

import datetime
import threading
import time
from math import floor

from astropy.time import Time
from dataclass_binder import Binder

from gnss_monitor import constants
from gnss_monitor.config import Config, Location
from gnss_monitor.ntripclient import NtripClient
from gnss_monitor.plotleds import LedPlot
from gnss_monitor.satephemeris import SatEphemeris
from gnss_monitor.skyplot import SkyPlot
from gnss_monitor.transform import lla2ecef, ecef2aer
from gnss_monitor.ledcontroller import LedController
from gnss_monitor.twolineelements import TwoLineElements

TIME_START = datetime.datetime.now(datetime.UTC)

def propagate_all(all_ephem, all_azelev, location: Location, simulation_speed=1, verbose=False):
    """
    Continuously propagates ephemeris data and computes the satellites' azimuth and
    elevation as observed from a specific location. The propagation is performed in a loop
    for a predefined number of satellites, and the results are updated in the specified
    all_ephem and azimuth-elevation output arrays.

    Parameters:
        all_ephem: List
            A list of ephemeris data objects for satellites. Assumes a fixed length as defined
            by constants.MAX_SATS.
        all_azelev: List[List[float]]
            A mutable list to store the resulting azimuth, elevation pairs for each satellite.
        location: Location
            A Location object which contains latitude, longitude, and altitude in degrees and
            meters respectively.
        simulation_speed: int, optional
            Speed-up factor for the simulation's time progression. Default is 1.
        verbose: bool, optional
            If True, additional information about each satellite's azimuth, elevation, and
            range is printed to the console. Default is False.

    Returns:
        None

    Raises:
        No exceptions explicitly raised by this method.
    """
    # Start continuous loop
    while True:
        # Loop over all the ephemeris
        for idx in range(constants.MAX_SATS):
            eph = all_ephem[idx]

            # If it has a Time of Ephemeris, it can be propagated
            if eph.toe or eph.tle is not None:
                wn, tow = getCurrentToW(simulation_speed)
                x, y, z = eph.propagate(wn, tow)

                # Convert to azimuth, elevation and range
                az, elev, r = ecef2aer(x, y, z, location.latitude_deg, location.longitude_deg,
                                           location.altitude_m)
                all_azelev[idx] = [az, elev]
                if verbose:
                    print('Sat', eph.prn, 'az', az, 'elev', elev, 'r', r)
        time.sleep(constants.PROPAGATION_INTERVAL)


def get_utc_now():
    """
    This function retrieves the current date and time in UTC. It exists in order to allow mocking

    Returns
    -------
    datetime.datetime
        Current date and time in UTC format.
    """
    return datetime.datetime.now(datetime.UTC)


def getCurrentToW(simulation_speed = 1):
    """
        Calculates the current GPS Week Number (WN) and Time of Week (ToW) based on
        the simulation speed and the current system UTC time. This utilizes a
        predefined start time `TIME_START` and converts the time to GPS format
        for further computations.

        Parameters:
            simulation_speed (int | float): The speed multiplier to simulate GPS
                                            time, where 1 represents real-time.

        Returns:
            tuple: A tuple containing:
                   - gps_wn (int): The current GPS Week Number.
                   - gps_tow (float): The current Time of Week in seconds.
    """
    current_time = (get_utc_now() - TIME_START) * simulation_speed + TIME_START
    gps_time_now = Time(current_time, format='datetime').to_value('gps')
    gps_tow = gps_time_now % constants.SEC_IN_WEEK
    gps_wn = floor(gps_time_now / constants.SEC_IN_WEEK)
    return gps_wn, gps_tow


if __name__ == '__main__':
    outputFile = ''
    headerFile = False

    # Read the configuration file
    config = Binder(Config).parse_toml("./config.toml")

    # Create data structures for the ephemeris and azimuth + elevation
    ephemeris = []
    for satIdx in range(constants.MAX_SATS):
        ephemeris.append(SatEphemeris())
    azelev = [[] for _ in range(constants.MAX_SATS)]

    running_threads = []
    try:
        # Get the TLE
        tle = TwoLineElements()
        tle.set_tle(ephemeris)

        # Create RTCM retrieval loop
        client = NtripClient(ephemeris, azelev, config.ntrip)
        running_threads.append(threading.Thread(target=client.get_ephemeris_loop))

        # Create propagation loop
        running_threads.append(threading.Thread(target=propagate_all, args=[ephemeris, azelev, config.location, config.simulation_speed, config.verbose]))

        # Create LED update loop for satellites
        ledController = LedController(constants.MAX_SATS, ephemeris, azelev, config.leds)
        running_threads.append(threading.Thread(target=ledController.update_leds))

        # Create LED update loop for orbital planes
        running_threads.append(threading.Thread(target=ledController.show_plane, args=[config.leds.satellites.orbit_plane_a]))
        running_threads.append(threading.Thread(target=ledController.show_plane, args=[config.leds.satellites.orbit_plane_b]))
        running_threads.append(threading.Thread(target=ledController.show_plane, args=[config.leds.satellites.orbit_plane_c]))

        # Start all threads
        for thread in running_threads:
            thread.daemon = True
            thread.start()

        # Start plotting loop. This has to be done in the main thread
        skyplot = SkyPlot(constants.MAX_SATS)
        ledPlot = LedPlot(10, ledController.ledstrip)
        while True:
            skyplot.update_plot(ephemeris, azelev)
            ledPlot.update_plot()
            time.sleep(constants.PLOTTING_INTERVAL)

    finally:
        [thread.join() for thread in running_threads]

