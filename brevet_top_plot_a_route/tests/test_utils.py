import pytest

from brevet_top_plot_a_route.utils import get_map_id_from_url, route_down_sample_factor


@pytest.mark.parametrize(
    ("url", "map_id"),
    [
        (None, None),
        ("", None),
        ("wrong", None),
        ("https://example.com/path", None),
        ("https://www.plotaroute.com/route/123", 123),
        ("https://www.plotaroute.com/route/123.45", 123),
        ("https://www.plotaroute.com/route/123.45?units=km", 123),
    ],
)
def test_get_map_id_from_url(url: str, map_id: float):
    # verification
    assert get_map_id_from_url(url) == map_id


@pytest.mark.parametrize(
    ("size", "length", "factor"),
    [
        (8000, 500, 0.01001),
        (8000, 300, 0.00601),
        (8000, 200, 0.004),
        (4000, 300, 0.00602),
        (4000, 200, 0.00401),
        (2000, 200, 0.00402),
        (2000, 100, 0.00201),
        (2000, 50, 0.00101),
        (1000, 100, 0.00202),
        (1000, 50, 0.00101),
        (500, 100, 0.00204),
        (500, 50, 0.00102),
        (200, 100, 0.0021),
        (200, 50, 0.00105),
        (100, 50, 0.0011),
    ],
)
def test_route_down_sample_factor(size: int, length: int, factor: float):
    assert round(route_down_sample_factor(size, length), 5) == factor
