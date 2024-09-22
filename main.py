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
from math import sqrt, sin, cos, pi, atan2, hypot
import socket
import sys
import datetime
import base64
import time
import os
import ssl
from optparse import OptionParser
from matplotlib.lines import Line2D
from matplotlib.text import Annotation
from pyrtcm import RTCMReader
from astropy.time import Time
import matplotlib.pyplot as plt

CLIENT_VERSION = 0.3
USER_AGENT = "NTRIP JCMBsoftPythonClient/%.1f" % CLIENT_VERSION

# reconnect parameter (fixed values):
SLEEP_TIME_FACTOR = 2  # How much the sleep time increases with each failed attempt
MAX_RECONNECTS = 1
MAX_RECONNECT_TIMEOUT = 1200
sleepTime = 1  # So the first one is 1 second

MU_EARTH = 3.986004418e14
ROT_RATE_EARTH = 7292115.0e-11

SEC_IN_WEEK = 24 * 3600 * 7
DF_GALILEO_EPH = 1046
SPEED_OF_LIGHT = 2.99792458e8

# WGS84ellipsoid constants:
WGS84_SEMI_MAJOR_AXIS = 6378137
WGS84_FIRST_ECCENTRICITY_SQUARED = 6.69437999014e-3

OWN_LAT_DEG = 52
OWN_LON_DEG = 4
OWN_ALT_M = 0

RAD_TO_DEG = 180 / pi
DEG_TO_RAD = pi / 180


class SatEphemeris:
    def __init__(self):
        self.gst = 0
        self.prn = 0
        self.signalHealth = 0
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

    def readRTCM(self, rtcm):
        self.gst = rtcm.DF289 * SEC_IN_WEEK + rtcm.DF293
        self.prn = rtcm.DF252
        self.signalHealth = rtcm.DF287
        self.dataValidity = rtcm.DF288
        self.wn = rtcm.DF289
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

    def propagate(self, tow):
        tk = tow - self.toe
        if tk > SEC_IN_WEEK / 2:
            tk -= SEC_IN_WEEK
        elif tk < -SEC_IN_WEEK / 2:
            tk += SEC_IN_WEEK

        n0 = sqrt(MU_EARTH / pow(self.a, 3))
        n = n0 + self.deltaN
        M = self.m0 + n * tk

        ek = self.getEccentricAnomaly(M)
        F = -2 * sqrt(MU_EARTH) / (SPEED_OF_LIGHT * SPEED_OF_LIGHT)
        delta_tr = F * self.ecc * sqrt(self.a) * sin(ek)
        delta_t = self.af0 + self.af1 * tk + delta_tr
        t = tow - delta_t
        tk = t - self.toe
        M = self.m0 + n * tk

        ek = self.getEccentricAnomaly(M)

        v = atan2(sqrt(1 - self.ecc * self.ecc) * sin(ek), cos(ek) - self.ecc)
        phi = v + self.omega
        u = phi + self.cuc * cos(2 * phi) + self.cus * sin(2 * phi)
        r = self.a * (1 - self.ecc * cos(ek)) + self.crc * cos(2 * phi) + self.crs * sin(2 * phi)
        i = self.i0 + self.iDot * tk
        Omega = self.Omega0 + (self.OmegaDot - ROT_RATE_EARTH) * tk - ROT_RATE_EARTH * self.toe
        x1 = cos(u) * r
        y1 = sin(u) * r

        x = x1 * cos(Omega) - y1 * cos(i) * sin(Omega)
        y = x1 * sin(Omega) + y1 * cos(i) * cos(Omega)
        z = y1 * sin(i)
        return x, y, z

    def getEccentricAnomaly(self, mean_anomaly):
        nr_next = 0
        nr = 1
        iter_ctr = 1
        while abs(nr_next - nr) > 1e-15 and iter_ctr < 200:
            nr = nr_next
            f = nr - self.ecc * sin(nr) - mean_anomaly
            f1 = 1 - self.ecc * cos(nr)
            f2 = self.ecc * sin(nr)
            nr_next = nr - (f / (f1 - (f2 * f / 2 * f1)))
            iter_ctr += 1
        ek = nr_next
        return ek


