# !/usr/bin/env -S python3 -u

import datetime
import threading
import time
from math import floor

from astropy.time import Time
from dataclass_binder import Binder

from galileo_reference_tree import constants
from galileo_reference_tree.config import Config, Location
from galileo_reference_tree.ledcontroller import LedController
from galileo_reference_tree.ntripclient import NtripClient
from galileo_reference_tree.plotleds import LedPlot
from galileo_reference_tree.satephemeris import SatEphemeris
from galileo_reference_tree.skyplot import SkyPlot
from galileo_reference_tree.transform import ecef2aer
from galileo_reference_tree.twolineelements import TwoLineElements

TIME_START = datetime.datetime.now(datetime.UTC)


def propagate_all(all_ephem, all_azelev, location: Location, simulation_speed=1):
    """
    Continuously propagates ephemeris data and computes the satellites' azimuth and
    elevation as observed from a specific location. The propagation is performed in a loop
    for a predefined number of satellites, and the results are updated in the specified
    all_ephem and azimuth-elevation output arrays.

    Parameters:
        all_ephem (list[SatEphemeris]): A list of ephemeris data objects for satellites.
            Assumes a fixed length as defined by constants.MAX_SATS.
        all_azelev (list[list[float]]): A mutable list to store the resulting azimuth,
            elevation pairs for each satellite.
        location (Location): A Location object which contains latitude, longitude, and
            altitude in degrees and meters respectively.
        simulation_speed (int, optional): optional speed-up factor for the simulation's
            time progression. Default is 1.
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
        time.sleep(constants.PROPAGATION_INTERVAL)


def get_utc_now():
    """
    This function retrieves the current date and time in UTC. It exists in order to allow mocking

    Returns:
        datetime.datetime: Current date and time in UTC format.
    """
    return datetime.datetime.now(datetime.UTC)


def getCurrentToW(simulation_speed=1):
    """
    Calculates the current GPS Week Number (WN) and Time of Week (ToW) based on
    the simulation speed and the current system UTC time. This utilizes a
    predefined start time `TIME_START` and converts the time to GPS format
    for further computations.

    Parameters:
        simulation_speed (int | float): The speed multiplier to simulate GPS
            time, where 1 represents real-time.

    Returns:
        tuple[float, float]: The (gps_wn, gps_tow) in weeks and seconds respectively
    """
    current_time = (get_utc_now() - TIME_START) * simulation_speed + TIME_START
    gps_time_now = Time(current_time, format='datetime').to_value('gps')
    gps_tow = gps_time_now % constants.SEC_IN_WEEK
    gps_wn = floor(gps_time_now / constants.SEC_IN_WEEK)
    return gps_wn, gps_tow


if __name__ == '__main__':

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
        client = NtripClient(ephemeris, config.ntrip)
        running_threads.append(threading.Thread(target=client.get_ephemeris_loop))

        # Create propagation loop
        running_threads.append(threading.Thread(target=propagate_all,
                                                args=[ephemeris, azelev, config.location,
                                                      config.general.simulation_speed]))

        # Create LED update loop for satellites
        ledController = LedController(constants.MAX_SATS, ephemeris, azelev, config.leds)
        running_threads.append(threading.Thread(target=ledController.update_leds))

        # Create LED update loop for orbital planes
        running_threads.append(
            threading.Thread(target=ledController.show_plane, args=[config.leds.satellites.orbit_plane_a]))
        running_threads.append(
            threading.Thread(target=ledController.show_plane, args=[config.leds.satellites.orbit_plane_b]))
        running_threads.append(
            threading.Thread(target=ledController.show_plane, args=[config.leds.satellites.orbit_plane_c]))

        # Start all threads
        for thread in running_threads:
            thread.daemon = True
            thread.start()

        if config.general.plotting:
            # Start plotting loop. This has to be done in the main thread
            skyplot = SkyPlot(constants.MAX_SATS)
            ledPlot = LedPlot(10, ledController.ledstrip)
            while True:
                skyplot.update_plot(ephemeris, azelev)
                ledPlot.update_plot()
                time.sleep(constants.PLOTTING_INTERVAL)

    finally:
        [thread.join() for thread in running_threads if thread.is_alive()]
