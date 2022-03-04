from typing import List

import pytest

from hirschberg.algo_numpy import line_score, match_distance
import numpy as np


def test_line_score_empty():
    line = line_score([], [])
    assert np.array_equal(line, [])


def test_line_score_source_empty():
    line = line_score([], np.array(list("AB")))
    assert np.array_equal(line, [10, 20])


def test_line_score_target_empty():
    line = line_score(np.array(list("AB")), [])
    assert np.array_equal(line, [100, 200])


@pytest.mark.parametrize(
    ("source", "target", "score"),
    [
        ("", "AB", [-2, -4]),
        ("AB", "", [-2, -4]),
        ("A", "A", [-2, 2]),
        ("A", "T", [-2, -1]),
        ("A", "TA", [-2, -1, 0]),
        ("AG", "T", [-4, -3]),
        ("AGTA", "TATGC", [-8, -4, 0, -2, -1, -3]),
        ("ACGC", "CGTAT", [-8, -4, 0, 1, -1, -3]),
    ],
)
def test_line_score(source: str, target: str, score: List[float]):
    line = line_score(
        np.array(list(source)),
        np.array(list(target)),
        insertion_cost=-2,
        deletion_cost=-2,
        cost_function=match_distance,
    )
    assert np.array_equal(line, score)
