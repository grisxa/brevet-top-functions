import pytest
from google.cloud.firestore_v1 import GeoPoint

from brevet_top_gcp_utils import firestore_to_track_point


@pytest.mark.parametrize(
    ("data", "point"),
    [
        ({}, (0, 0, 0, 0)),
        ({"distance": 0}, (0, 0, 0, 0)),
        (
            {"distance": 12.3, "coordinates": GeoPoint(60, 30)},
            (60, 30, 0, 12.3),
        ),
    ],
)
def test_firestore_to_track_point(data: dict, point: tuple[float, float, float, float]):
    assert firestore_to_track_point(data) == point
