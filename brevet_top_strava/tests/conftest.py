import functools
import pathlib
from datetime import datetime
from itertools import accumulate
from typing import Tuple, List, Iterable

import gpxpy
import pytest

from brevet_top_plot_a_route import geo_distance, RoutePoint, CheckPoint, attach_labels


def safe_distance(
    source: Tuple[float, float, float, float], target: Tuple[float, float, float, float]
) -> Tuple[float, float, float, float]:
    try:
        distance = geo_distance(source[0], source[1], target[0], target[1])
        return target[0:3] + (source[3] + distance,)
    except ValueError:
        return source


def add_distance(point_generator):
    @functools.wraps(point_generator)
    def wrapper_decorator(*args, **kwargs):
        points = point_generator(*args, **kwargs)
        first_point: Tuple[float, float, float, float] = next(points)

        yield accumulate(
            points,
            func=safe_distance,
            initial=first_point,
        )

    return wrapper_decorator


@pytest.fixture
def gpx_track_data(track_name: str) -> gpxpy.gpx.GPX:
    file_path = pathlib.Path(__file__).parent.absolute() / "files" / track_name
    return gpxpy.parse(file_path.open(encoding="UTF-8"))


@pytest.fixture
def gpx_route_data(route_name: str) -> gpxpy.gpx.GPX:
    file_path = pathlib.Path(__file__).parent.absolute() / "files" / route_name
    return gpxpy.parse(file_path.open(encoding="UTF-8"))


@pytest.fixture
def gpx_track_point(
    gpx_track_data: gpxpy.gpx.GPX,
) -> Iterable[Tuple[float, float, float, float]]:
    return [
        (
            point.latitude,
            point.longitude,
            point.time.timestamp() if point.time else 0.0,
            float(point.comment or 0),
        )
        for track in gpx_track_data.tracks
        for segment in track.segments
        for point in segment.points
    ]


@pytest.fixture
@add_distance
def gpx_route_point(
    gpx_route_data: gpxpy.gpx.GPX,
) -> Iterable[Tuple[float, float, float, float]]:
    for track in gpx_route_data.tracks:
        for segment in track.segments:
            for point in segment.points:
                yield (
                    point.latitude,
                    point.longitude,
                    point.time.timestamp() if point.time else 0.0,
                    0.0,
                )


@pytest.fixture
def gpx_waypoint(
    gpx_route_data: gpxpy.gpx.GPX,
) -> List[Tuple[float, float, str, float]]:
    return [
        (wp.latitude, wp.longitude, wp.name, float(wp.source or 0))
        for wp in gpx_route_data.waypoints
    ]


@pytest.fixture
def get_track(
    gpx_track_point: Iterable[Tuple[float, float, float, float]]
) -> List[Tuple[float, float, float, float]]:
    return list(gpx_track_point)


@pytest.fixture
def get_route(
    gpx_route_point: Iterable[Tuple[float, float, float, float]]
) -> List[Tuple[float, float, float, float]]:
    return list(gpx_route_point)


@pytest.fixture
def route_points(
    get_route: List[Tuple[float, float, float, float]]
) -> List[RoutePoint]:
    return [RoutePoint(lat=point[0], lng=point[1]) for point in get_route]


@pytest.fixture
def get_checkpoints(
    get_route: List[Tuple[float, float, float, float]],
    gpx_waypoint: List[Tuple[float, float, str, float]],
) -> List[Tuple[float, float, float, float]]:
    checkpoints = [
        CheckPoint(lat=wp[0], lng=wp[1], name=wp[2], distance=wp[3])
        for wp in gpx_waypoint
    ]

    attach_labels(checkpoints, get_route)

    double: List[Tuple[float, float, float, float]] = [
        (cp.lat, cp.lng, 0.0, cp.distance * 1000) for cp in checkpoints for _ in (0, 1)
    ]
    double.pop()
    double.pop(0)
    return double


def pytest_assertrepr_compare(op, left, right):
    if isinstance(left, datetime) and isinstance(right, datetime) and op == "<=":
        return [
            "Datetime comparison has failed:",
            f"    {left.isoformat()} <= {right.isoformat()}",
        ]
