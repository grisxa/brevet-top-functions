from typing import List
from unittest.mock import patch

import pytest

from plot_a_route import find_checkpoints, RoutePoint, CheckPoint


@pytest.fixture()
def data_good():
    return {"RouteData": '[{"lat": 1, "lng": 2}]'}


def test_find_checkpoints_empty():
    # verification
    assert find_checkpoints([]) == []


def test_find_checkpoints_single():
    # setup
    source: List[RoutePoint] = [RoutePoint(lat=1, lng=2)]
    expected: List[CheckPoint] = [CheckPoint(lat=1, lng=2, name="Start")]

    # verification
    assert find_checkpoints(source) == expected


@patch("plot_a_route.find_labels", return_value=[])
def test_find_checkpoints_many(mock_find_labels):
    # setup
    source: List[RoutePoint] = [
        RoutePoint(lat=1, lng=2),
        RoutePoint(lat=3, lng=4, dir="CP1", distance=1234567),
        RoutePoint(lat=5, lng=6),
        RoutePoint(lat=7, lng=8, labtxt="CP2", distance=2345678),
        RoutePoint(lat=9, lng=0),
        RoutePoint(lat=2, lng=3, labtxt="home", distance=3456789),
    ]
    expected: List[CheckPoint] = [
        CheckPoint(lat=1, lng=2, name="Start"),
        CheckPoint(lat=3, lng=4, name="CP1", distance=1235),
        CheckPoint(lat=7, lng=8, name="CP2", distance=2346),
    ]

    # action
    result = find_checkpoints(source)

    # verification
    assert result == expected
    mock_find_labels.assert_called_once()
