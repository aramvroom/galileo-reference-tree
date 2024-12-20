import base64
import socket
import sys

import pyrtcm

from gnss_monitor import constants
from gnss_monitor.config import Ntrip


def check_connection_response(line):
    """
    Check the given response line to determine if the connection was successful.

    Checks if the response indicates a successful connection. If the connection
    is not successful, it generates a RuntimeError with the details

    Parameters:
        line (str): The response line to be examined.

    Raises:
        RuntimeError:
            If the line does not indicate a successful connection
    """
    # These are the expected statuses
    if "ICY 200 OK" in line or "HTTP/1.0 200 OK" in line or "HTTP/1.1 200 OK" in line:
        return

    # If there was no OK, throw an error with the line
    error_string = line + "\n"

    # Also return human-readable error in case the mount point isn't found
    if "SOURCETABLE" in line:
        error_string += "Could not connect to mountpoint\n"

    raise RuntimeError(error_string)


class NtripClient(object):
    """
    Represents a client for connecting to a network caster/server. This class handles
    the setup, communication, and parsing of satellite data through the NTRIP
    protocol, ensuring that ephemeris data is updated as new information is
    received.

    Attributes:
        ephem (list[SatEphemeris]): Array of satellite ephemeris objects used to
            store RTCM data received from the server.
        config (Ntrip config object): An object containing the NTRIP configuration settings
            required for establishing a connection with the server.
        socket (socket): A socket object used to connect with the NTRIP caster/server.
        Initially set to None.
    """

    def __init__(self, ephem, ntrip_config: Ntrip):
        """
        Initialization of the NtripClient.

        Parameters:
            ephem (List[SatEphemeris]): Array of SatEphemeris objects to save the RTCM data to
            ntrip_config (Ntrip config object): NTRIP configuration data containing network settings.
        """
        self.ephem = ephem
        self.config = ntrip_config
        self.socket = None

        self.connect_to_server()

    def get_mount_point_for_request(self):
        """
        Constructs and returns the mount point request formatted as per the NTRIP protocol.

        This method creates an HTTP request string for accessing a specific mount
        point on an NTRIP caster. The request includes user authentication encoded in
        Base64, client information, and optional headers depending on the configuration
        specified. The resulting request is returned as a byte object to be sent to the
        server.

        Returns:
            bytes: The constructed mount point request encoded in ASCII format.
        """
        user_name_base64 = base64.b64encode(bytes(self.config.username_password, 'utf-8')).decode("utf-8")
        client_name = "NTRIP {0}/{1}".format(self.config.software_name, self.config.software_version)
        mount_point_request = "GET /{0} HTTP/1.1\r\nUser-Agent: {1}\r\nAuthorization: Basic {2}\r\n".format(
            self.config.mountpoint, client_name, user_name_base64)
        if self.config.include_host_header | self.config.ntrip_v2:
            mount_point_request += "Host: %s:%s\r\n" % (self.config.address, self.config.port)
        if self.config.ntrip_v2:
            mount_point_request += "Ntrip-Version: Ntrip/2.0\r\n"
        mount_point_request += "\r\n"
        return bytes(mount_point_request, 'ascii')

    def connect_to_server(self):
        """
        Connects to the server and establishes a connection with the mount point. This involves creating a socket, sending
        a request to the server, and parsing the server's response to verify a successful connection.
        """
        # Set up a connection with the mount point
        self.socket = socket.create_connection((self.config.address, self.config.port))
        self.socket.sendall(self.get_mount_point_for_request())

        # Parse the response to the connection request
        response_size_bytes = 4096
        response_lines = self.socket.recv(response_size_bytes).decode('utf-8').split("\r\n")
        check_connection_response(response_lines[0])

    def get_ephemeris_loop(self):
        """
        Parses and updates Galileo Ephemeris data in a loop using the RTCM reader.

        The function indefinitely reads RTCM messages from a connected socket,
        checks if the message corresponds to a Galileo Ephemeris type, retrieves
        necessary information such as the satellite ID and Galileo System Time (GST),
        and updates the ephemeris data for the satellite if newer information is received.
        """
        # Create the RTCM Reader using the connected socket
        reader = pyrtcm.RTCMReader(self.socket, quitonerror=2)

        # Loop over the data parsed by the reader (which has an overloaded __next__ function)
        for (_, parsed_data) in reader:
            # Check if the message number (DF002) is that of a Galileo Ephemeris message
            if parsed_data.DF002 == constants.DF_GALILEO_EPH:
                # Get the satellite ID and the Galileo System Time (GST) of the ephemeris
                satID = parsed_data.DF252
                gst = parsed_data.DF289 * constants.SEC_IN_WEEK + parsed_data.DF293

                # If the ephemeris is newer than the current one, update the ephemeris by mapping the received data
                if gst > self.ephem[satID - 1].gst:
                    self.ephem[satID - 1].map_to_ephemeris(parsed_data)
