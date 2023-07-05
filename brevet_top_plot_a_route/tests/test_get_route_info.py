import json
from unittest.mock import patch, call

import pytest

from brevet_top_plot_a_route import get_route_info, RouteNotFound, route_down_sample_factor
from brevet_top_plot_a_route.check_point import CheckPoint
from brevet_top_plot_a_route.route_point import RoutePoint

mock_track = [
    {
        "lat": 60.027579,
        "lng": 30.296469,
        "dir": "Start on ",
        "symlabs": [
            {
                "lat": 60.0164379,
                "lng": 30.2789855,
                "lab": {
                    "labtxt": "CP2: shop",
                },
            }
        ],
    },
    {"lat": 60.027579, "lng": 30.296469},
    {
        "lat": 60.027572,
        "lng": 30.296473,
    },
    {
        "lat": 60.025528,
        "lng": 30.297576,
        "dir": "Turn right",
    },
    {
        "lat": 60.02288,
        "lng": 30.282106,
        "dir": "CP1: left",
    },
]

mock_download = {
    "RouteData": json.dumps(mock_track),
    "RouteID": 123,
    "RouteName": "Jogging",
    "Distance": 3030.405119607894,
    "Creator": "incognito",
    "CreatorID": 123,
}

mock_download_error = {
    "Error": "Invalid Route ID",
}

mock_last_point = RoutePoint(lat=2, lng=3, labtxt="home", distance=3456789)

mock_route = [
    RoutePoint(lat=1, lng=2),
    RoutePoint(lat=3, lng=4, dir="CP1", distance=1234567),
    RoutePoint(lat=5, lng=6),
    RoutePoint(lat=7, lng=8, labtxt="CP2", distance=2345678),
    RoutePoint(lat=9, lng=0),
    mock_last_point,
]

mock_checkpoints = [
    CheckPoint(lat=1, lng=2, name="Start"),
    CheckPoint(lat=3, lng=4, name="CP1", distance=1235),
    CheckPoint(lat=7, lng=8, name="CP2", distance=2346),
]


@patch("brevet_top_plot_a_route.add_last_checkpoint")
@patch("brevet_top_plot_a_route.find_checkpoints", return_value=mock_checkpoints)
@patch("brevet_top_plot_a_route.simplify_route", return_value=mock_route)
@patch("brevet_top_plot_a_route.route_down_sample_factor", return_value=0.1)
@patch("brevet_top_plot_a_route.convert_route_points", return_value=mock_route)
@patch("brevet_top_plot_a_route.download_data", return_value=mock_download)
def test_get_route_info(
    mock_downloader,
    mock_converter,
    mock_factor,
    mock_simplifier,
    mock_finder,
    mock_last,
):
    # setup
    expected = {
        "checkpoints": mock_checkpoints,
        "name": "Jogging",
        "length": 3,
        "mapUrl": "https://www.plotaroute.com/route/123",
        "track": mock_route,
        "short_track": mock_route,
    }

    # action
    info = get_route_info("https://www.plotaroute.com/route/123")

    # verification
    mock_downloader.assert_called_once_with(
        "https://www.plotaroute.com/get_route.asp?RouteID=123.0"
    )
    mock_converter.assert_called_once_with(mock_track)
    mock_factor.assert_called_once_with(6, 6)
    mock_simplifier.assert_has_calls([call(mock_route), call(mock_route, factor=0.1)])
    mock_finder.assert_called_once_with(mock_route)
    mock_last.assert_called_once_with(mock_checkpoints, mock_last_point)
    assert info == expected


@patch("brevet_top_plot_a_route.convert_route_points")
@patch("brevet_top_plot_a_route.download_data", return_value=mock_download_error)
def test_get_route_info_exception(mock_downloader, mock_converter):
    # action
    with pytest.raises(RouteNotFound) as error:
        get_route_info("https://www.plotaroute.com/route/123")

    # verification
    assert "Invalid Route ID" in str(error)
    mock_downloader.assert_called_once_with(
        "https://www.plotaroute.com/get_route.asp?RouteID=123.0"
    )
    mock_converter.assert_not_called()


@patch("brevet_top_plot_a_route.convert_route_points", return_value=[])
@patch("brevet_top_plot_a_route.download_data", return_value=mock_download)
def test_get_route_info_empty(mock_downloader, mock_converter):
    # action
    info = get_route_info("https://www.plotaroute.com/route/123")

    # verification
    mock_downloader.assert_called_once_with(
        "https://www.plotaroute.com/get_route.asp?RouteID=123.0"
    )
    mock_converter.assert_called_once_with(mock_track)
    assert info is None


@pytest.mark.parametrize(
    ("size", "length", "factor"),
    [
        (8000, 500, 0.01001),
        (8000, 300, 0.00601),
        (8000, 200, 0.004),
        (4000, 300, 0.00602),
        (4000, 200, 0.00401),
        (2000, 200, 0.00402),
        (2000, 100, 0.00201),
        (2000, 50, 0.00101),
        (1000, 100, 0.00202),
        (1000, 50, 0.00101),
        (500, 100, 0.00204),
        (500, 50, 0.00102),
        (200, 100, 0.0021),
        (200, 50, 0.00105),
        (100, 50, 0.0011),
    ],
)
def test_route_down_sample_factor(size: int, length: int, factor: float):
    assert round(route_down_sample_factor(size, length), 5) == factor
