from typing import List

import numpy as np
import pytest

from hirschberg.algo_numpy import linear_search, symbol_distance


@pytest.mark.parametrize(
    ("subject", "source", "alignment", "cost"),
    [
        ("A", "ABC", np.array(["A", None, None]), 0),
        ("B", "ABC", np.array([None, "B", None]), 0),
        ("D", "ABC", np.array([None, None, "D"]), 1),
        ("F", "ABC", np.array([None, None, "F"]), 3),
        ("C", "T", np.array(["C"]), 17),
        ("T", "C", np.array(["T"]), 17),
    ],
)
def test_linear_search(subject: str, source: str, alignment: List[str], cost: int):
    line, distance = linear_search(subject, np.array(list(source)), symbol_distance)
    assert np.array_equal(line, alignment)
    assert distance == cost
