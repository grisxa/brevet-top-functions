from datetime import datetime
from typing import Tuple

import pytest

from strava.build import get_track_start_point


@pytest.mark.parametrize(
    ("activity", "point"),
    [
        (
            {
                "start_latitude": 60,
                "start_longitude": 30,
                "start_date": "2021-11-15T12:13:14Z",
            },
            (
                60,
                30,
                1636978394.0,
                0,
            ),
        ),
    ],
)
def test_get_track_start_point(
    activity: dict, point: Tuple[float, float, float, datetime]
):
    assert get_track_start_point(activity) == point


def test_get_track_start_fail():
    with pytest.raises(KeyError) as error:
        get_track_start_point({})
    assert "start_latitude" in str(error)
