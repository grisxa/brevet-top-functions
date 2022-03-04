from typing import List

import pytest

from hirschberg.algo_pure import linear_search, symbol_distance


@pytest.mark.parametrize(
    ("subject", "source", "alignment", "cost"),
    [
        ("A", "ABC", ["A", None, None], 0),
        ("B", "ABC", [None, "B", None], 0),
        ("D", "ABC", [None, None, "D"], 1),
        ("F", "ABC", [None, None, "F"], 3),
        ("C", "T", ["C"], 17),
        ("T", "C", ["T"], 17),
    ],
)
def test_linear_search(subject: str, source: str, alignment: List[str], cost: float):
    assert linear_search(subject, list(source), symbol_distance) == (alignment, cost)
