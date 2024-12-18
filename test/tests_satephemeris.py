import io
import struct
import unittest
from math import pi
from unittest.mock import MagicMock, patch

from astropy.time import Time
from pyrtcm import RTCM_DATA_FIELDS, RTCMMessage

from gnss_monitor import constants
from gnss_monitor.satephemeris import SatEphemeris, correct_wn_for_rollover
from gnss_monitor.twolineelements import TwoLineElements

class TestSatEphemeris(unittest.TestCase):
    def setUp(self):
        # One of the received Galileo ephemeris messages (ephemeris for 2024/12/15 12:30:00 UTC)
        self.rtcm = RTCMMessage(payload=b'A`\x94\xa4Kk\xd5\xa8.\xe0\x00\x01\x9e\x00\xbfZ\xa0\x1a\xa8}\xe8\xd5B\xda\xd8\x13\x94\x00\xf5&`f\x92\xa8\x13\xfd\x10.\xef\xfe\xc6\xc9\xb3P\xbf\xfd\xc2u35\x90\xa6Q\x99\x93\xc8\xef\xfc~\xdf\xbb\xed\x00')

    @patch("astropy.time.Time.to_value")
    def test_map_to_ephemeris(self, mock_to_value):
        # Prepare
        sat_ephemeris = SatEphemeris()
        mock_to_value.return_value = 1400 * constants.SEC_IN_WEEK

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

    @patch('gnss_monitor.twolineelements.requests.get')
    @patch('gnss_monitor.twolineelements.load.open')
    def test_propagate_tle(self, mock_open_file, mock_requests_get):
        # Prepare
        # Mocking TLE object is complex. As the TLE loader is already covered by another UT, it can be used here instead
        mock_tle = """OBJECT_NAME,OBJECT_ID,EPOCH,MEAN_MOTION,ECCENTRICITY,INCLINATION,RA_OF_ASC_NODE,ARG_OF_PERICENTER,MEAN_ANOMALY,EPHEMERIS_TYPE,CLASSIFICATION_TYPE,NORAD_CAT_ID,ELEMENT_SET_NO,REV_AT_EPOCH,BSTAR,MEAN_MOTION_DOT,MEAN_MOTION_DDOT
GSAT0211 (GALILEO 14),2016-030A,2024-12-15T22:14:03.283296,1.70473113,.0003845,55.2859,236.7768,4.5714,355.5270,0,U,41549,999,5330,0,.28E-6,0"""
        mock_html = """
        <table>
            <tr><th>Satellite Name</th><th>SV ID</th></tr>
            <tr><td>GSAT0211</td><td>E02</td></tr>
        </table>
        """

        # Mock file content with TLE CSV
        mock_open_file.return_value = io.StringIO(mock_tle)

        # Mock successful HTTP response with simplified HTML
        mock_requests_get.return_value.status_code = 200
        mock_requests_get.return_value.text = mock_html

        # Load the TLE into a SatEphemeris array
        sat_ephemeris = [SatEphemeris() for _ in range(2)]  # Placeholder for ephemeris list with empty dicts
        tle = TwoLineElements()
        tle.set_tle(sat_ephemeris)

        # Also load the RTCM data into the SatEphemeris array
        sat_ephemeris[1].map_to_ephemeris(self.rtcm)

        # Execute, by propagating both the TLE and the ephemeris
        x,y,z = sat_ephemeris[1].propagate_ephemeris(sat_ephemeris[1].toe + 600)
        x_tle,y_tle,z_tle = sat_ephemeris[1].propagate_tle(sat_ephemeris[1].wn, sat_ephemeris[1].toe + 600)

        # Verify, with a margin of 5km due to TLE inaccuracy
        self.assertAlmostEqual(x, x_tle, delta=5e3)
        self.assertAlmostEqual(y, y_tle, delta=5e3)
        self.assertAlmostEqual(z, z_tle, delta=5e3)

    @patch("astropy.time.Time.to_value")
    def test_get_time_with_rollover(self, mock_to_value):
        # Prepare
        ephem_wn = 7890
        expected_ephem_wn = 1746

        current_wn, current_tow = 1025, 5678
        mock_to_value.return_value = current_wn * constants.SEC_IN_WEEK + current_tow

        # Execute
        found_wn = correct_wn_for_rollover(ephem_wn)

        # Verify
        self.assertEqual(found_wn, expected_ephem_wn)

if __name__ == '__main__':
    unittest.main()
