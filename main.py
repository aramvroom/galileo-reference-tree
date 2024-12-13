# !/usr/bin/env -S python3 -u

import datetime
import threading
import time

from astropy.time import Time
from dataclass_binder import Binder

from gnss_monitor import constants
from gnss_monitor.config import Config
from gnss_monitor.ntripclient import NtripClient
from gnss_monitor.plotleds import LedPlot
from gnss_monitor.satephemeris import SatEphemeris
from gnss_monitor.skyplot import SkyPlot
from gnss_monitor.transform import geodetic2aer
from gnss_monitor.ledcontroller import LedController

TIME_START = datetime.datetime.now(datetime.UTC)

def propagate_all(all_ephem, all_azelev, location, simulation_speed=1, verbose=False):
    # Start continuous loop
    while True:
        # Loop over all the ephemeris
        for idx in range(constants.MAX_SATS):
            eph = all_ephem[idx]

            # If it has a Time of Ephemeris, it can be propagated
            if eph.toe:
                x, y, z = eph.propagate(getCurrentToW(simulation_speed))

                # Convert to azimuth, elevation and range
                az, elev, r = geodetic2aer(x, y, z, location.latitude_deg, location.longitude_deg,
                                           location.altitude_m)
                all_azelev[idx] = [az, elev]
                if verbose:
                    print('Sat', eph.prn, 'az', az, 'elev', elev, 'r', r)
        time.sleep(constants.PROPAGATION_INTERVAL)


def get_utc_now():
    return datetime.datetime.now(datetime.UTC)

def getCurrentToW(simulation_speed = 1):
    current_time = (get_utc_now() - TIME_START) * simulation_speed + TIME_START
    gps_time_now = Time(current_time, format='datetime').to_value('gps')
    gps_tow = gps_time_now % constants.SEC_IN_WEEK
    return gps_tow


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

    try:
        # Start RTCM retrieval loop
        client = NtripClient(ephemeris, azelev, config.ntrip)
        p1 = threading.Thread(target=client.get_ephemeris_loop)
        p1.daemon = True
        p1.start()

        # Start propagation loop
        p2 = threading.Thread(target=propagate_all, args=[ephemeris, azelev, config.location, config.simulation_speed, config.verbose])
        p2.daemon = True
        p2.start()

        # Start LED update loop for satellites
        ledController = LedController(constants.MAX_SATS, ephemeris, azelev, config.leds)
        ledController.update_leds()
        #p3 = threading.Thread(target=ledController.update_leds)
        #p3.start()

        # Start LED update loop for orbital planes
        p4 = threading.Thread(target=ledController.show_plane, args=[config.leds.satellites.orbit_plane_a])
        p5 = threading.Thread(target=ledController.show_plane, args=[config.leds.satellites.orbit_plane_b])
        p6 = threading.Thread(target=ledController.show_plane, args=[config.leds.satellites.orbit_plane_c])
        p4.start()
        p5.start()
        p6.start()

        # Start plotting loop. This has to be done in the main thread
        skyplot = SkyPlot(constants.MAX_SATS)
        ledPlot = LedPlot(10, ledController.ledstrip)
        while True:
            skyplot.update_plot(ephemeris, azelev)
            ledPlot.update_plot()
            time.sleep(constants.PLOTTING_INTERVAL)

    finally:
        p1.join()
        p2.join()
        p3.join()
        p4.join()
        p5.join()
        p6.join()
