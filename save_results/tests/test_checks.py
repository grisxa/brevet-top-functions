import pytest
from google.api_core.datetime_helpers import DatetimeWithNanoseconds

from save_results import is_manual_checkin, is_strava_checkin, is_self_checkin


@pytest.mark.parametrize(
    ("checkin", "result"),
    [
        ("2023-07-10T04:04:00+00:00", True),
        ("2023-07-17T01:16:06+00:00", False),
        ("2023-07-10T04:25:11.170000+00:00", False),
    ],
)
def test_manual_checkin(checkin: str, result: bool):
    assert is_manual_checkin(DatetimeWithNanoseconds.fromisoformat(checkin)) == result


@pytest.mark.parametrize(
    ("checkin", "result"),
    [
        ("2023-07-10T04:04:00+00:00", True),
        ("2023-07-17T01:16:06+00:00", True),
        ("2023-07-10T04:25:11.170000+00:00", False),
    ],
)
def test_strava_checkin(checkin: str, result: bool):
    assert is_strava_checkin(DatetimeWithNanoseconds.fromisoformat(checkin)) == result


@pytest.mark.parametrize(
    ("checkin", "result"),
    [
        ("2023-07-10T04:04:00+00:00", False),
        ("2023-07-17T01:16:06+00:00", False),
        ("2023-07-10T04:25:11.170000+00:00", True),
    ],
)
def test_self_checkin(checkin: str, result: bool):
    assert is_self_checkin(DatetimeWithNanoseconds.fromisoformat(checkin)) == result
