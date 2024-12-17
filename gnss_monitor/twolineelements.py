import csv
import warnings

import requests
from skyfield.api import load
from skyfield.sgp4lib import EarthSatellite
from bs4 import BeautifulSoup

class TwoLineElements(object):
    def __init__(self):
        max_days = 10.0  # download again once 7 days old
        name = 'galileo_tle.csv'  # custom filename, not 'gp.php'

        base = 'https://celestrak.org/NORAD/elements/gp.php'
        url = base + '?GROUP=galileo&FORMAT=csv'


        if not load.exists(name) or load.days_old(name) >= max_days:
            load.download(url, filename=name)

        with load.open(name, mode='r') as f:
            data = list(csv.DictReader(f))

        ts = load.timescale()
        self.sats = [EarthSatellite.from_omm(ts, fields) for fields in data]
        self.gsat_to_svid_map = {}

        self.get_gsat_to_svid_map()

    def get_gsat_to_svid_map(self):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'}
        res = requests.get("https://www.gsc-europa.eu/system-service-status/constellation-information", headers=headers, timeout=20)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            info_table = soup.find("table")  # Finds the first table on the page
            rows = info_table.find_all("tr")
            for row in rows[1:]:
                cells = row.find_all("td")
                if len(cells) >= 2:
                    self.gsat_to_svid_map[cells[0].text.strip()] = int(cells[1].text.strip()[1:])# Ensure the row has enough columns

    def set_tle(self, ephemeris):
        for sat in self.sats:
            gsat = sat.name[:8]
            try:
                sv_id = self.gsat_to_svid_map[gsat]
                ephemeris[sv_id-1].tle = sat
            except KeyError:
                warnings.warn("Unknown satellite name {0} in TLE, skipping".format(gsat))