class NtripClient(object):
    def __init__(self,
                 ephem,
                 azelev,
                 buffer=50,
                 user="",
                 out=sys.stdout,
                 port=2101,
                 caster="",
                 mountpoint="",
                 host=False,
                 lat=46,
                 lon=122,
                 height=1212,
                 ssl=False,
                 verbose=False,
                 UDP_Port=None,
                 V2=False,
                 headerFile=sys.stderr,
                 headerOutput=False,
                 maxConnectTime=0
                 ):
        self.buffer = buffer
        self.user = base64.b64encode(bytes(user, 'utf-8')).decode("utf-8")
        self.out = out
        self.port = port
        self.caster = caster
        self.mountpoint = mountpoint
        self.setPosition(lat, lon)
        self.height = height
        self.verbose = verbose
        self.ssl = ssl
        self.host = host
        self.UDP_Port = UDP_Port
        self.V2 = V2
        self.headerFile = headerFile
        self.headerOutput = headerOutput
        self.maxConnectTime = maxConnectTime
        self.socket = None
        self.flagE = None
        self.flagN = None

        self.ephemeris = ephem
        self.azelev = azelev

        if UDP_Port:
            self.UDP_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.UDP_socket.bind(('', 0))
            self.UDP_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        else:
            self.UDP_socket = None

    def setPosition(self, lat, lon):
        self.flagN = "N"
        self.flagE = "E"
        if lon > 180:
            lon = (lon - 360) * -1
            self.flagE = "W"
        elif 0 > lon >= -180:
            lon = lon * -1
            self.flagE = "W"
        elif lon < -180:
            lon = lon + 360
            self.flagE = "E"
        if lat < 0:
            lat = lat * -1
            self.flagN = "S"
        self.lonDeg = int(lon)
        self.latDeg = int(lat)
        self.lonMin = (lon - self.lonDeg) * 60
        self.latMin = (lat - self.latDeg) * 60

    def getMountPointBytes(self):
        mountPointString = "GET %s HTTP/1.1\r\nUser-Agent: %s\r\nAuthorization: Basic %s\r\n" % (
            self.mountpoint, USER_AGENT, self.user)
        if self.host or self.V2:
            hostString = "Host: %s:%i\r\n" % (self.caster, self.port)
            mountPointString += hostString
        if self.V2:
            mountPointString += "Ntrip-Version: Ntrip/2.0\r\n"
        mountPointString += "\r\n"
        if self.verbose:
            print(mountPointString)
        return bytes(mountPointString, 'ascii')

    def getGGABytes(self):
        now = datetime.datetime.utcnow()
        ggaString = "GPGGA,%02d%02d%04.2f,%02d%011.8f,%1s,%03d%011.8f,%1s,1,05,0.19,+00400,M,%5.3f,M,," % \
                    (now.hour, now.minute, now.second, self.latDeg, self.latMin, self.flagN, self.lonDeg, self.lonMin,
                     self.flagE, self.height)
        checksum = calcultateCheckSum(ggaString)
        if self.verbose:
            print("$%s*%s\r\n" % (ggaString, checksum))
        return bytes("$%s*%s\r\n" % (ggaString, checksum), 'ascii')

    def findHeader(self):
        found_header = False
        while not found_header:
            casterResponse = self.socket.recv(4096)  # All the data
            header_lines = casterResponse.decode('utf-8').split("\r\n")

            for line in header_lines:
                if line == "":
                    if not found_header:
                        found_header = True
                        if self.verbose:
                            sys.stderr.write("End Of Header" + "\n")
                else:
                    if self.verbose:
                        sys.stderr.write("Header: " + line + "\n")
                if self.headerOutput:
                    self.headerFile.write(line + "\n")

            for line in header_lines:
                if line.find("SOURCETABLE") >= 0:
                    sys.stderr.write("Mount point does not exist")
                    sys.exit(1)
                elif line.find("401 Unauthorized") >= 0:
                    sys.stderr.write("Unauthorized request\n")
                    sys.exit(1)
                elif line.find("404 Not Found") >= 0:
                    sys.stderr.write("Mount Point does not exist\n")
                    sys.exit(2)
                elif line.find("ICY 200 OK") >= 0:
                    # Request was valid
                    self.socket.sendall(self.getGGABytes())
                elif line.find("HTTP/1.0 200 OK") >= 0:
                    # Request was valid
                    self.socket.sendall(self.getGGABytes())
                elif line.find("HTTP/1.1 200 OK") >= 0:
                    # Request was valid
                    self.socket.sendall(self.getGGABytes())

    def readData(self):
        reconnectTry = 1
        sleepTime = 1
        error_indicator = 0
        if self.maxConnectTime > 0:
            EndConnect = datetime.timedelta(seconds=self.maxConnectTime)
        try:
            while reconnectTry <= MAX_RECONNECTS:
                if self.verbose:
                    sys.stderr.write('Connection {0} of {1}\n'.format(reconnectTry, MAX_RECONNECTS))

                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                if self.ssl:
                    self.socket = ssl.wrap_socket(self.socket)

                error_indicator = self.socket.connect_ex((self.caster, self.port))

                if error_indicator:
                    self.socket = None
                    if self.verbose:
                        print("Error indicator: ", error_indicator)

                    if reconnectTry < MAX_RECONNECTS:
                        sys.stderr.write("%s No Connection to NtripCaster.  Trying again in %i seconds\n" % (
                            datetime.datetime.now(), sleepTime))
                        time.sleep(sleepTime)
                        sleepTime *= SLEEP_TIME_FACTOR
                        if sleepTime > MAX_RECONNECT_TIMEOUT:
                            sleepTime = MAX_RECONNECT_TIMEOUT
                    reconnectTry += 1
                    continue

                sleepTime = 1
                connectTime = datetime.datetime.now()

                self.socket.settimeout(10)
                self.socket.sendall(self.getMountPointBytes())
                self.findHeader()

                rtr = RTCMReader(self.socket, quitonerror=2)
                for (raw_data, parsed_data) in rtr:
                    if parsed_data.DF002 == DF_GALILEO_EPH:
                        satID = parsed_data.DF252
                        gst = parsed_data.DF289 * SEC_IN_WEEK + parsed_data.DF293
                        if gst > ephemeris[satID - 1].gst:
                            ephemeris[satID - 1].readRTCM(parsed_data)

        except socket.timeout:
            if self.verbose:
                sys.stderr.write('Connection TimedOut\n')
        except socket.error:
            if self.verbose:
                sys.stderr.write('Connection Error\n')

        except KeyboardInterrupt:
            if self.socket:
                sys.stderr.write('Closing Connection\n')
                self.socket.close()
            sys.exit()

        if error_indicator:
            if self.socket:
                sys.stderr.write('Closing Connection\n')
                self.socket.close()
            sys.exit()

        if reconnectTry < MAX_RECONNECTS:
            sys.stderr.write("%s No Connection to NtripCaster.  Trying again in %i seconds\n" % (
                datetime.datetime.now(), sleepTime))
            time.sleep(sleepTime)
            sleepTime *= SLEEP_TIME_FACTOR

            if sleepTime > MAX_RECONNECT_TIMEOUT:
                sleepTime = MAX_RECONNECT_TIMEOUT
        else:
            sys.exit(1)

        reconnectTry += 1

    def propagate_all(self):
        while True:
            for satIdx in range(36):
                eph = self.ephemeris[satIdx]
                if eph.toe:
                    x, y, z = eph.propagate(getCurrentToW())
                    az, elev, r = geodetic2aer(x, y, z, OWN_LAT_DEG, OWN_LON_DEG, OWN_ALT_M)
                    self.azelev[satIdx] = [az, elev]
                    if self.verbose:
                        print('Sat', eph.prn, 'az', az, 'elev', elev, 'r', r)
            time.sleep(0.1)


