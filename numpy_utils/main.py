import numpy as np
from numpy import radians, arccos, sin, cos

from numpy_utils import FloatArray

DISTANCE_FACTOR = np.float64(0.001)
EARTH_RADIUS = np.float64(6371e3)


def np_geo_distance(
    point: FloatArray,
    track: FloatArray,
    factor: np.float64 = DISTANCE_FACTOR,
) -> FloatArray:
    point_latitude, point_longitude = radians(point[0:2]).astype(np.float64)
    latitude_radians, longitude_radians = radians(track.T[0:2]).astype(np.float64)

    distance_shift = abs(track.T[3] - point[3]) * factor
    return distance_shift + EARTH_RADIUS * arccos(
        sin(point_latitude) * sin(latitude_radians)
        + cos(point_latitude)
        * cos(latitude_radians)
        * cos(longitude_radians - point_longitude)
    )
