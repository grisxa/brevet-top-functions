from typing import List

import pytest

from hirschberg.algo_pure import line_score, match_distance


def test_line_score_empty():
    assert line_score([], []) == []


@pytest.mark.parametrize(
    ("source", "target", "score"),
    [
        ("A", "A", [-2, 2]),
        ("A", "T", [-2, -1]),
        ("A", "TA", [-2, -1, 0]),
        ("AG", "T", [-4, -3]),
        ("AGTA", "TATGC", [-8, -4, 0, -2, -1, -3]),
        ("ACGC", "CGTAT", [-8, -4, 0, 1, -1, -3]),
    ],
)
def test_line_score(source: str, target: str, score: List[float]):
    assert (
        line_score(
            list(source),
            list(target),
            insertion_cost=-2,
            deletion_cost=-2,
            cost_function=match_distance,
        )
        == score
    )
