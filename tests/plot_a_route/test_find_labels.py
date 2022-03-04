import pytest

from plot_a_route import find_labels
from plot_a_route.check_point import CheckPoint


@pytest.fixture()
def point():
    return {
        "lat": 60.027579,
        "lng": 30.296469,
        "dir": "Start on ",
        "sur": "asphalt",
        "rdc": "footway",
        "symlabs": [
            {
                "lat": 60.0164379,
                "lng": 30.2789855,
                "sym": {"iconclass": "fa fa-shopping-cart", "iconcol": "sc1"},
                "lab": {
                    "labtxt": "CP2: shop",
                    "labpos": "N",
                    "labsize": "S",
                    "labcol": "sc0",
                },
            }
        ],
    }


def test_find_labels(point):
    # setup
    route_point = CheckPoint(**point)
    expected = [CheckPoint(lat=60.0164379, lng=30.2789855, name="CP2: shop")]

    # action/verification
    assert find_labels(route_point) == expected
