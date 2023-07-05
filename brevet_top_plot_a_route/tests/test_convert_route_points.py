import pytest

from brevet_top_plot_a_route import convert_route_points, RoutePoint


@pytest.mark.parametrize(
    ("track", "route"),
    [
        ([], []),
        ([{"lat": 0, "lng": 0}], [RoutePoint(lat=0, lng=0, distance=0)]),
        (
            [{"lat": 60, "lng": 30}, {"lat": 60.1, "lng": 30.1}],
            [
                RoutePoint(lat=60, lng=30, distance=0),
                RoutePoint(lat=60.1, lng=30.1, distance=12428.210486152113),
            ],
        ),
        (
            [
                {"lat": 60, "lng": 30},
                {"lat": 60.1, "lng": 30.1},
                {"lat": 60.2, "lng": 30.2},
            ],
            [
                RoutePoint(lat=60, lng=30, distance=0),
                RoutePoint(lat=60.1, lng=30.1, distance=12428.210486152113),
                RoutePoint(lat=60.2, lng=30.2, distance=24848.915263829265),
            ],
        ),
    ],
)
def test_convert_route_points(track, route):
    assert convert_route_points(track) == route
