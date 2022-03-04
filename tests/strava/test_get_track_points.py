from unittest.mock import patch, call

from strava.api import get_track_points, STREAM_OPTIONS

ACTIVITIES = [
    {"id": "1"},
    {"id": "2"},
    {"id": "3"},
]

TOKEN: str = "Bearer none"

HEADERS = {"Authorization": TOKEN}

STRAVA_STREAMS = {
    "latlng": {
        "data": [
            [60.025713, 30.29734],
            [60.025625, 30.297406],
            [60.025575, 30.297454],
        ],
        "series_type": "distance",
        "original_size": 3,
        "resolution": "high",
    },
    "distance": {
        "data": [
            200.7,
            210.9,
            216.7,
        ],
        "series_type": "distance",
        "original_size": 3,
        "resolution": "high",
    },
    "time": {
        "data": [
            59,
            62,
            64,
        ],
        "series_type": "distance",
        "original_size": 3,
        "resolution": "high",
    },
}

TRACK = [
    [60.025713, 30.29734, 1234567949.0, 200.7],
    [60.025625, 30.297406, 1234567952.0, 210.9],
    [60.025575, 30.297454, 1234567954.0, 216.7],
]


@patch("strava.api.build_track", return_value=TRACK)
@patch("strava.api.download_data", return_value=STRAVA_STREAMS)
@patch("strava.api.get_track_start_point", return_value=(60, 30, 1234567890, 0))
def test_get_track_points(mock_start, mock_download, mock_build):
    # setup
    start_calls = [call(ACTIVITIES[0]), call(ACTIVITIES[1]), call(ACTIVITIES[2])]
    download_calls = [
        call(
            "https://www.strava.com/api/v3/activities/1/streams",
            HEADERS,
            params=STREAM_OPTIONS,
        ),
        call(
            "https://www.strava.com/api/v3/activities/2/streams",
            HEADERS,
            params=STREAM_OPTIONS,
        ),
        call(
            "https://www.strava.com/api/v3/activities/3/streams",
            HEADERS,
            params=STREAM_OPTIONS,
        ),
    ]
    build_calls = [
        call(start_timestamp=1234567890, start_distance=0, stream=STRAVA_STREAMS),
        call(start_timestamp=1234567890, start_distance=216.7, stream=STRAVA_STREAMS),
        call(start_timestamp=1234567890, start_distance=216.7, stream=STRAVA_STREAMS),
    ]
    # action
    track = get_track_points(ACTIVITIES, TOKEN)

    # verification
    mock_start.assert_has_calls(start_calls)
    mock_download.assert_has_calls(download_calls)
    mock_build.assert_has_calls(build_calls)
    assert track.tolist() == TRACK * 3


@patch("strava.api.build_track", return_value=TRACK)
@patch("strava.api.download_data", return_value=STRAVA_STREAMS)
@patch("strava.api.get_track_start_point", return_value=(60, 30, 1234567890, 0))
def test_get_track_points_empty(mock_start, mock_download, mock_build):
    # action
    track = get_track_points([], TOKEN)

    # verification
    mock_start.assert_not_called()
    mock_download.assert_not_called()
    mock_build.assert_not_called()
    assert track.tolist() == []
