from math import sqrt, sin, cos, hypot, atan2, pi

from gnss_monitor import constants


def llh2ecef(lat, lon, h):
    """
    Converts geodetic coordinates (latitude, longitude, and altitude) to
    Earth-Centered, Earth-Fixed (ECEF) coordinates.

    This function transforms latitude, longitude, and altitude values based on
    the WGS84 ellipsoid parameters into the Cartesian ECEF coordinates. It
    takes into account the flattening of the Earth by using the ellipsoidal
    model defined by constants such as the semi-major axis and first
    eccentricity squared. Source: Subirana, J., Hernandez-Pajares, M., Zornoza, J.,
    European Space Agency, & Fletcher, K. (2013). GNSS Data Processing Volume 1.
    ESA Communications.

    Parameters:
        lat (float): The latitude in degrees.
        lon (float): The longitude in degrees.
        h (float): The height in meters above the WGS84 ellipsoid.

    Returns:
        tuple[float, float, float] The ECEF coordinates (x, y, z) in meters.
    """
    lat *= constants.DEG_TO_RAD
    lon *= constants.DEG_TO_RAD

    n = constants.WGS84_SEMI_MAJOR_AXIS / sqrt(1 - constants.WGS84_FIRST_ECCENTRICITY_SQUARED * sin(lat) ** 2)
    x = (n + h) * cos(lat) * cos(lon)
    y = (n + h) * cos(lat) * sin(lon)
    z = ((1 - constants.WGS84_FIRST_ECCENTRICITY_SQUARED) * n + h) * sin(lat)
    return x, y, z


def ecef2aer(x, y, z, lat0, lon0, alt0):
    """
    Converts Earth-Centered Earth-Fixed (ECEF) coordinates to Azimuth, Elevation,
    and Range (AER) coordinates with respect to a fixed observation point defined
    by latitude, longitude, and altitude.

    Parameters:
        x (float): X-coordinate of the target in ECEF (meters).
        y (float): Y-coordinate of the target in ECEF (meters).
        z (float): Z-coordinate of the target in ECEF (meters).
        lat0 (float): Latitude of the observation point in degrees.
        lon0 (float): Longitude of the observation point in degrees.
        alt0 (float): Altitude of the observation point in meters.

    Returns:
        tuple[float, float, float]: The (azimuth, elevation, range) in degrees and meters respectively.
    """
    x0, y0, z0 = llh2ecef(lat0, lon0, alt0)
    e, n, u = ecef2enu(x - x0, y - y0, z - z0, lat0, lon0)

    r = hypot(e, n)
    slant_range = hypot(r, u)
    elev = atan2(u, r) * constants.RAD_TO_DEG
    az = atan2(e, n) % (2 * pi) * constants.RAD_TO_DEG

    return az, elev, slant_range


def ecef2enu(dx, dy, dz, lat0, lon0):
    """
    Convert a position difference in ECEF coordinates to ENU (East-North-Up) local coordinates.

    Parameters:
        dx (float): The delta-x component of the vector in ECEF coordinates in meters.
        dy (float): The delta-y component of the vector in ECEF coordinates in meters.
        dz (float): The delta-zz-component of the vector in ECEF coordinates in meters.
        lat0 (float): Latitude of the reference point in degrees.
        lon0 (float): Longitude of the reference point in degrees.

    Returns:
            tuple[float, float, float]: The (east, north, up) in ENU coordinates
    """
    lat0 *= constants.DEG_TO_RAD
    lon0 *= constants.DEG_TO_RAD

    t = cos(lon0) * dx + sin(lon0) * dy
    east = -sin(lon0) * dx + cos(lon0) * dy
    up = cos(lat0) * t + sin(lat0) * dz
    north = -sin(lat0) * t + cos(lat0) * dz
    return east, north, up
