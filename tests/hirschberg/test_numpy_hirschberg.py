from typing import Tuple

import pytest

from hirschberg.algo_numpy import np_hirschberg, symbol_distance, match_distance
import numpy as np


def test_hirschberg_empty():
    assert np_hirschberg([], []) == ([], [], 0)


def test_hirschberg_deletion():
    first, second, distance = np_hirschberg(
        np.array(list("ABC")), [], deletion_cost=-2, cost_function=symbol_distance
    )
    assert np.array_equal(first, np.array(list("ABC")))
    assert np.array_equal(second, np.array([None, None, None]))
    assert distance == -6


def test_hirschberg_insertion():
    first, second, distance = np_hirschberg(
        [], np.array(list("AB")), insertion_cost=-2, cost_function=symbol_distance
    )
    assert np.array_equal(first, np.array([None, None]))
    assert np.array_equal(second, np.array(list("AB")))
    assert distance == -4


def test_hirschberg_single_target():
    first, second, distance = np_hirschberg(
        np.array(list("AB")), ["A"], deletion_cost=-2, cost_function=symbol_distance
    )
    assert np.array_equal(first, np.array(list("AB")))
    assert np.array_equal(second, np.array(["A", None]))
    assert distance == -2


def test_hirschberg_single_source():
    first, second, distance = np_hirschberg(
        ["B"], np.array(list("AB")), insertion_cost=-2, cost_function=symbol_distance
    )
    assert np.array_equal(first, np.array([None, "B"]))
    assert np.array_equal(second, np.array(list("AB")))
    assert distance == -2


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
def test_hirschberg(source: str, target: str, alignments: Tuple[list, list, int]):
    first, second, distance = np_hirschberg(
        np.array(list(source)),
        np.array(list(target)),
        deletion_cost=-2,
        insertion_cost=-2,
        cost_function=match_distance,
    )
    assert np.array_equal(first, np.array(alignments[0]))
    assert np.array_equal(second, np.array(alignments[1]))
    assert distance == alignments[2]
