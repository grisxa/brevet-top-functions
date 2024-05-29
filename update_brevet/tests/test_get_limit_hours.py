import pytest

from update_brevet.main import get_limit_hours


@pytest.mark.parametrize(
    ("distance", "time"),
    [
        (0, 0),
        (1, 1.05),
        (60, 4),
        (61, 4.067),
        (200, 13.5),
        (300, 20),
        (351, 23.4),
        (400, 27),
        (450, 30),
        (501, 33.4),
        (600, 40),
        (601, 40.088),
        (680, 47),
        (880, 64.501),
        (1000, 75.002),
        (1001, 75.089),
    ],
)
def test_get_limit_hours(distance: int, time: float):
    assert round(get_limit_hours(distance), 3) == time
