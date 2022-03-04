from typing import List

import pytest
from gpxpy import gpx

from strava.obsolete import align_track_to_route
from strava.track_point import StravaTrackPoint
from tests.strava.conftest import add_distance


@pytest.fixture
@add_distance
def gpx_track_plan(gpx_route_data: gpx.GPX):
    for track in gpx_route_data.tracks:
        for segment in track.segments:
            for point in segment.points:
                yield point


@pytest.mark.parametrize(
    ("file_name", "score"),
    [("акименко-4852246-5142976610.gpx", -3243.545)],  # -3243.5446552562885
)
def x_test_gpx_sosnovsky(
    file_name: str,
    score: float,
    gpx_track_plan: List[StravaTrackPoint],
    gpx_track: List[StravaTrackPoint],
):
    # for waypoint in gpx_data.waypoints:
    #    print('waypoint {0} -> ({1},{2})'
    #    .format(waypoint.name, waypoint.latitude, waypoint.longitude))

    cost, reduced = align_track_to_route(gpx_track_plan, gpx_track)

    assert round(cost, 3) == score
