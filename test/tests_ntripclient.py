import unittest
from unittest.mock import patch, MagicMock

from gnss_monitor.ntripclient import *

class TestCheckConnectionResponse(unittest.TestCase):
    @patch("sys.stderr.write")
    @patch("sys.exit")
    def test_check_connection_response_ok(self, mock_exit, mock_stderr_write):
        # Test when response is OK
        # Execute
        check_connection_response("HTTP/1.1 200 OK")

        # Verify
        mock_exit.assert_not_called()
        mock_stderr_write.assert_not_called()

    @patch("sys.stderr.write")
    def test_check_connection_response_error(self, mock_stderr_write):
        # Test when response is an error
        # Execute
        check_connection_response("HTTP/1.1 404 Not Found")

        # Verify
        mock_stderr_write.assert_called_with("HTTP/1.1 404 Not Found\n")

    @patch("sys.stderr.write")
    def test_check_connection_response_sourcetable(self, mock_stderr_write):
        # Test when SOURCETABLE is in the response
        # Execute
        check_connection_response("SOURCETABLE")

        # Verify
        mock_stderr_write.assert_any_call("SOURCETABLE\n")
        mock_stderr_write.assert_any_call("Mount point does not exist\n")


class TestNtripClient(unittest.TestCase):
    def setUp(self):
        # Sample configuration for the NtripClient class
        self.ntrip_config = Ntrip(
            address="ntrip.test.server",
            port=2101,
            username_password="test_user:test_pass",
            mountpoint="test_mount",
            software_name="TestClient",
            software_version="1.0",
            include_host_header=True,
            ntrip_v2=True
        )
        self.ephem = [{} for _ in range(36)]
        self.azelev = {}

    @patch("socket.create_connection")
    @patch("gnss_monitor.ntripclient.check_connection_response")
    def test_connect_to_server(self, mock_check_response, mock_create_connection):
        # Prepare
        mock_socket = MagicMock()
        mock_create_connection.return_value = mock_socket
        mock_socket.recv.return_value = b"ICY 200 OK\r\n"

        # Execute
        client = NtripClient(self.ephem, self.azelev, self.ntrip_config)

        # Verify
        mock_create_connection.assert_called_with((self.ntrip_config.address, self.ntrip_config.port))
        mock_socket.sendall.assert_called()
        mock_check_response.assert_called_with("ICY 200 OK")

    @patch("gnss_monitor.ntripclient.NtripClient.connect_to_server")
    def test_get_mount_point_for_request(self, mock_connect_to_server):
        # Prepare
        mock_socket = MagicMock()
        mock_connect_to_server.return_value = mock_socket

        # Execute
        client = NtripClient(self.ephem, self.azelev, self.ntrip_config)
        request = client.get_mount_point_for_request().decode("ascii")

        # Verify
        self.assertIn(f"GET /{self.ntrip_config.mountpoint} HTTP/1.1", request)
        self.assertIn(f"User-Agent: NTRIP {self.ntrip_config.software_name}/{self.ntrip_config.software_version}", request)
        self.assertIn("Authorization: Basic", request)
        self.assertIn(f"Host: {self.ntrip_config.address}:{self.ntrip_config.port}", request)
        self.assertIn("Ntrip-Version: Ntrip/2.0", request)

    @patch("pyrtcm.RTCMReader")
    @patch("gnss_monitor.ntripclient.NtripClient.connect_to_server")
    def test_get_ephemeris_loop(self, mock_connect_to_server, mock_rtcm_reader):
        # Prepare
        # Mock an ephemeris entry with a 'gst' property and a 'map_to_ephemeris' method
        mock_ephemeris_entry = MagicMock()
        mock_ephemeris_entry.gst = 0
        self.ephem[0] = mock_ephemeris_entry  # Assume satID is 1, so index 0 is used

        # Mock RTCMReader to provide a fake parsed data entry
        mock_parsed_data = MagicMock()
        mock_parsed_data.DF002 = constants.DF_GALILEO_EPH
        mock_parsed_data.DF252 = 1  # satID
        mock_parsed_data.DF289 = 2
        mock_parsed_data.DF293 = 3

        # GST calculated as DF289 * SEC_IN_WEEK + DF293
        expected_gst = (2 * constants.SEC_IN_WEEK) + 3

        # Set the mocked RTCMReader to yield the mocked parsed data
        mock_reader = MagicMock()
        mock_reader.__iter__.return_value = [(None, mock_parsed_data)]
        mock_rtcm_reader.return_value = mock_reader

        # Execute
        # Create the client and invoke get_ephemeris_loop
        client = NtripClient(self.ephem, self.azelev, self.ntrip_config)
        client.get_ephemeris_loop()

        # Verify
        # Ensure RTCMReader was initialized correctly
        mock_rtcm_reader.assert_called_with(client.socket, quitonerror=2)

        # Check if the ephemeris entry was updated with new GST
        mock_ephemeris_entry.map_to_ephemeris.assert_called_once_with(mock_parsed_data)

    @patch("socket.create_connection")
    def test_connect_to_server_with_socket_error(self, mock_create_connection):
        # Prepare
        # Test connection failure due to a socket error
        mock_create_connection.side_effect = socket.error("Connection failed")

        # Execute and Verify
        with self.assertRaises(socket.error):
            NtripClient(self.ephem, self.azelev, self.ntrip_config)

if __name__ == '__main__':
    unittest.main()
