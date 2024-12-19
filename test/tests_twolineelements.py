import io
import unittest
from unittest.mock import patch

from gnss_monitor.satephemeris import SatEphemeris
from gnss_monitor.twolineelements import TwoLineElements


class TestTwoLineElements(unittest.TestCase):

    def setUp(self):
        # Sample Galileo TLE CSV data
        self.mock_tle_csv = """OBJECT_NAME,OBJECT_ID,EPOCH,MEAN_MOTION,ECCENTRICITY,INCLINATION,RA_OF_ASC_NODE,ARG_OF_PERICENTER,MEAN_ANOMALY,EPHEMERIS_TYPE,CLASSIFICATION_TYPE,NORAD_CAT_ID,ELEMENT_SET_NO,REV_AT_EPOCH,BSTAR,MEAN_MOTION_DOT,MEAN_MOTION_DDOT
GSAT0101 (GALILEO-PFM),2011-060A,2024-12-17T03:37:34.461120,1.70475748,.0002871,57.1195,356.5835,315.9115,44.0866,0,U,37846,999,8192,0,-.91E-6,0
GSAT0102 (GALILEO-FM2),2011-060B,2024-12-17T01:46:49.519200,1.70475232,.0004632,57.1222,356.5858,304.3209,53.8272,0,U,37847,999,8192,0,-.91E-6,0"""

        # Sample Galileo SV ID Mapping HTML (simplified)
        self.mock_html = """
        <table>
            <tr><th>Satellite Name</th><th>SV ID</th></tr>
            <tr><td>GSAT0101</td><td>E01</td></tr>
            <tr><td>GSAT0102</td><td>E02</td></tr>
        </table>
        """

        # Ephemeris mock object
        self.mock_ephemeris = [SatEphemeris() for _ in range(2)]  # Placeholder for ephemeris list with empty dicts

    @patch('gnss_monitor.twolineelements.requests.get')
    @patch('gnss_monitor.twolineelements.load.open')
    @patch('gnss_monitor.twolineelements.load.exists')
    @patch('gnss_monitor.twolineelements.load.download')
    def test_initialization(self, mock_download, mock_exists, mock_open_file, mock_requests_get):
        """Test that TLE data is fetched and parsed correctly during initialization."""
        # Mock the file exists and its content
        mock_exists.return_value = False  # Simulate file does not exist, so download is triggered
        mock_open_file.return_value = io.StringIO(self.mock_tle_csv)

        # Mock HTTP request for constellation info
        mock_requests_get.return_value.status_code = 200
        mock_requests_get.return_value.text = self.mock_html

        # Initialize the TwoLineElements class
        tle = TwoLineElements()

        # Assertions
        mock_download.assert_called_once()  # Ensure download was called
        self.assertEqual(len(tle.sats), 2)  # Two satellites parsed from CSV
        self.assertEqual(tle.sats[0].name, 'GSAT0101 (GALILEO-PFM)')  # First satellite name
        self.assertEqual(tle.sats[1].name, 'GSAT0102 (GALILEO-FM2)')  # Second satellite name
        self.assertEqual(tle.gsat_to_svid_map['GSAT0101'], 1)  # SV ID mapping
        self.assertEqual(tle.gsat_to_svid_map['GSAT0102'], 2)

    @patch('gnss_monitor.twolineelements.requests.get')
    def test_get_gsat_to_svid_map(self, mock_requests_get):
        """Test the Galileo satellite to SV ID mapping retrieval."""
        # Mock successful HTTP response with simplified HTML
        mock_requests_get.return_value.status_code = 200
        mock_requests_get.return_value.text = self.mock_html

        # Create instance and test map retrieval
        tle = TwoLineElements()
        tle.get_gsat_to_svid_map()

        # Assertions
        self.assertEqual(tle.gsat_to_svid_map['GSAT0101'], 1)
        self.assertEqual(tle.gsat_to_svid_map['GSAT0102'], 2)

    @patch('gnss_monitor.twolineelements.requests.get')
    @patch('gnss_monitor.twolineelements.load.open')
    def test_set_tle(self, mock_open_file, mock_requests_get):
        """Test the set_tle method, ensuring TLEs are assigned correctly."""
        # Mock file content with TLE CSV
        mock_open_file.return_value = io.StringIO(self.mock_tle_csv)
        # Mock successful HTTP response with simplified HTML
        mock_requests_get.return_value.status_code = 200
        mock_requests_get.return_value.text = self.mock_html

        # Initialize TLE class
        tle = TwoLineElements()

        # Set TLEs to mock ephemeris
        tle.set_tle(self.mock_ephemeris)

        # Assertions
        self.assertEqual(self.mock_ephemeris[0].tle.name, 'GSAT0101 (GALILEO-PFM)')
        self.assertEqual(self.mock_ephemeris[1].tle.name, 'GSAT0102 (GALILEO-FM2)')

    @patch('gnss_monitor.twolineelements.requests.get')
    @patch('gnss_monitor.twolineelements.load.open')
    def test_set_tle_with_unknown_satellite(self, mock_open_file, mock_requests_get):
        """Test set_tle method when a satellite is not in the SV ID map."""
        # Mock file content with TLE CSV
        mock_open_file.return_value = io.StringIO(self.mock_tle_csv)
        # Mock successful HTTP response with simplified HTML
        mock_requests_get.return_value.status_code = 200
        mock_requests_get.return_value.text = self.mock_html

        # Initialize TLE class
        tle = TwoLineElements()

        # Modify SV ID map to exclude one satellite
        tle.gsat_to_svid_map.pop('GSAT0102', None)

        with self.assertWarns(UserWarning):  # Expect a warning for unknown satellite
            tle.set_tle(self.mock_ephemeris)

        # Assertions
        self.assertEqual(self.mock_ephemeris[0].tle.name, 'GSAT0101 (GALILEO-PFM)')  # Known satellite
        self.assertEqual(self.mock_ephemeris[1].tle, None)  # Unknown satellite skipped


if __name__ == '__main__':
    unittest.main()
