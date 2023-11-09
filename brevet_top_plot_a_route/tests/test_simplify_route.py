from typing import List

import pytest

from brevet_top_plot_a_route.utils import simplify_route
from brevet_top_plot_a_route.route_point import RoutePoint


@pytest.mark.parametrize(
    ("track", "simplified"),
    [
        ([], []),
        ([RoutePoint(lat=0, lng=0)], [RoutePoint(lat=0, lng=0)]),
        (
            [RoutePoint(lat=60, lng=30), RoutePoint(lat=60.1, lng=30.1)],
            [RoutePoint(lat=60, lng=30), RoutePoint(lat=60.1, lng=30.1)],
        ),
        (
            [
                RoutePoint(lat=60, lng=30),
                RoutePoint(lat=60.1, lng=30.1),
                RoutePoint(lat=60.1, lng=30.1),
            ],
            [RoutePoint(lat=60, lng=30), RoutePoint(lat=60.1, lng=30.1)],
        ),
        (
            [
                RoutePoint(lat=60, lng=30),
                RoutePoint(lat=60.1, lng=30.1),
                RoutePoint(lat=60.2, lng=30.2),
            ],
            [RoutePoint(lat=60, lng=30), RoutePoint(lat=60.2, lng=30.2)],
        ),
        (
            [
                RoutePoint(lat=60, lng=30),
                RoutePoint(lat=60.3, lng=30.1),
                RoutePoint(lat=60.2, lng=30.2),
            ],
            [
                RoutePoint(lat=60, lng=30),
                RoutePoint(lat=60.3, lng=30.1),
                RoutePoint(lat=60.2, lng=30.2),
            ],
        ),
    ],
)
def test_simplify_route(track: List[RoutePoint], simplified: List[RoutePoint]):
    assert simplify_route(track) == simplified
