from brevet_top_plot_a_route.route_point import PlotARoutePoint

from brevet_top_plot_a_route.route import Route


def test_route():
    # setup
    a = Route()
    b = Route.from_dict({"RouteName": "test", "Distance": 123.45})

    # verification
    assert repr(a) == "<Route name= distance=0>"
    assert repr(b) == "<Route name=test distance=123.45>"


def test_full():
    # setup
    a = Route.from_dict({
      "RouteData": "[{\"lat\":40.78,\"lng\":43.86,\"dir\":\"Start on a square\"}]",
      "RouteID": 12345,
      "RouteName": "test",
      "Distance": 123.45,
    })

    # verification
    assert repr(a) == "<Route name=test distance=123.45>"
    assert a.route_id == 12345
    assert a.route_data == [PlotARoutePoint(lat=40.78, lng=43.86, dir="Start on a square")]