def calcultateCheckSum(stringToCheck):
    xsum_calc = 0
    for char in stringToCheck:
        xsum_calc = xsum_calc ^ ord(char)
    return "%02X" % xsum_calc


def lla2ecef(lat, lon, alt):
    # Source: https://github.com/sglvladi/MATLAB/blob/master/ecef.py

    lat *= DEG_TO_RAD
    lon *= DEG_TO_RAD

    N = WGS84_SEMI_MAJOR_AXIS / sqrt(1 - WGS84_FIRST_ECCENTRICITY_SQUARED * sin(lat) * sin(lat))
    x = (N + alt) * cos(lat) * cos(lon)
    y = (N + alt) * cos(lat) * sin(lon)
    z = ((1 - WGS84_FIRST_ECCENTRICITY_SQUARED) * N + alt) * sin(lat)
    return x, y, z


def geodetic2aer(x, y, z, lat0, lon0, alt0):
    x0, y0, z0 = lla2ecef(lat0, lon0, alt0)
    e, n, u = ecef2enu(x - x0, y - y0, z - z0, lat0, lon0)

    r = hypot(e, n)
    slantRange = hypot(r, u)
    elev = atan2(u, r) * RAD_TO_DEG
    az = atan2(e, n) % (2 * pi) * RAD_TO_DEG

    return az, elev, slantRange


