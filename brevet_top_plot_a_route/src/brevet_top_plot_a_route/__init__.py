import json
import logging
from copy import deepcopy
from itertools import accumulate, compress
from typing import Optional, List, Tuple

import numpy as np
import requests
from rdp import rdp

from brevet_top_numpy_utils import FloatArray, np_geo_distance
from .check_point import CheckPoint
from .exceptions import RouteNotFound
from .route_point import RoutePoint

ROUTE_PREFIX: str = "https://www.plotaroute.com/route/"
API_PREFIX: str = "https://www.plotaroute.com/get_route.asp"
ROUTE_SIMPLIFY_FACTOR = 0.001
ROUTE_SIMPLIFY_DIVIDER = (
    20000.0  # used as (sqrt(len) / divider) to reduce to ~100 points
)
EPILOG_MAX_LENGTH = 0.5  # km


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


def get_route_info(url: str) -> Optional[dict]:
    """
    Download the route details using Plot A Route API.

    :param url: original route link
    :return: a dict with the route details or None
    """
    # allow ids like 12345.6 - the server is rounding to int
    map_id: float = float(url.removeprefix(ROUTE_PREFIX).split("?")[0])

    route_data: dict = download_data(f"{API_PREFIX}?RouteID={map_id}")
    if "Error" in route_data:
        raise RouteNotFound(route_data["Error"])

    track: List[RoutePoint] = convert_route_points(get_route_data(route_data))

    if len(track) < 1:
        logging.error(f"Empty route for {url}")
        return None

    distance: float = route_data.get("Distance", 0)
    name: str = route_data.get("RouteName", "unknown")

    route = simplify_route(track)
    short_route = simplify_route(
        track, factor=route_down_sample_factor(len(track), len(route))
    )
    logging.info(
        f"The route has been simplified from {len(track)}"
        f" points to {len(route)} / {len(short_route)}"
    )

    checkpoints: List[CheckPoint] = find_checkpoints(track)
    add_last_checkpoint(checkpoints, track[-1])

    info = {
        "checkpoints": checkpoints,
        "name": name,
        "length": round(distance / 1000),
        "mapUrl": url,
        "track": route,
        "short_track": short_route,
    }
    return info


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


def find_checkpoints(route_points: List[RoutePoint]) -> List[CheckPoint]:
    """
    Trace the route and find checkpoints.

    :param route_points: a list of route points
    :return: a list of checkpoints
    """
    if len(route_points) == 0:
        return []
    checkpoints: List[CheckPoint] = []
    labels: List[CheckPoint] = []

    first_point: CheckPoint = copy_checkpoint(route_points.pop(0))

    # search for symlabs checkpoints
    labels.extend(label for label in find_labels(first_point) if label.is_control())

    # rename the first point
    first_point.fix_name("Start")
    checkpoints.append(first_point)

    # search along other route points
    for point in route_points:
        if point.is_control():
            checkpoints.append(copy_checkpoint(point))

    attach_labels(labels, [(p.lat, p.lng, 0, p.distance) for p in route_points])

    checkpoints.extend(labels)
    return checkpoints


def attach_labels(
    labels: List[CheckPoint], points: List[Tuple[float, float, float, float]]
):
    """
    Find best matching route points and update distance from the route start.

    :param labels: a list of CheckPoint
    :param points: a list of route points to compare
    """
    for label in labels:
        step_away: FloatArray = np_geo_distance(
            np.array([label.lat, label.lng, 0.0, 0.0], dtype=np.float64),
            np.array(points, dtype=np.float64),
        )
        offset: int = np.argmin(step_away)  # noqa: E711
        if not label.distance:
            label.distance = round(points[offset][3] / 1000)


def copy_checkpoint(point: RoutePoint) -> CheckPoint:
    """
    Convert a RoutePoint to a CheckPoint and distance units from m to km.

    :param point: a RoutePoint
    :return: a new CheckPoint
    """
    new_point = deepcopy(point.__dict__)
    new_point["distance"] = round(point.distance / 1000)
    return CheckPoint(**new_point)


def find_labels(point: CheckPoint) -> List[CheckPoint]:
    """
    Find checkpoints defined in symlabs/lab/labtxt tags.

    :param point: a CheckPoint to review
    :return: a list of new CheckPoints
    """
    return [
        CheckPoint(**label, labtxt=label.get("lab", {}).get("labtxt"))
        for label in point.__dict__.get("symlabs", [])
    ]


def add_last_checkpoint(checkpoints: List[CheckPoint], finish: RoutePoint = None):
    """
    Compare the route and checkpoint list and add a new CheckPoint if the route is longer.

    :param checkpoints: a list of checkpoints
    :param finish: the last route point
    """
    # add the last point from the route if too far from the last control
    if (
        len(checkpoints) > 0
        and finish is not None
        and finish.distance / 1000 > checkpoints[-1].distance + EPILOG_MAX_LENGTH
    ):
        checkpoint = copy_checkpoint(finish)
        checkpoint.fix_name("End")
        checkpoints.append(checkpoint)


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


def convert_route_points(points: List[dict]) -> List[RoutePoint]:
    """
    Transform a route from Plot A Route format to internal one adding distance.

    :param points: a list of source route points as [dict]
    :return: a list of route point as [RoutePoint]
    """
    if len(points) == 0:
        return []
    first_point: RoutePoint = RoutePoint(**points.pop(0), distance=0)

    return list(accumulate(points, build_point, initial=first_point))


def build_point(route: RoutePoint, point: dict) -> RoutePoint:
    try:
        distance = geo_distance(
            route.lat,
            route.lng,
            point.get("lat", 0.0),
            point.get("lng", 0.0),
        )
        return RoutePoint(**point, distance=route.distance + distance)
    except ValueError:
        # points are way too close, skip one
        return route


def get_route_data(data: dict) -> List[dict]:
    return json.loads(data.get("RouteData", "[]"))


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
