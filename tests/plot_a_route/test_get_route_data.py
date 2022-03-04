import pytest

from plot_a_route import get_route_data


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
    assert get_route_data(data_good) == [{"lat": 1, "lng": 2}]


def test_get_route_data_empty(data_short):
    assert get_route_data(data_short) == []


def test_get_route_data_failure(data_bad):
    with pytest.raises(Exception) as error:
        get_route_data(data_bad)
    assert "JSONDecodeError" in str(error)
