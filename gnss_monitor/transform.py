from math import sqrt, sin, cos, hypot, atan2, pi

from gnss_monitor import constants


def lla2ecef(lat, lon, alt):
    # Source: https://github.com/sglvladi/MATLAB/blob/master/ecef.py

    lat *= constants.DEG_TO_RAD
    lon *= constants.DEG_TO_RAD

    n = constants.WGS84_SEMI_MAJOR_AXIS / sqrt(1 - constants.WGS84_FIRST_ECCENTRICITY_SQUARED * sin(lat) * sin(lat))
    x = (n + alt) * cos(lat) * cos(lon)
    y = (n + alt) * cos(lat) * sin(lon)
    z = ((1 - constants.WGS84_FIRST_ECCENTRICITY_SQUARED) * n + alt) * sin(lat)
    return x, y, z


def geodetic2aer(x, y, z, lat0, lon0, alt0):
    x0, y0, z0 = lla2ecef(lat0, lon0, alt0)
    e, n, u = ecef2enu(x - x0, y - y0, z - z0, lat0, lon0)

    r = hypot(e, n)
    slant_range = hypot(r, u)
    elev = atan2(u, r) * constants.RAD_TO_DEG
    az = atan2(e, n) % (2 * pi) * constants.RAD_TO_DEG

    return az, elev, slant_range


def ecef2enu(u, v, w, lat0, lon0):

    lat0 *= constants.DEG_TO_RAD
    lon0 *= constants.DEG_TO_RAD

    t = cos(lon0) * u + sin(lon0) * v
    east = -sin(lon0) * u + cos(lon0) * v
    up = cos(lat0) * t + sin(lat0) * w
    north = -sin(lat0) * t + cos(lat0) * w
    return east, north, up
