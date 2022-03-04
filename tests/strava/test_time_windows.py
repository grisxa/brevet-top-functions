import dateutil.parser
import pytest

from strava.api import time_window


@pytest.mark.parametrize(
    ("brevet", "params"),
    [
        ({}, {}),
        (
            {"startDate": dateutil.parser.isoparse("2021-11-17T11:12:13Z")},
            {"after": 1637140333.0},
        ),
        (
            {"endDate": dateutil.parser.isoparse("2021-11-17T11:12:13Z")},
            {"before": 1637154733.0},
        ),
        (
            {
                "startDate": dateutil.parser.isoparse("2021-11-16T11:12:13Z"),
                "endDate": dateutil.parser.isoparse("2021-11-17T11:12:13Z"),
            },
            {"after": 1637053933.0, "before": 1637154733.0},
        ),
    ],
)
def test_time_window(brevet: dict, params: dict):
    assert time_window(brevet) == params
