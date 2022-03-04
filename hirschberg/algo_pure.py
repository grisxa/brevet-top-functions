from typing import Tuple, List, TypeVar, Optional

T = TypeVar("T")

"""
The sequence alignment method is well explained here:

https://en.wikipedia.org/wiki/Hirschberg's_algorithm
http://blog.piotrturski.net/2015/04/hirschbergs-algorithm-explanation.html

Alternative (memory consuming):

https://en.wikipedia.org/wiki/Needleman–Wunsch_algorithm

"""


def hirschberg(
    source: List[Optional[T]],
    target: List[Optional[T]],
    deletion_cost: int = 100,
    insertion_cost: int = 0,
    cost_function=None,
) -> Tuple[List[Optional[T]], List[Optional[T]], float]:
    source_length: int = len(source)
    target_length: int = len(target)

    if source_length == 0 and target_length == 0:
        return [], [], 0

    if target_length == 0:
        return source, [None] * source_length, source_length * deletion_cost

    if source_length == 0:
        return [None] * target_length, target, target_length * insertion_cost

    if target_length == 1:
        (indices, cost) = linear_search(target[0], source, cost_function)
        return source, indices, deletion_cost * (source_length - 1) - cost

    if source_length == 1:
        indices, cost = linear_search(source[0], target, cost_function)
        return indices, target, insertion_cost * (target_length - 1) - cost

    cut_index = int(source_length / 2)
    left_score: List[float] = line_score(
        source[:cut_index], target, deletion_cost, insertion_cost, cost_function
    )
    # fmt: off
    right_score: List[float] = line_score(
        source[:(cut_index-1):-1],
        target[::-1],
        deletion_cost,
        insertion_cost,
        cost_function,
    )
    # fmt: on

    sum_score = [a + b for a, b in zip(left_score, right_score[::-1])]
    max_score = max(a + b for a, b in zip(left_score, right_score[::-1]))
    max_index = sum_score.index(max_score)

    left_cost, left_indices, left_total_cost = hirschberg(
        source[:cut_index],
        target[:max_index],
        deletion_cost,
        insertion_cost,
        cost_function,
    )
    right_cost, right_indices, right_total_cost = hirschberg(
        source[cut_index:],
        target[max_index:],
        deletion_cost,
        insertion_cost,
        cost_function,
    )

    return (
        left_cost + right_cost,
        left_indices + right_indices,
        left_total_cost + right_total_cost,
    )


def line_score(
    source: List[T],
    target: List[T],
    deletion_cost: int = 100,
    insertion_cost: int = 0,
    cost_function=None,
) -> List[float]:
    source_length: int = len(source)
    target_length: int = len(target)

    line1: List[float] = [j * insertion_cost for j in range(target_length + 1)]
    line2: List[float] = []
    for i in range(1, source_length + 1):
        line2 = [line1[0] + deletion_cost]
        for j in range(1, target_length + 1):
            replacement_score = line1[j - 1] - cost_function(
                source[i - 1], target[j - 1]
            )
            deletion_score = line1[j] + deletion_cost  # source[i]
            insertion_score = line2[j - 1] + insertion_cost  # target[j]

            line2.append(max(replacement_score, deletion_score, insertion_score))
        line1 = line2
    return line2


def linear_search(
    subject: Optional[T], source: List[Optional[T]], cost_function
) -> Tuple[List[Optional[T]], float]:
    minimum_cost: float = float("inf")
    index: int = 0
    line: List[Optional[T]] = [None] * len(source)
    for i, value in enumerate(source):
        cost = cost_function(subject, value)
        if cost < minimum_cost:
            minimum_cost = cost
            index = i
    line[index] = subject
    return line, minimum_cost


def symbol_distance(source: str, target: str) -> int:
    return abs(ord(target) - ord(source))


def match_distance(a, b) -> float:
    return -2 if a == b else 1
