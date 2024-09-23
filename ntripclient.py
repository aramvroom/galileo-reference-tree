"""
Source: https://github.com/jcmb/NTRIP/
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

import base64
import datetime
import socket
import ssl
import sys
import time

from pyrtcm import RTCMReader

import constants


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
        self.lonDeg = None
        self.latDeg = None
        self.lonMin = None
        self.latMin = None

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
            self.mountpoint, constants.USER_AGENT, self.user)
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
        checksum = self.calculateCheckSum(ggaString)
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

    def calculateCheckSum(self, stringToCheck):
        xsum_calc = 0
        for char in stringToCheck:
            xsum_calc = xsum_calc ^ ord(char)
        return "%02X" % xsum_calc

    def readData(self):
        reconnectTry = 1
        NTRIP_INTERVAL = 1
        error_indicator = 0
        if self.maxConnectTime > 0:
            EndConnect = datetime.timedelta(seconds=self.maxConnectTime)
        try:
            while reconnectTry <= constants.MAX_RECONNECTS:
                if self.verbose:
                    sys.stderr.write('Connection {0} of {1}\n'.format(reconnectTry, constants.MAX_RECONNECTS))

                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                if self.ssl:
                    self.socket = ssl.wrap_socket(self.socket)

                error_indicator = self.socket.connect_ex((self.caster, self.port))

                if error_indicator:
                    self.socket = None
                    if self.verbose:
                        print("Error indicator: ", error_indicator)

                    if reconnectTry < constants.MAX_RECONNECTS:
                        sys.stderr.write("%s No Connection to NtripCaster.  Trying again in %i seconds\n" % (
                            datetime.datetime.now(), NTRIP_INTERVAL))
                        time.sleep(NTRIP_INTERVAL)
                        NTRIP_INTERVAL *= constants.SLEEP_TIME_FACTOR
                        if NTRIP_INTERVAL > constants.MAX_RECONNECT_TIMEOUT:
                            NTRIP_INTERVAL = constants.MAX_RECONNECT_TIMEOUT
                    reconnectTry += 1
                    continue

                NTRIP_INTERVAL = 1
                connectTime = datetime.datetime.now()

                self.socket.settimeout(10)
                self.socket.sendall(self.getMountPointBytes())
                self.findHeader()

                rtr = RTCMReader(self.socket, quitonerror=2)
                for (raw_data, parsed_data) in rtr:
                    if parsed_data.DF002 == constants.DF_GALILEO_EPH:
                        satID = parsed_data.DF252
                        gst = parsed_data.DF289 * constants.SEC_IN_WEEK + parsed_data.DF293
                        if gst > self.ephemeris[satID - 1].gst:
                            self.ephemeris[satID - 1].readRTCM(parsed_data)

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

        if reconnectTry < constants.MAX_RECONNECTS:
            sys.stderr.write("%s No Connection to NtripCaster.  Trying again in %i seconds\n" % (
                datetime.datetime.now(), NTRIP_INTERVAL))
            time.sleep(NTRIP_INTERVAL)
            NTRIP_INTERVAL *= constants.SLEEP_TIME_FACTOR

            if NTRIP_INTERVAL > constants.MAX_RECONNECT_TIMEOUT:
                NTRIP_INTERVAL = constants.MAX_RECONNECT_TIMEOUT
        else:
            sys.exit(1)

        reconnectTry += 1
