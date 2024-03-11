from brevet_top_plot_a_route.check_point import CheckPoint
from brevet_top_plot_a_route.route import Route
from brevet_top_plot_a_route.route_point import RoutePoint


def test_add_last_checkpoint_no_track():
    # setup
    route = Route()
    route._add_last_checkpoint()

    # verification
    assert route.checkpoints is None


def test_add_last_checkpoint_no_checkpoints():
    # setup
    route = Route(track=[RoutePoint(lat=40.78, lng=43.86, distance=0)])
    route._add_last_checkpoint()

    # verification
    assert route.checkpoints is None


def test_add_last_checkpoint_empty():
    # setup
    route = Route(checkpoints=[], track=[RoutePoint(lat=40.78, lng=43.86, distance=0)])
    route._add_last_checkpoint()

    # verification
    assert route.checkpoints == []


def test_add_last_checkpoint_close():
    # setup
    checkpoint = CheckPoint(lat=60, lng=30, distance=2, name="test")
    route = Route(checkpoints=[checkpoint], track=[RoutePoint(lat=40.78, lng=43.86, distance=3000)])
    route._add_last_checkpoint()

    # verification
    assert str(route.checkpoints) == ("[<CheckPoint lat=60 lng=30 name='test' distance=2>,"
                                      " <CheckPoint lat=40.78 lng=43.86 name='End' distance=3>]")


def test_add_last_checkpoint_add():
    # setup
    checkpoint = CheckPoint(lat=60, lng=30, distance=2, name="test")
    route = Route(checkpoints=[checkpoint], track=[RoutePoint(lat=40.78, lng=43.86, distance=5000)])
    route._add_last_checkpoint()

    # verification
    assert str(route.checkpoints) == ("[<CheckPoint lat=60 lng=30 name='test' distance=2>, "
                                      "<CheckPoint lat=40.78 lng=43.86 name='End' distance=5>]")
