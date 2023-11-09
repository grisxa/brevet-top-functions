from typing import List
from unittest.mock import patch

import pytest

from brevet_top_plot_a_route.check_point import CheckPoint
from brevet_top_plot_a_route.route import Route
from brevet_top_plot_a_route.route_point import RoutePoint


@pytest.fixture()
def mock_route():
    return Route()


def test_find_checkpoints_empty(mock_route):
    # action
    with pytest.raises(ValueError) as error:
        mock_route.find_checkpoints()

    # verification
    assert "Empty route" in str(error)


def test_find_checkpoints_single(mock_route):
    # setup
    mock_route.track = [RoutePoint(lat=1, lng=2)]
    expected: List[CheckPoint] = [CheckPoint(lat=1, lng=2, name="Start")]

    # action
    result = mock_route.find_checkpoints()

    # verification
    assert str(result) == str(expected)


@patch("brevet_top_plot_a_route.check_point.CheckPoint.find_labels", return_value=[])
def test_find_checkpoints_many(mock_find_labels, mock_route):
    # setup
    mock_route.track = [
        RoutePoint(lat=1, lng=2),
        RoutePoint(lat=3, lng=4, dir="CP1", distance=1234567),
        RoutePoint(lat=5, lng=6),
        RoutePoint(lat=7, lng=8, labtxt="CP2", distance=2345678),
        RoutePoint(lat=9, lng=0),
        RoutePoint(lat=2, lng=3, labtxt="home", distance=3456789),
    ]
    expected: List[CheckPoint] = [
        CheckPoint(lat=1, lng=2, name="Start"),
        CheckPoint(lat=3, lng=4, name="CP1", distance=1234567),
        CheckPoint(lat=7, lng=8, name="CP2", distance=2345678),
    ]

    # action
    result = mock_route.find_checkpoints()

    # verification
    assert str(result) == str(expected)
    mock_find_labels.assert_called_once()
