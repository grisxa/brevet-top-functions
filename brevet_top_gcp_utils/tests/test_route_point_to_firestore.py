import pytest
from google.cloud.firestore_v1 import GeoPoint

from brevet_top_gcp_utils import route_point_to_firestore
from brevet_top_plot_a_route import RoutePoint


@pytest.mark.parametrize(
    ("point", "result"),
    [
        (
            RoutePoint(lat=1, lng=2),
            {
                "coordinates": GeoPoint(latitude=1, longitude=2),
                "distance": 0,
            },
        ),
        (
            RoutePoint(lat=3, lng=4, dir="CP1", distance=123),
            {
                "coordinates": GeoPoint(latitude=3, longitude=4),
                "distance": 123,
            },
        ),
    ],
)
def test_route_point_to_firestore(point: RoutePoint, result: dict):
    assert route_point_to_firestore(point) == result
