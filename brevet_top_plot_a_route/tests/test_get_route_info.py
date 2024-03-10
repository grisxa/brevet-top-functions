import json
from unittest.mock import patch, call

import pytest

from brevet_top_plot_a_route.check_point import CheckPoint
from brevet_top_plot_a_route.exceptions import RouteNotFound
from brevet_top_plot_a_route.main import get_route_info
from brevet_top_plot_a_route.route_point import RoutePoint
from brevet_top_plot_a_route.utils import route_down_sample_factor

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
        "dir": "CP1: village, turn left",
        "labtxt": "CP1: village",
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

mock_download_short = {
    "RouteData": "[]",
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


@patch("brevet_top_plot_a_route.route.Route.find_checkpoints", return_value=mock_checkpoints)
@patch("brevet_top_plot_a_route.route.Route.make_tracks")
@patch("brevet_top_plot_a_route.main.download_data", return_value=mock_download)
def test_get_route_info(
    mock_downloader,
    mock_tracks,
    mock_cps,
):
    # setup
    expected = {
        "checkpoints": mock_checkpoints,
        "name": "Jogging",
        "length": 3,
        "mapUrl": "https://www.plotaroute.com/route/123",
        "track": None,
        "short_track": None,
    }

    # action
    info = get_route_info("https://www.plotaroute.com/route/123")

    # verification
    mock_downloader.assert_called_once_with(
        "https://www.plotaroute.com/get_route.asp?RouteID=123"
    )
    mock_tracks.assert_called_once()
    mock_cps.assert_called_once()
    assert info == expected


@patch("brevet_top_plot_a_route.main.download_data", return_value=mock_download_error)
def test_get_route_info_exception(mock_downloader):
    # action
    with pytest.raises(RouteNotFound) as error:
        get_route_info("https://www.plotaroute.com/route/123")

    # verification
    assert "Invalid Route ID" in str(error)
    mock_downloader.assert_called_once_with(
        "https://www.plotaroute.com/get_route.asp?RouteID=123"
    )
