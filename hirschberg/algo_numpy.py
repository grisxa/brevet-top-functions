from typing import Tuple

import numpy as np
from numpy import add, full, concatenate, empty, fmax, flipud
from numpy.typing import ArrayLike

"""
The sequence alignment method is well explained here:

https://en.wikipedia.org/wiki/Hirschberg's_algorithm
http://blog.piotrturski.net/2015/04/hirschbergs-algorithm-explanation.html

Alternative (memory consuming):

https://en.wikipedia.org/wiki/Needleman–Wunsch_algorithm

"""


def np_hirschberg(
    source: ArrayLike,
    target: ArrayLike,
    deletion_cost: int = 100,
    insertion_cost: int = 0,
    cost_function=None,
) -> Tuple[ArrayLike, ArrayLike, float]:
    source_length, target_length = len(source), len(target)

    if source_length == 0 and target_length == 0:
        return [], [], 0

    if target_length == 0:
        return (
            source,
            full(source.shape, None),
            source_length * deletion_cost,
        )

    if source_length == 0:
        return (
            full(target.shape, None),
            target,
            target_length * insertion_cost,
        )

    if target_length == 1:
        indices, cost = linear_search(target[0], source, cost_function)
        return source, indices, deletion_cost * (source_length - 1) - cost

    if source_length == 1:
        indices, cost = linear_search(source[0], target, cost_function)
        return indices, target, insertion_cost * (target_length - 1) - cost

    cut_index: int = int(source_length / 2)
    upper_score: ArrayLike = line_score(
        source[:cut_index], target, deletion_cost, insertion_cost, cost_function
    )
    lower_score: ArrayLike = line_score(
        flipud(source[cut_index:]),
        flipud(target),
        deletion_cost,
        insertion_cost,
        cost_function,
    )

    max_index: int = int(np.argmax(upper_score + flipud(lower_score)))

    left_source, left_target, left_cost = np_hirschberg(
        source[:cut_index],
        target[:max_index],
        deletion_cost,
        insertion_cost,
        cost_function,
    )
    right_source, right_target, right_cost = np_hirschberg(
        source[cut_index:],
        target[max_index:],
        deletion_cost,
        insertion_cost,
        cost_function,
    )

    return (
        concatenate((left_source, right_source)),
        concatenate((left_target, right_target)),
        left_cost + right_cost,
    )


def line_score(
    source: ArrayLike,
    target: ArrayLike,
    deletion_cost: int = 100,
    insertion_cost: int = 10,
    cost_function=None,
) -> ArrayLike:
    source_length, target_length = len(source), len(target)

    if source_length == 0:
        return add.accumulate(full(target_length, insertion_cost))

    if target_length == 0:
        return add.accumulate(full(source_length, deletion_cost))

    full_deletion_column: ArrayLike = add.accumulate(
        concatenate(([0], full(source_length, deletion_cost)))
    )
    full_insertion_row: ArrayLike = add.accumulate(
        concatenate(([0], full(target_length, insertion_cost)))
    )

    row1: ArrayLike = full_insertion_row
    row2: ArrayLike = empty([target_length], dtype=np.int32)

    for i in range(source_length):
        replacement_score = row1[:-1] - cost_function(source[i], target)
        deletion_score = row1[1:] + deletion_cost
        replacement_deletion_score_max = fmax(replacement_score, deletion_score)

        for j in range(target_length):
            insertion_score = insertion_cost + (
                full_deletion_column[i + 1] if j == 0 else row2[j - 1]
            )
            row2[j] = max(replacement_deletion_score_max[j], insertion_score)
        row1 = concatenate(([full_deletion_column[i + 1]], row2))
    return row1


def next_cell(deletion_score: int, replacement_score: int, insertion_score: int) -> int:
    return max(deletion_score, replacement_score, insertion_score)


def linear_search(subject, source: ArrayLike, cost_function) -> Tuple[ArrayLike, int]:
    line: ArrayLike = full(source.shape, None)
    cost: ArrayLike = cost_function(subject, source)
    index: int = cost.argmin()
    line[index] = subject
    return line, cost[index]


def symbol_distance(a: str, b: ArrayLike) -> ArrayLike:
    return abs(b.view(np.int32) - ord(a))


def match_distance(a: ArrayLike, b: ArrayLike) -> ArrayLike:
    return 1 - np.equal(a.view(np.int32), b.view(np.int32)) * 3
