import pytest
from google.api_core.datetime_helpers import DatetimeWithNanoseconds

from save_results import is_manual_checkin, is_self_checkin, is_strava_checkin
from save_results.main import checkin_reorder


@pytest.mark.parametrize(
    ("checkin", "result"),
    [
        ("2023-07-10T04:04:00+00:00", False),
        ("2023-07-17T01:16:06+00:00", False),
        ("2023-07-10T04:25:11.170000+00:00", False),
        ("2023-07-10T04:25:11.123456+00:00", True),
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
        ("2023-07-10T04:25:11.123456+00:00", False),
    ],
)
def test_self_checkin(checkin: str, result: bool):
    assert is_self_checkin(DatetimeWithNanoseconds.fromisoformat(checkin)) == result


@pytest.mark.parametrize(
    ("checkins", "results"),
    [
        (
            [
                "2024-04-28 10:06:55+00:00",
                "2024-04-28 10:08:26.923000+00:00",
                "2024-04-28 10:10:03.123456+00:00",
                "2024-04-28 10:14:00+00:00",
            ],
            [
                "2024-04-28 10:10:03.123456+00:00",  # volunteer's checkin has the highest priority
                "2024-04-28 10:08:26.923000+00:00",  # self checkin has the second priority
                "2024-04-28 10:06:55+00:00",  # strava checkins are the least important
                "2024-04-28 10:14:00+00:00",
            ],
        ),
    ],
)
def test_checkin_reorder(checkins: list[str], results: list[str]):
    assert checkin_reorder(
        [DatetimeWithNanoseconds.fromisoformat(c) for c in checkins]
    ) == [DatetimeWithNanoseconds.fromisoformat(r) for r in results]
