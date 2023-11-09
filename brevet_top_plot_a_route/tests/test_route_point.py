from types import NotImplementedType

import pytest

from brevet_top_plot_a_route.route import Route
from brevet_top_plot_a_route.route_point import PlotARoutePoint, RoutePoint


@pytest.mark.parametrize(
    ("kwargs", "dump"),
    [
        ({}, "<PlotARoutePoint lat=0 lng=0>"),
        ({"lat": 60, "lng": 30}, "<PlotARoutePoint lat=60 lng=30>"),
        ({"lat": 60, "lng": 30, "sur": "asphalt"}, "<PlotARoutePoint lat=60 lng=30>"),  # should drop "sur"
        ({"lat": 60, "lng": 30, "dir": "Start"}, "<PlotARoutePoint lat=60 lng=30>"),
        ({"lat": 60, "lng": 30, "labtxt": "here"}, "<PlotARoutePoint lat=60 lng=30>"),
        ({"lat": 60, "lng": 30, "symlabs": [{}]}, "<PlotARoutePoint lat=60 lng=30>"),
    ]
)
def test_plot_a_route_point(kwargs, dump):
    # setup
    point = PlotARoutePoint(**kwargs)

    # verification
    assert str(point) == dump
    assert type(point.labtxt) is str
    assert type(point.symlabs) is list


@pytest.mark.parametrize(
    ("kwargs", "dump"),
    [
        ({}, "<RoutePoint lat=0 lng=0 distance=0>"),
        ({"lat": 60, "lng": 30, "distance": 100}, "<RoutePoint lat=60 lng=30 distance=100>"),
        ({"lat": 60, "lng": 30, "sur": "asphalt"}, "<RoutePoint lat=60 lng=30 distance=0>"),  # should drop "sur"
        ({"lat": 60, "lng": 30, "symlabs": []}, "<RoutePoint lat=60 lng=30 distance=0>"),  # should accept "symlabs"
    ]
)
def test_route_point(kwargs, dump):
    # setup
    point = RoutePoint(**kwargs)

    # verification
    assert str(point) == dump
    assert type(point.labtxt) is str
    assert type(point.symlabs) is list


def test_route_point_equality():
    # setup
    a = RoutePoint(lat=60, lng=30, distance=100)
    b = RoutePoint(lat=60, lng=30, distance=100, dir="right", labtxt="start")

    # verification
    assert a == b


def test_route_point_inequality():
    # setup
    a = RoutePoint(lat=60, lng=30, distance=100)
    b = RoutePoint(lat=60, lng=30, distance=101)

    # verification
    assert a != b


def test_route_point_equality_wrong_class():
    # setup
    a = RoutePoint(lat=60, lng=30, distance=100, dir="right", labtxt="start")
    b = PlotARoutePoint(lat=60, lng=30)

    c = a.__eq__(b)

    # verification
    assert type(c) is NotImplementedType


@pytest.mark.parametrize(
    ("kwargs", "control"),
    [
        ({"lat": 60, "lng": 30, "distance": 100, "dir": "CP1", "labtxt": "stop"}, True),
        ({"lat": 60, "lng": 30, "distance": 100, "dir": "right", "labtxt": "CP2"}, True),
        ({"lat": 60, "lng": 30, "distance": 100, "dir": "right", "labtxt": "start"}, False),
        ({"lat": 60, "lng": 30, "distance": 100}, False),
    ]
)
def test_route_point_is_control(kwargs, control):
    # setup
    point = RoutePoint(**kwargs)

    # verification
    assert point.is_control() == control


def test_from_plot_a_route():
    # setup
    point = PlotARoutePoint(lat=60, lng=30)
    expected = RoutePoint(lat=60, lng=30, distance=10)

    # verification
    assert RoutePoint.from_plot_a_route(point, distance=10) == expected
