import pytest

from brevet_top_plot_a_route.route import Route


@pytest.fixture()
def data_good():
    return {"RouteData": '[{"lat": 1, "lng": 2}]'}


@pytest.fixture()
def data_short():
    return {"Distance": "1"}


@pytest.fixture()
def data_bad():
    return {"RouteData": "error"}


def test_get_route_data_success(data_good):
    # setup
    route = Route.from_dict(data_good)

    # verification
    assert str(route.route_data) == "[<PlotARoutePoint lat=1 lng=2>]"


def test_get_route_data_empty(data_short):
    # setup
    route = Route.from_dict(data_short)

    # verification
    assert route.route_data == []


def test_get_route_data_failure(data_bad):
    # verification
    with pytest.raises(Exception) as error:
        Route.from_dict(data_bad)
    assert "JSONDecodeError" in str(error)
