from typing import Tuple

import numpy as np
from numpy import radians, arccos, sin, cos, sum as np_sum, isnan

from float_array import FloatArray
from hirschberg import np_hirschberg

DISTANCE_FACTOR = np.float64(0.001)
EARTH_RADIUS = np.float64(6371e3)
MAX_POINT_DISTANCE = 3000.0


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


def np_geo_distance_track(
    source: FloatArray,
    target: FloatArray,
    factor: np.float64 = DISTANCE_FACTOR,
) -> np.float64:
    """
    Compares two tracks point by point and returns a total difference between them.
    The distance from start is also considered but may be tuned with factor parameter
    (say, set to 0).

    :param source: the source track or route
    :param target: the target track
    :param factor: distance from the start multiplier
    :return:
    """
    source_lat_radians, source_lon_radians = radians(source.T[0:2].astype(float))
    target_lat_radians, target_lon_radians = radians(target.T[0:2].astype(float))

    distance_shift: FloatArray = abs(target.T[3] - source.T[3]) * factor
    difference: FloatArray = distance_shift + EARTH_RADIUS * arccos(
        sin(source_lat_radians) * sin(target_lat_radians)
        + cos(source_lat_radians)
        * cos(target_lat_radians)
        * cos(target_lon_radians - source_lon_radians)
    )
    np.nan_to_num(difference, copy=False, nan=MAX_POINT_DISTANCE)
    return np_sum(difference[~isnan(difference)])


def np_align_track_to_route(
    route: FloatArray, track: FloatArray
) -> Tuple[float, FloatArray]:
    """
    Compare route and track sequences.

    :param route: original sequence to compare to
    :param track: GPS recorded points
    :return: a tuple (score, points)

    Use the score to decide if the match is good enough.
    Points are in form of array [latitude, longitude, timestamp, distance] or None
    """
    # logging.info(f"route len {len(route)} / track len {len(track)}")
    first, second, distance = np_hirschberg(
        route,
        track,
        deletion_cost=-MAX_POINT_DISTANCE,
        insertion_cost=0,
        cost_function=np_geo_distance,
    )
    mask = first.all(axis=1) != None  # noqa: E711
    second = second[mask]
    # second = second[second.all(axis=1) != None]  # noqa: E711
    return distance, second.astype(float)
