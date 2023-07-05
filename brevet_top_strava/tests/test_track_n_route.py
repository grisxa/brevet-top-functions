import csv
import pathlib
from timeit import default_timer as timer

import numpy as np
import pytest
from matplotlib import pyplot as plt

from brevet_top_numpy_utils import FloatArray
from brevet_top_strava import (
    cut_off_prolog,
    cut_off_epilog,
    np_align_track_to_route,
    clear_stops,
)
from brevet_top_strava.math import (
    np_geo_distance_track,
    DISTANCE_FACTOR,
)
from brevet_top_strava.simplify import down_sample_mask


@pytest.fixture
def route() -> FloatArray:
    file_path = (
        pathlib.Path(__file__).parent.absolute()
        / "files"
        / "track_n_route"
        / "route.csv"
    )
    with open(file_path, newline="", encoding="utf-8") as csv_file:
        table = csv.reader(csv_file, delimiter=",", quotechar='"')
        return np.array([row for row in table], dtype=np.float64)


@pytest.fixture
def track() -> FloatArray:
    file_path = (
        pathlib.Path(__file__).parent.absolute()
        / "files"
        / "track_n_route"
        / "track.csv"
    )
    with open(file_path, newline="", encoding="utf-8") as csv_file:
        table = csv.reader(csv_file, delimiter=",", quotechar='"')
        return np.array([row for row in table], dtype=np.float64)


@pytest.fixture
def checkpoints() -> FloatArray:
    return np.array(
        [
            (61.794567, 34.376714, 0, 0),
            (62.4756046, 33.8108947, 0, 102000),
            (62.4756046, 33.8108947, 0, 102000),
            (61.8990356, 34.2402839, 0, 186000),
            (61.8990356, 34.2402839, 0, 186000),
            (61.8451562, 33.2059313, 0, 250000),
            (61.8451562, 33.2059313, 0, 250000),
            (62.0858942, 32.3777768, 0, 312000),
            (62.0858942, 32.3777768, 0, 312000),
            (61.6315222, 33.1801236, 0, 400000),
            (61.6315222, 33.1801236, 0, 400000),
            (61.6601033, 31.3930076, 0, 511000),
            (61.6601033, 31.3930076, 0, 511000),
            (61.9088612, 30.6221674, 0, 577000),
            (61.9088612, 30.6221674, 0, 577000),
            (61.700979, 30.689884, 0, 604000),
        ],
        dtype=np.float64,
    )


@pytest.fixture
def csv_file():
    file_path = (
        pathlib.Path(__file__).parent.absolute()
        / "files"
        / "track_n_route"
        / "reduced.csv"
    )
    with open(file_path, "a", newline="", encoding="utf-8") as csv_file_handler:
        yield csv.writer(
            csv_file_handler, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
        )


def test_track_n_route(
    route: FloatArray, track: FloatArray, checkpoints: FloatArray  # , csv_file
):

    assert len(route) == 92
    assert len(track) == 13176
    assert len(checkpoints) == 16
    assert DISTANCE_FACTOR == 0.001

    assert np.sum(route[:, 0]) == 5696.3386417
    assert np.sum(route[:, 1]) == 3014.2516266999996
    assert np.sum(route[:, 3]) == 28733915.214295506

    assert np.sum(track[:, 0]) == 815628.6317980001
    assert np.sum(track[:, 1]) == 432893.45070800005
    assert np.sum(track[:, 2]) == 21463450720585.0
    assert np.sum(track[:, 3]) == 4140305660.3

    assert np.sum(checkpoints[:, 0]) == 990.5079006000001
    assert np.sum(checkpoints[:, 1]) == 522.7269686
    assert np.sum(checkpoints[:, 3]) == 5280000.0

    start = timer()
    down_sample = down_sample_mask(track)

    draft: FloatArray = clear_stops(
        cut_off_prolog(
            cut_off_epilog(track[down_sample], checkpoints[-1]),
            checkpoints[0],
        ),
        checkpoints,
    )
    end = timer()
    print(f"\ncut time {end-start}")

    assert len(track[down_sample]) == 4443
    assert len(draft) == 4428

    assert np.sum(draft[:, 0]) == 274159.349531
    assert np.sum(draft[:, 1]) == 145644.086359
    assert np.sum(draft[:, 2]) == 7213116304023.0
    assert np.sum(draft[:, 3]) == 1344077537.5

    start = timer()
    cost, reduced = np_align_track_to_route(route, draft)

    cost_reviewed = np_geo_distance_track(route, reduced, factor=0)
    end = timer()
    print(f"\nalign time {end-start}")

    assert len(reduced) == 92
    assert round(cost, 3) == -3892.192
    assert round(cost_reviewed, 3) == 3696.592

    assert round(np.sum(reduced[:, 0]), 3) == 5696.339
    assert round(np.sum(reduced[:, 1]), 3) == 3014.261
    assert np.sum(reduced[:, 2]) == 149866262600.0
    assert np.sum(reduced[:, 3]) == 28929489.1

    # for point in reduced:
    #    csv_file.writerow(point.tolist())
    plt.plot(route.T[1], route.T[0], marker="x")
    plt.plot(reduced.T[1], reduced.T[0], marker=".")
    # plt.show()
