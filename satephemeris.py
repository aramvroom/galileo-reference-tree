from math import pi, sqrt, sin, atan2, cos

import constants


class SatEphemeris(object):
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
        self.gst = rtcm.DF289 * constants.SEC_IN_WEEK + rtcm.DF293
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
        if tk > constants.SEC_IN_WEEK / 2:
            tk -= constants.SEC_IN_WEEK
        elif tk < -constants.SEC_IN_WEEK / 2:
            tk += constants.SEC_IN_WEEK

        n0 = sqrt(constants.MU_EARTH / pow(self.a, 3))
        n = n0 + self.deltaN
        M = self.m0 + n * tk

        ek = self.getEccentricAnomaly(M)
        F = -2 * sqrt(constants.MU_EARTH) / (constants.SPEED_OF_LIGHT * constants.SPEED_OF_LIGHT)
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
        Omega = self.Omega0 + (self.OmegaDot - constants.ROT_RATE_EARTH) * tk - constants.ROT_RATE_EARTH * self.toe
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
