import csv
import warnings

import requests
from bs4 import BeautifulSoup
from skyfield.api import load
from skyfield.sgp4lib import EarthSatellite

from gnss_monitor import constants


class TwoLineElements(object):
    """
    Handles fetching, processing, and mapping of Two Line Element (TLE) data for Galileo satellites.

    This class is utilized to download TLE data for Galileo satellites from relevant online
    sources, process the data, and associate satellite identifiers with corresponding SV IDs.

    Attributes:
        sats (list[EarthSatellite]): A list of EarthSatellite objects created from TLE data.
        gsat_to_svid_map (dict): A dictionary mapping GSAT satellite names to SVIDs.
    """

    def __init__(self):
        """
        Initialization function responsible for downloading, parsing, and using Galileo satellite Two-Line Element (TLE)
        data in CSV format. The class fetches data from CelesTrak if the local file does not exist
        or is outdated. Loaded data is used to create EarthSatellite objects and populate a mapping
        between GSAT identifiers and SVID values.
        """
        name = 'galileo_tle.csv'  # custom filename, not 'gp.php'

        base = 'https://celestrak.org/NORAD/elements/gp.php'
        url = base + '?GROUP=galileo&FORMAT=csv'

        if not load.exists(name) or load.days_old(name) >= constants.TLE_MAX_AGE:
            load.download(url, filename=name)

        with load.open(name, mode='r') as f:
            data = list(csv.DictReader(f))

        ts = load.timescale()
        self.sats = [EarthSatellite.from_omm(ts, fields) for fields in data]
        self.gsat_to_svid_map = {}

        self.get_gsat_to_svid_map()

    def get_gsat_to_svid_map(self):
        """
        Fetches the GSAT to SV ID mapping from EUSPA's European GNSS Service Centre (GSC).

        This function retrieves data from the GSC about the Galileo constellation information.
        It parses the HTML response to extract the mapping of GSAT identifiers to their corresponding SV IDs.
        The extracted mapping is stored in the `gsat_to_svid_map` attribute as a dictionary, where keys represent
        GSAT identifiers (as strings) and values represent SVIDs (as integers).

        Raises:
            RequestException: If there is an issue with making the HTTP request.
            AttributeError: If expected HTML elements are not found in the response or parsed structure.
            ValueError: If SV IDs values cannot be correctly parsed to integers, or if data is improperly formatted.
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'}
        res = requests.get("https://www.gsc-europa.eu/system-service-status/constellation-information", headers=headers,
                           timeout=20)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            info_table = soup.find("table")  # Finds the first table on the page
            rows = info_table.find_all("tr")
            for row in rows[1:]:
                cells = row.find_all("td")
                if len(cells) >= 2:
                    self.gsat_to_svid_map[cells[0].text.strip()] = int(
                        cells[1].text.strip()[1:])  # Ensure the row has enough columns

    def set_tle(self, ephemeris):
        """
        Sets the TLE (Two-Line Elements) values in the given ephemeris data for satellites by
        mapping satellite names to corresponding IDs. If a satellite name cannot be mapped,
        a warning is issued indicating the unmapped satellite.

        Parameters:
            ephemeris (list[SatEphemeris]): A list containing satellite ephemeris data.
        """
        for sat in self.sats:
            gsat = sat.name[:8]
            try:
                sv_id = self.gsat_to_svid_map[gsat]
                ephemeris[sv_id - 1].tle = sat
            except KeyError:
                warnings.warn("Unknown satellite name {0} in TLE, skipping".format(gsat))
