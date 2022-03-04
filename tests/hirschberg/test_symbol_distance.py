import pytest

from hirschberg.algo_pure import symbol_distance


@pytest.mark.parametrize(
    ("source", "target", "result"),
    [
        ("a", "a", 0),
        ("a", "b", 1),
        ("c", "a", 2),
        ("A", "a", 32),
    ],
)
def test_symbol_distance(source: str, target: str, result: int):
    assert symbol_distance(source, target) == result
