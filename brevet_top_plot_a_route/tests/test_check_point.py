import pytest

from brevet_top_plot_a_route.check_point import CheckPoint


@pytest.mark.parametrize(
    ("kwargs", "dump"),
    [
        ({}, "<CheckPoint lat=0 lng=0 name='' distance=0.0>"),
        ({"lat": 60, "lng": 30, "distance": 1000}, "<CheckPoint lat=60 lng=30 name='' distance=1.0>"),
        ({"lat": 60, "lng": 30, "distance": 1000, "labtxt": "start"},
         "<CheckPoint lat=60 lng=30 name='start' distance=1.0>"),
    ]
)
def test_check_point(kwargs, dump):
    # setup
    point = CheckPoint(**kwargs)

    # verification
    assert str(point) == dump


@pytest.mark.parametrize(
    ("kwargs", "name"),
    [
        ({"lat": 60, "lng": 30, "distance": 100, "name": "CP1"}, "CP1"),
        ({"lat": 60, "lng": 30, "distance": 100, "dir": "right"}, "right"),
        ({"lat": 60, "lng": 30, "distance": 100, "labtxt": "start"}, "start"),
    ]
)
def test_check_point_fix_name(kwargs, name):
    # setup
    point = CheckPoint(**kwargs)

    # verification
    assert point.name == name


def test_check_point_overwrite_name():
    # setup
    point = CheckPoint(lat=60, lng=30, distance=100)

    # action
    point.fix_name(" CP2 ")

    # verification
    # no leading/trailing spaces
    assert point.name == "CP2"
