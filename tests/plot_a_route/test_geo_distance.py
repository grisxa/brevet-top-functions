import pytest

from plot_a_route import geo_distance


@pytest.mark.parametrize(
    ("latitude1", "longitude1", "latitude2", "longitude2", "expected"),
    [
        (0, 0, 0, 0, 0),
        (10, 20, 10, 20, 0),
        (50, 20, 60, 20, 1111949.2664455846),
        (60, 20, 60, 30, 555445.1329718407),
        (59.99206, 30.217991, 59.993239, 30.21586, 176.72072480622808),
    ],
)
def test_geo_distance(latitude1, longitude1, latitude2, longitude2, expected):
    assert geo_distance(latitude1, longitude1, latitude2, longitude2) == expected


def test_geo_distance_exception():
    # action
    with pytest.raises(ValueError) as error:
        geo_distance(60.6910260, 28.8063560, 60.6910260, 28.8063570)

    # verification
    assert "math domain error" in str(error)
