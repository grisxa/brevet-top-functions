from typing import Tuple

import pytest

from hirschberg.algo_pure import hirschberg, match_distance


def test_hirschberg_empty():
    assert hirschberg([], []) == ([], [], 0)


def test_hirschberg_deletion():
    assert hirschberg(list("ABC"), [], deletion_cost=-2) == (
        list("ABC"),
        [None, None, None],
        -6,
    )


def test_hirschberg_insertion():
    assert hirschberg([], list("AB"), insertion_cost=-2) == (
        [None, None],
        list("AB"),
        -4,
    )


def test_hirschberg_single_target():
    assert hirschberg(
        list("AB"), ["A"], deletion_cost=-2, cost_function=match_distance
    ) == (list("AB"), ["A", None], 0)


def test_hirschberg_single_source():
    assert hirschberg(
        ["B"], list("AB"), insertion_cost=-2, cost_function=match_distance
    ) == ([None, "B"], list("AB"), 0)


@pytest.mark.parametrize(
    ("source", "target", "alignments"),
    [
        ("CG", "TG", (list("CG"), list("TG"), 1)),
        ("C", "CA", (["C", None], list("CA"), 0)),
        ("CA", "C", (list("CA"), ["C", None], 0)),
        ("CGCA", "TGC", (list("CGCA"), ["T", "G", "C", None], 1)),
        ("TA", "TA", (list("TA"), list("TA"), 4)),
        ("AG", "", (list("AG"), [None, None], -4)),
        ("AGTA", "TA", (list("AGTA"), [None, None, "T", "A"], 0)),
        (
            "AGTACGCA",
            "TATGC",
            (list("AGTACGCA"), [None, None, "T", "A", "T", "G", "C", None], 1),
        ),
        # FIXME: gap penalty
        (
            "GAAAAAAT",
            "GAAT",
            (list("GAAAAAAT"), ["G", None, None, None, "A", None, "A", "T"], 0),
        ),
    ],
)
def test_hirschberg(source: str, target: str, alignments: Tuple[list, list]):
    assert (
        hirschberg(
            list(source),
            list(target),
            deletion_cost=-2,
            insertion_cost=-2,
            cost_function=match_distance,
        )
        == alignments
    )
