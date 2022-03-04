import csv
import pathlib
from timeit import default_timer as timer
from typing import List, Tuple

import numpy as np
import pytest
from numpy.typing import ArrayLike

from strava.simplify import (
    cut_off_prolog,
    cut_off_epilog,
    clear_stops,
    down_sample_mask,
)

COUNTER = 100


def read_csv(file_name: str) -> ArrayLike:
    file_path = pathlib.Path(__file__).parent.absolute() / "files" / file_name
    with open(file_path, newline="", encoding="utf-8") as csv_file:
        table = csv.reader(csv_file, delimiter=",", quotechar='"')
        return np.array([row for row in table], dtype=float)


@pytest.fixture
def read_source() -> ArrayLike:
    return read_csv("gps-track.csv")


@pytest.fixture
def read_data(expected_file: str) -> ArrayLike:
    return read_csv(expected_file)


@pytest.fixture
def csv_file():
    file_path = (
        pathlib.Path(__file__).parent.absolute() / "files" / "gps-track-temp.csv"
    )
    with open(file_path, "w", newline="", encoding="utf-8") as csv_file_handler:
        yield csv.writer(
            csv_file_handler, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
        )


@pytest.fixture
def get_checkpoints() -> List[Tuple[float, float, float, float]]:
    return [
        (59.99206, 30.217991, 0.0, 0),
        (59.98603, 30.227709, 0.0, 302000),
    ]


@pytest.mark.parametrize("expected_file", ["gps-track-epilog.csv"])
def test_cut_off_epilog(
    read_data: ArrayLike,
    read_source: ArrayLike,
    get_checkpoints: List[Tuple[float, float, float, float]],
):
    start = timer()
    for _ in range(COUNTER):
        epilog = cut_off_epilog(read_source, get_checkpoints[-1])
    end = timer()
    print(f"\nepilog: {end-start} sec.")

    assert np.array_equal(epilog, read_data)


@pytest.mark.parametrize("expected_file", ["gps-track-prolog.csv"])
def test_cut_off_prolog(
    read_data: ArrayLike,
    read_source: ArrayLike,
    get_checkpoints: List[Tuple[float, float, float, float]],
):
    start = timer()
    for _ in range(COUNTER):
        prolog = cut_off_prolog(read_source, get_checkpoints[0])
    end = timer()
    print(f"\nprolog: {end-start} sec.")

    assert np.array_equal(prolog, read_data)


@pytest.mark.parametrize("expected_file", ["gps-track-prolog-epilog.csv"])
def test_cut_off_prolog_epilog(
    read_data: ArrayLike,
    read_source: ArrayLike,
    get_checkpoints: List[Tuple[float, float, float, float]],
):
    start = timer()
    for _ in range(COUNTER):
        track = cut_off_prolog(
            cut_off_epilog(read_source, get_checkpoints[-1]), get_checkpoints[0]
        )
    end = timer()
    print(f"\ntrack: {end-start} sec.")

    assert np.array_equal(track, read_data)


@pytest.mark.parametrize("expected_file", ["gps-track-epilog-prolog.csv"])
def test_cut_off_epilog_prolog(
    read_data: ArrayLike,
    read_source: ArrayLike,
    get_checkpoints: List[Tuple[float, float, float, float]],
):
    start = timer()
    for _ in range(COUNTER):
        track = cut_off_epilog(
            cut_off_prolog(read_source, get_checkpoints[0]), get_checkpoints[-1]
        )
    end = timer()
    print(f"\ntrack: {end-start} sec.")

    assert np.array_equal(track, read_data)


@pytest.mark.parametrize("expected_file", ["gps-track-clear.csv"])
def test_clear_stops(
    read_data: ArrayLike,
    read_source: ArrayLike,
    get_checkpoints: List[Tuple[float, float, float, float]],
):
    start = timer()
    for _ in range(COUNTER):
        track = clear_stops(read_source, get_checkpoints)
    end = timer()
    print(f"\ntrack: {end-start} sec.")

    assert np.array_equal(track, read_data)


@pytest.mark.parametrize(
    ("expected_file", "interval", "length"),
    [
        ("gps-track-down-sample-050.csv", 50, 6532),
        ("gps-track-down-sample-100.csv", 100, 3363),
        ("gps-track-down-sample-200.csv", 200, 1702),
        ("gps-track-down-sample-500.csv", 500, 678),
        ("gps-track-down-sample-999.csv", 999, 335),
    ],
)
def test_down_sample(
    read_data: ArrayLike,
    expected_file: str,
    interval: int,
    length: int,
    read_source: ArrayLike,
    get_checkpoints: List[Tuple[float, float, float, float]],
    csv_file,
):
    start = timer()
    for _ in range(int(COUNTER / 10)):
        mask = down_sample_mask(read_source, interval=interval)
    end = timer()
    print(f"\nmask: {end - start} sec.")

    assert len(read_source[mask]) == length
    assert np.array_equal(read_source[mask], read_data)


def test_down_sample_compare(
    read_source: ArrayLike,
    get_checkpoints: List[Tuple[float, float, float, float]],
):
    start = timer()
    """
    for _ in range(int(COUNTER / 10)):
        mask = down_sample_mask_pure(read_source)
    """
    end1 = timer()
    for _ in range(int(COUNTER / 10)):
        np_mask = down_sample_mask(read_source)
    end2 = timer()
    print(f"\nmask: {end1 - start} / {end2 - end1}  sec.")

    assert (len(read_source), len(read_source[np_mask])) == (
        56255,
        # len(read_source[mask]),  3359,
        3363,
    )


def test_down_first(
    read_source: ArrayLike, get_checkpoints: List[Tuple[float, float, float, float]]
):
    start = timer()
    for _ in range(int(COUNTER / 10)):
        clear_stops(
            cut_off_prolog(
                cut_off_epilog(
                    read_source[down_sample_mask(read_source)], get_checkpoints[-1]
                ),
                get_checkpoints[0],
            ),
            get_checkpoints,
        )
    end = timer()
    print(f"\nmask first: {end-start} sec.")


def test_down_last(
    read_source: ArrayLike, get_checkpoints: List[Tuple[float, float, float, float]]
):
    start = timer()
    for _ in range(int(COUNTER / 10)):
        track = clear_stops(
            cut_off_prolog(
                cut_off_epilog(read_source, get_checkpoints[-1]), get_checkpoints[0]
            ),
            get_checkpoints,
        )
        down_sample_mask(track)
    end = timer()
    print(f"\nmask last: {end-start} sec.")