def ecef2enu(u, v, w, lat0, lon0):
    lat0 = DEG_TO_RAD * lat0
    lon0 = DEG_TO_RAD * lon0

    t = cos(lon0) * u + sin(lon0) * v
    east = -sin(lon0) * u + cos(lon0) * v
    up = cos(lat0) * t + sin(lat0) * w
    north = -sin(lat0) * t + cos(lat0) * w
    return east, north, up


def getCurrentToW():
    now = datetime.datetime.utcnow()
    gpsTimeNow = Time(now, format='datetime').to_value('gps')
    gpsTow = gpsTimeNow % SEC_IN_WEEK
    return gpsTow


if __name__ == '__main__':
    usage = "NtripClient.py [options] caster port mountpoint"
    parser = OptionParser(version=str(CLIENT_VERSION), usage=usage)
    parser.add_option("-u", "--user", type="string", dest="user", default="IBS",
                      help="The Ntripcaster username.  Default: %default")
    parser.add_option("-p", "--password", type="string", dest="password", default="IBS",
                      help="The Ntripcaster password. Default: %default")
    parser.add_option("-o", "--org", type="string", dest="org",
                      help="Use IBSS and the provided organization for the user. Caster and Port are not needed in "
                           "this case Default: %default")
    parser.add_option("-b", "--baseorg", type="string", dest="baseorg",
                      help="The org that the base is in. IBSS Only, assumed to be the user org")
    parser.add_option("-t", "--latitude", type="float", dest="lat", default=50.09,
                      help="Your latitude.  Default: %default")
    parser.add_option("-g", "--longitude", type="float", dest="lon", default=8.66,
                      help="Your longitude.  Default: %default")
    parser.add_option("-e", "--height", type="float", dest="height", default=1200,
                      help="Your ellipsoid height.  Default: %default")
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Verbose")
    parser.add_option("-T", "--Tell", action="store_true", dest="tell", default=False, help="Tell Settings")
    parser.add_option("-s", "--ssl", action="store_true", dest="ssl", default=False, help="Use SSL for the connection")
    parser.add_option("-H", "--host", action="store_true", dest="host", default=False,
                      help="Include host header, should be on for IBSS")
    parser.add_option("-r", "--Reconnect", type="int", dest="maxReconnect", default=1, help="Number of reconnections")
    parser.add_option("-D", "--UDP", type="int", dest="UDP", default=None,
                      help="Broadcast recieved data on the provided port")
    parser.add_option("-2", "--V2", action="store_true", dest="V2", default=False, help="Make a NTRIP V2 Connection")
    parser.add_option("-f", "--outputFile", type="string", dest="outputFile", default=None,
                      help="Write to this file, instead of stdout")
    parser.add_option("-m", "--maxtime", type="int", dest="maxConnectTime", default=0,
                      help="Maximum length of the connection, in seconds")

    parser.add_option("--Header", action="store_true", dest="headerOutput", default=False,
                      help="Write headers to stderr")
    parser.add_option("--HeaderFile", type="string", dest="headerFile", default=None,
                      help="Write headers to this file, instead of stderr.")
    (options, args) = parser.parse_args()
    ntripArgs = {}
    ntripArgs['lat'] = OWN_LAT_DEG
    ntripArgs['lon'] = OWN_LON_DEG
    ntripArgs['height'] = 0
    ntripArgs['host'] = False
    ntripArgs['ssl'] = False
    ntripArgs['caster'] = 'ntrip.kadaster.nl'
    ntripArgs['port'] = 2101
    ntripArgs['mountpoint'] = 'BCEP00KAD0'
    ntripArgs['V2'] = False
    ntripArgs['verbose'] = False
    ntripArgs['headerOutput'] = False
    MAX_RECONNECTS = 1
    options.outputFile = 'test10.rtcm'
    options.headerFile = False
    fileOutput = True

    if options.outputFile:
        file = open(options.outputFile, 'wb')
        ntripArgs['out'] = file
        fileOutput = True
    else:
        stdout = os.fdopen(sys.stdout.fileno(), "wb", closefd=False, buffering=0)
        ntripArgs['out'] = stdout

    if options.headerFile:
        h = open(options.headerFile, 'w')
        ntripArgs['headerFile'] = h
        ntripArgs['headerOutput'] = True

    max_sats = 36
    ephemeris = []
    for satIdx in range(max_sats):
        ephemeris.append(SatEphemeris())

    azelev = [[] for _ in range(max_sats)]
    sats_plot = [[Line2D] for _ in range(max_sats)]
    annot = [[Annotation] for _ in range(max_sats)]
    client = NtripClient(ephemeris, azelev, **ntripArgs)

    plt.ion()
    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
    ax.set_theta_zero_location("N")  # theta=0 at the top
    ax.set_theta_direction(-1)  # theta increasing clockwise
    ax.set_ylim([90, 0])
    ax.set_yticks([0, 15, 30, 45, 60, 90])

    satIdx: int
    for satIdx in range(max_sats):
        sats_plot[satIdx] = plt.polar([], [], 'g.')
        annot[satIdx] = ax.annotate('%s' % (satIdx + 1), xy=[-5, -5], textcoords='data')

    try:
        # p1 = mp.Process(target=propagate_all)
        p2 = threading.Thread(target=client.propagate_all)
        p2.start()
        p1 = threading.Thread(target=client.readData)
        p1.start()

        plt.show()
        while True:
            azelev_now = client.azelev
            for satIdx in range(max_sats):
                if len(azelev_now[satIdx]) and azelev_now[satIdx][1] >= 0:
                    Line2D.set_xdata(sats_plot[satIdx][0], [azelev_now[satIdx][0] / 180 * pi])
                    Line2D.set_ydata(sats_plot[satIdx][0], [azelev_now[satIdx][1]])
                    if not ephemeris[satIdx].signalHealth:
                        Line2D.set_color(sats_plot[satIdx][0], 'g')
                    else:
                        Line2D.set_color(sats_plot[satIdx][0], 'r')

                    annot[satIdx].xy = [azelev_now[satIdx][0] / 180 * pi, azelev_now[satIdx][1]]
                    annot[satIdx].set_x(azelev_now[satIdx][0] / 180 * pi)
                    annot[satIdx].set_y(azelev_now[satIdx][1])
                    plt.draw()
                    plt.pause(0.02)

            ax.set_title('Latest update %s' % datetime.datetime.utcnow().strftime('%Y/%m/%d - %H:%M:%S'))
            time.sleep(0.5)

    finally:
        p1.join()
        p2.join()
