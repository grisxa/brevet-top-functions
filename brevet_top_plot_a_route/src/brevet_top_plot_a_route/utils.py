import logging
from copy import deepcopy
from itertools import compress
from typing import List, Optional

import numpy as np
import requests
from rdp import rdp

from .check_point import CheckPoint
from .route_point import RoutePoint

ROUTE_PREFIX: str = "https://www.plotaroute.com/route/"

ROUTE_SIMPLIFY_FACTOR = 0.001
ROUTE_SIMPLIFY_DIVIDER = (
    20000.0  # used as (sqrt(len) / divider) to reduce to ~100 points
)


def get_map_id_from_url(url: Optional[str]) -> Optional[int]:
    """
    Extract map ID from the map URL

    :param url: a link to the map
    :return: the map ID
    """
    if not url:
        return None
    if not url.startswith(ROUTE_PREFIX):
        return None
    return int(float(url.removeprefix(ROUTE_PREFIX).split("?")[0]))


def download_data(route_url: str) -> dict:
    """
    Generic HTTP request.

    :param route_url: a link to GET
    :return: JSON with results
    """
    try:
        req = requests.get(route_url)
        req.raise_for_status()
        return req.json()
    except Exception as error:
        logging.error(f"HTTP error: {error}")
        raise


def route_down_sample_factor(source: int, target: int) -> float:
    """
    Simple Ramer-Douglas-Peucker (rdp) epsilon calculator based on point number ratio.
    The target sequence is expected to be reduced by the rdp previously.

    :param source: the source number of points
    :param target: the target number of points
    :return: down-sampling factor (epsilon)
    """
    factor = 0.0002 * target / source + target / 50000
    logging.info(f"Route down-sampling factor for {source} / {target} is {factor}")
    return factor


def simplify_route(
        points: List[RoutePoint], factor: float = ROUTE_SIMPLIFY_FACTOR
) -> List[RoutePoint]:
    """
    Reduce number of route points with Ramer-Douglas-Peucker algorithm.

    :param points: a source list of points as [RoutePoint]
    :param factor: optional down-sample factor (epsilon in RDP algorithm)
    :return: reduced list of points as [RoutePoint]
    """
    coordinates: List[List[float]] = [[p.lat or 0, p.lng or 0] for p in points]
    simple_mask = rdp(coordinates, factor, algo="iter", return_mask=True)
    return list(compress(points, simple_mask))


# noinspection NonAsciiCharacters
def geo_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Generic geo distance calculation

    :param lat1: Latitude of the first point
    :param lon1: Longitude of the first point
    :param lat2: Latitude of the second point
    :param lon2: Longitude of the second point
    :return: A distance between the points
    """

    if lat1 == lat2 and lon1 == lon2:
        return 0

    φ1 = lat1 * np.pi / 180
    φ2 = lat2 * np.pi / 180
    # noinspection PyPep8Naming
    Δλ = (lon2 - lon1) * np.pi / 180
    radius = 6371e3
    # May raise [ValueError: math domain error] if points are way too close
    distance = radius * np.arccos(
        np.sin(φ1) * np.sin(φ2) + np.cos(φ1) * np.cos(φ2) * np.cos(Δλ)
    )
    if np.isnan(distance):
        # emulate math package
        raise ValueError("math domain error")
    return distance


if __name__ == "__main__":
    pass
