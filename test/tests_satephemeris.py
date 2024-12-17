import struct
import unittest
from math import pi
from unittest.mock import MagicMock

from pyrtcm import RTCM_DATA_FIELDS, RTCMMessage

from gnss_monitor import constants
from gnss_monitor.satephemeris import SatEphemeris


class MyTestCase(unittest.TestCase):
    def setUp(self):
        # One of the received Galileo ephemeris messages (ephemeris for 2024/12/15 12:30:00 UTC)
        self.rtcm = RTCMMessage(payload=b'A`\x94\xa4Kk\xd5\xa8.\xe0\x00\x01\x9e\x00\xbfZ\xa0\x1a\xa8}\xe8\xd5B\xda\xd8\x13\x94\x00\xf5&`f\x92\xa8\x13\xfd\x10.\xef\xfe\xc6\xc9\xb3P\xbf\xfd\xc2u35\x90\xa6Q\x99\x93\xc8\xef\xfc~\xdf\xbb\xed\x00')

    def test_map_to_ephemeris(self):
        # Prepare
        sat_ephemeris = SatEphemeris()

        # Execute
        sat_ephemeris.map_to_ephemeris(self.rtcm)

        # Verify
        self.assertEqual(sat_ephemeris.gst, self.rtcm.DF304 + self.rtcm.DF289 * constants.SEC_IN_WEEK )
        self.assertEqual(sat_ephemeris.prn, self.rtcm.DF252)
        self.assertEqual(sat_ephemeris.signalHealth, self.rtcm.DF287)
        self.assertEqual(sat_ephemeris.dataValidity, self.rtcm.DF288)
        self.assertEqual(sat_ephemeris.wn, self.rtcm.DF289)
        self.assertEqual(sat_ephemeris.iodNav, self.rtcm.DF290)
        self.assertEqual(sat_ephemeris.iDot, self.rtcm.DF292 * pi)
        self.assertEqual(sat_ephemeris.toc, self.rtcm.DF293)
        self.assertEqual(sat_ephemeris.af2, self.rtcm.DF294)
        self.assertEqual(sat_ephemeris.af1, self.rtcm.DF295)
        self.assertEqual(sat_ephemeris.af0, self.rtcm.DF296)
        self.assertEqual(sat_ephemeris.crs, self.rtcm.DF297)
        self.assertEqual(sat_ephemeris.deltaN, self.rtcm.DF298 * pi)
        self.assertEqual(sat_ephemeris.m0, self.rtcm.DF299 * pi)
        self.assertEqual(sat_ephemeris.ecc, self.rtcm.DF301)
        self.assertEqual(sat_ephemeris.cus, self.rtcm.DF302)
        self.assertEqual(sat_ephemeris.a, self.rtcm.DF303 * self.rtcm.DF303)
        self.assertEqual(sat_ephemeris.toe, self.rtcm.DF304)
        self.assertEqual(sat_ephemeris.cic, self.rtcm.DF305)
        self.assertEqual(sat_ephemeris.Omega0, self.rtcm.DF306 * pi)
        self.assertEqual(sat_ephemeris.i0, self.rtcm.DF308 * pi)
        self.assertEqual(sat_ephemeris.crc, self.rtcm.DF309)
        self.assertEqual(sat_ephemeris.omega, self.rtcm.DF310 * pi)
        self.assertEqual(sat_ephemeris.OmegaDot, self.rtcm.DF311 * pi)


    def test_get_eccentric_anomaly(self):
        # Prepare
        sat_ephemeris = SatEphemeris()
        sat_ephemeris.map_to_ephemeris(self.rtcm)
        expected_eccentric_anomaly = pi

        # Execute
        found_eccentric_anomaly = sat_ephemeris.getEccentricAnomaly(pi)

        # Verify
        self.assertEqual(found_eccentric_anomaly, expected_eccentric_anomaly)

    def test_propagate_at_toe(self):
        # Prepare
        sat_ephemeris = SatEphemeris()
        sat_ephemeris.map_to_ephemeris(self.rtcm)
        expected_x, expected_y, expected_z = 417440.572,  18971103.221, 22713182.960    # From JGX0OPSULT_20243491200_02D_05M_ORB.SP3

        # Execute
        x,y,z = sat_ephemeris.propagate(sat_ephemeris.wn, sat_ephemeris.toe)

        # Verify (within 2 meters)
        self.assertAlmostEqual(x, expected_x, delta=2)
        self.assertAlmostEqual(y, expected_y, delta=2)
        self.assertAlmostEqual(z, expected_z, delta=2)

    def test_propagate_later(self):
        # Prepare
        sat_ephemeris = SatEphemeris()
        sat_ephemeris.map_to_ephemeris(self.rtcm)
        expected_x, expected_y, expected_z = -654659.021, 19786342.403, 22002213.080    # From JGX0OPSULT_20243491200_02D_05M_ORB.SP3

        # Execute (propagate to 10 minutes later)
        x,y,z = sat_ephemeris.propagate(sat_ephemeris.wn, sat_ephemeris.toe + 600)

        # Verify (within 2 meters)
        self.assertAlmostEqual(x, expected_x, delta=2)
        self.assertAlmostEqual(y, expected_y, delta=2)
        self.assertAlmostEqual(z, expected_z, delta=2)





if __name__ == '__main__':
    unittest.main()
