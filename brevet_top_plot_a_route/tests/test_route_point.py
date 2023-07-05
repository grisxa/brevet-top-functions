from brevet_top_plot_a_route.route_point import PlotARoutePoint, RoutePoint


def test_plot_a_route_point():
    # setup
    a = PlotARoutePoint()
    b = PlotARoutePoint()
    b.lat, b.lng = 60, 30

    # verification
    assert str(a) == "<PlotARoutePoint lat=0 lng=0>"
    assert str(b) == "<PlotARoutePoint lat=60 lng=30>"


def test_route_point():
    # setup
    a = RoutePoint()
    b = RoutePoint(lat=60, lng=30, distance=100)
    c = RoutePoint(lat=60, lng=30, distance=100, dir="right", labtxt="start")

    # verification
    assert str(a) == "<RoutePoint lat=0 lng=0 distance=0>"
    assert str(b) == "<RoutePoint lat=60 lng=30 distance=100>"
    assert str(c) == "<RoutePoint lat=60 lng=30 distance=100>"
    assert c.dir == "right"
    assert c.labtxt == "start"
    assert a != {}
    assert a != b
    assert b == c


def test_route_point_is_control():
    # setup
    a = RoutePoint(lat=60, lng=30, distance=100, dir="CP1", labtxt="stop")
    b = RoutePoint(lat=60, lng=30, distance=100, dir="right", labtxt="CP2")
    c = RoutePoint(lat=60, lng=30, distance=100, dir="right", labtxt="start")
    d = RoutePoint(lat=60, lng=30, distance=100)

    # verification
    assert a.is_control() is True
    assert b.is_control() is True
    assert c.is_control() is False
    assert d.is_control() is False
