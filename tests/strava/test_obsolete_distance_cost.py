import pytest

from strava.track_point import StravaTrackPoint
from strava.obsolete import distance_cost


@pytest.mark.parametrize(
    ("point_a", "point_b", "cost"),
    [
        (
            StravaTrackPoint(lat=60.123, lng=30.123, distance=0),
            StravaTrackPoint(lat=60.124, lng=30.124, distance=0),
            124.23,
        ),
        (
            StravaTrackPoint(lat=60.123, lng=30.123, distance=100),
            StravaTrackPoint(lat=60.124, lng=30.124, distance=200),
            124.33,
        ),
        (
            StravaTrackPoint(lat=60.12, lng=30.12, distance=1000),
            StravaTrackPoint(lat=60.13, lng=30.13, distance=2000),
            1243.26,
        ),
        (
            StravaTrackPoint(lat=60, lng=20, distance=150),
            StravaTrackPoint(lat=50, lng=20, distance=0),
            1111949.42,
        ),
        (
            StravaTrackPoint(lat=60, lng=20, distance=150),
            StravaTrackPoint(lat=60, lng=20, distance=0),
            0.15,
        ),
        (
            StravaTrackPoint(lat=60, lng=20, distance=150),
            StravaTrackPoint(lat=60, lng=20, distance=150),
            0,
        ),
        (
            StravaTrackPoint(lat=60, lng=20, distance=150),
            StravaTrackPoint(lat=60, lng=20, distance=1150),
            1.0,
        ),
        (
            StravaTrackPoint(lat=60, lng=20, distance=150),
            StravaTrackPoint(lat=60, lng=30, distance=200),
            555445.18,
        ),
        (
            StravaTrackPoint(lat=60, lng=20, distance=150),
            StravaTrackPoint(lat=0, lng=0, distance=0),
            6891381.27,
        ),
    ],
)
def test_distance_cost(
    point_a: StravaTrackPoint, point_b: StravaTrackPoint, cost: float
):
    assert round(distance_cost(point_a, point_b), 2) == cost
