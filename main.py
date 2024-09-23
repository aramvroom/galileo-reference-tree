# !/usr/bin/env -S python3 -u

import datetime
import os
import sys
import threading
import time

from astropy.time import Time

import constants
import ntripclient as ntrip
from satephemeris import SatEphemeris
from skyplot import SkyPlot
from transform import geodetic2aer


def propagate_all(all_ephem, all_azelev, verbose=False):
    # Start continuous loop
    while True:
        # Loop over all the ephemeris
        for idx in range(constants.MAX_SATS):
            eph = all_ephem[idx]

            # If it has a Time of Ephemeris, it can be propagated
            if eph.toe:
                x, y, z = eph.propagate(getCurrentToW())

                # Convert to azumuth, elevation and range
                az, elev, r = geodetic2aer(x, y, z, constants.OWN_LAT_DEG, constants.OWN_LON_DEG,
                                           constants.OWN_ALT_M)
                all_azelev[idx] = [az, elev]
                if verbose:
                    print('Sat', eph.prn, 'az', az, 'elev', elev, 'r', r)
        time.sleep(constants.PROPAGATION_INTERVAL)


def getCurrentToW():
    now = datetime.datetime.utcnow()
    gpsTimeNow = Time(now, format='datetime').to_value('gps')
    gpsTow = gpsTimeNow % constants.SEC_IN_WEEK
    return gpsTow


def getNtripArgs(output_file="", header_file=False):
    args = {'lat': constants.OWN_LAT_DEG, 'lon': constants.OWN_LON_DEG, 'height': constants.OWN_ALT_M,
                 'host': constants.INCLUDE_HOST_HEADER, 'ssl': constants.USE_SSL,
                 'caster': constants.CASTER_URL, 'port': constants.CASTER_PORT, 'mountpoint': constants.MOUNTPOINT,
                 'V2': constants.USE_NTRIP_V2, 'verbose': constants.VERBOSE,
                 'headerOutput': constants.WRITE_HEADER}
    if output_file:
        file = open(output_file, 'wb')
        args['out'] = file
    else:
        stdout = os.fdopen(sys.stdout.fileno(), "wb", closefd=False, buffering=0)
        args['out'] = stdout

    if header_file:
        h = open(header_file, 'w')
        args['headerFile'] = h
        args['headerOutput'] = True
    return args


if __name__ == '__main__':
    outputFile = ''
    headerFile = False

    # Create dictionary with options for the NTRIP client
    ntripArgs = getNtripArgs(outputFile, headerFile)

    # Create data structures for the ephemeris and azimuth + elevation
    ephemeris = []
    for satIdx in range(constants.MAX_SATS):
        ephemeris.append(SatEphemeris())
    azelev = [[] for _ in range(constants.MAX_SATS)]

    try:
        # Start RTCM retrieval loop
        client = ntrip.NtripClient(ephemeris, azelev, **ntripArgs)
        p1 = threading.Thread(target=client.readData)
        p1.setDaemon(True)
        p1.start()

        # Start propagation loop
        p2 = threading.Thread(target=propagate_all, args=[ephemeris, azelev, constants.VERBOSE])
        p2.setDaemon(True)
        p2.start()

        # Start plotting loop. This has to be done in the main thread
        skyplot = SkyPlot(constants.MAX_SATS)
        while True:
            skyplot.update_plot(ephemeris, azelev)
            time.sleep(constants.PLOTTING_INTERVAL)

    finally:
        p1.join()
        p2.join()
