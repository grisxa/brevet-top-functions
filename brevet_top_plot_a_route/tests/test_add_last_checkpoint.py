from brevet_top_plot_a_route.check_point import CheckPoint
from brevet_top_plot_a_route.route import Route
from brevet_top_plot_a_route.route_point import RoutePoint


def test_add_last_checkpoint_no_track():
    # setup
    route = Route()

    # action
    result = route._add_last_checkpoint()

    # verification
    assert result is None


def test_add_last_checkpoint_no_checkpoints():
    # setup
    route = Route(track=[RoutePoint(lat=40.78, lng=43.86, distance=0)])

    # action
    result = route._add_last_checkpoint()

    # verification
    assert result is None


def test_add_last_checkpoint_empty():
    # setup
    route = Route(checkpoints=[], track=[RoutePoint(lat=40.78, lng=43.86, distance=0)])

    # action
    result = route._add_last_checkpoint()

    # verification
    assert result is None


def test_add_last_checkpoint_close():
    # setup
    checkpoint = CheckPoint(lat=60, lng=30, distance=2, name="test")
    route = Route(checkpoints=[checkpoint], track=[RoutePoint(lat=40.78, lng=43.86, distance=2400)])

    # action
    result = route._add_last_checkpoint(route.checkpoints)

    # verification
    assert str(result) == "[<CheckPoint lat=60 lng=30 name='test' distance=2>]"


def test_add_last_checkpoint_add():
    # setup
    checkpoint = CheckPoint(lat=60, lng=30, distance=2, name="test")
    route = Route(checkpoints=[checkpoint], track=[RoutePoint(lat=40.78, lng=43.86, distance=5000)])

    # action
    result = route._add_last_checkpoint(route.checkpoints)

    # verification
    assert str(result) == ("[<CheckPoint lat=60 lng=30 name='test' distance=2>, "
                           "<CheckPoint lat=40.78 lng=43.86 name='End' distance=5>]")
