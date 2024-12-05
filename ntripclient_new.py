import base64
import sys

from pyrtcm import RTCMReader
import constants
import socket
import ssl


def check_connection_response(line):
    # These are the expected statuses
    if "ICY 200 OK" in line or "HTTP/1.0 200 OK" in line or "HTTP/1.1 200 OK" in line:
        return

    # If there was no OK, throw an error with the line
    sys.stderr.write(line + "\n")

    # Also return human-readable error in case the mount point isn't found
    if "SOURCETABLE" in line:
        sys.stderr.write("Mount point does not exist\n")

    # Exit the script if we reach this point, as no OK was found then
    sys.exit(1)


class NtripClientNew(object):
    def __init__(self,
                 ephem,
                 azelev):
        self.ephem = ephem
        self.azelev = azelev
        self.socket = None

        self.ssl = True
        self.connect_to_server()

    def get_mount_point_request(self):
        user_name_base64 = base64.b64encode(bytes(constants.USER_NAME, 'utf-8')).decode("utf-8")
        mount_point_request = "GET /{0} HTTP/1.1\r\nUser-Agent: {1}\r\nAuthorization: Basic {2}\r\n".format(
            constants.MOUNTPOINT, constants.SOFTWARE_NAME, user_name_base64)
        if constants.INCLUDE_HOST_HEADER | constants.USE_NTRIP_V2:
            mount_point_request += "Host: %s:%s\r\n" % (constants.CASTER_URL, constants.CASTER_PORT)
        if constants.USE_NTRIP_V2:
            mount_point_request += "Ntrip-Version: Ntrip/2.0\r\n"
        mount_point_request += "\r\n"
        return bytes(mount_point_request, 'ascii')

    def connect_to_server(self):
        # Set up a connection with the mount point
        self.socket = socket.create_connection((constants.CASTER_URL, constants.CASTER_PORT))

        # TODO: Add and test SSL here
        # if self.ssl:
        #   context = ssl.create_default_context()
        #  context.wrap_socket(self.socket)

        self.socket.sendall(self.get_mount_point_request())

        # Parse the response to the connection request
        response_size_bytes = 4096
        response_lines = self.socket.recv(response_size_bytes).decode('utf-8').split("\r\n")
        check_connection_response(response_lines[0])

    def get_ephemeris_loop(self):
        # Create the RTCM Reader using the connected socket
        reader = RTCMReader(self.socket, quitonerror=2)

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
