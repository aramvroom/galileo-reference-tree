# !/usr/bin/env -S python3 -u
"""
This is heavily based on the NtripPerlClient program written by BKG.
Then heavily based on a unavco original.

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

"""
import threading
import sys
import datetime
import time
import os
from astropy.time import Time

import constants
import ntripclient as ntrip
from satephemeris import SatEphemeris
from skyplot import SkyPlot

from transform import geodetic2aer


def propagate_all(all_ephem, all_azelev, verbose=False):
    while True:
        for idx in range(constants.MAX_SATS):
            eph = all_ephem[idx]
            if eph.toe:
                x, y, z = eph.propagate(getCurrentToW())
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


def getNtripArgs(outputFile="", headerFile=False):
    ntripArgs = {'lat': constants.OWN_LAT_DEG, 'lon': constants.OWN_LON_DEG, 'height': constants.OWN_ALT_M,
                 'host': constants.INCLUDE_HOST_HEADER, 'ssl': constants.USE_SSL,
                 'caster': constants.CASTER_URL, 'port': constants.CASTER_PORT, 'mountpoint': constants.MOUNTPOINT,
                 'V2': constants.USE_NTRIP_V2, 'verbose': constants.VERBOSE,
                 'headerOutput': constants.WRITE_HEADER}
    if outputFile:
        file = open(outputFile, 'wb')
        ntripArgs['out'] = file
        fileOutput = True
    else:
        stdout = os.fdopen(sys.stdout.fileno(), "wb", closefd=False, buffering=0)
        ntripArgs['out'] = stdout

    if headerFile:
        h = open(headerFile, 'w')
        ntripArgs['headerFile'] = h
        ntripArgs['headerOutput'] = True
    return ntripArgs


if __name__ == '__main__':
    outputFile = 'test10.rtcm'
    headerFile = False

    ntripArgs = getNtripArgs(outputFile, headerFile)

    ephemeris = []
    for satIdx in range(constants.MAX_SATS):
        ephemeris.append(SatEphemeris())
    azelev = [[] for _ in range(constants.MAX_SATS)]

    # Create objects
    client = ntrip.NtripClient(ephemeris, azelev, **ntripArgs)
    skyplot = SkyPlot(constants.MAX_SATS)

    try:
        # Start propagation & RTCM retrieval loops
        p1 = threading.Thread(target=client.readData)
        p2 = threading.Thread(target=propagate_all, args=[ephemeris, azelev])
        p1.setDaemon(True)
        p2.setDaemon(True)
        p1.start()
        p2.start()

        # Plotting loop. This has to be done in the main thread
        while True:
            skyplot.update_plot(ephemeris, azelev)
            time.sleep(0.5)

    finally:
        p1.join()
        p2.join()
