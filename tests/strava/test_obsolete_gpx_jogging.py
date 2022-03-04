import pathlib
from typing import List

import gpxpy
import pytest
from gpxpy import gpx

from strava.obsolete import align_track_to_route
from strava.track_point import StravaTrackPoint


@pytest.fixture
def gpx_data() -> gpx.GPX:
    file_path = pathlib.Path(__file__).parent / "files" / "jogging.gpx"
    return gpxpy.parse(file_path.open(encoding="UTF-8"))


def x_test_gpx_jogging(
    gpx_route: List[StravaTrackPoint], gpx_track: List[StravaTrackPoint]
):
    cost, reduced = align_track_to_route(gpx_route, gpx_track)

    assert round(cost, 3) == -324.535
