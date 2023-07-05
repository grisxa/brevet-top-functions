import csv
import pathlib
from timeit import default_timer as timer
from typing import List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pytest
from numpy.typing import ArrayLike
from rdp import rdp

from brevet_top_plot_a_route import (
    ROUTE_SIMPLIFY_FACTOR,
    route_down_sample_factor,
)
from brevet_top_strava import (
    cut_off_prolog,
    cut_off_epilog,
    np_align_track_to_route,
    clear_stops,
)
from brevet_top_strava.math import np_geo_distance_track
from brevet_top_strava.simplify import down_sample_mask, CHECKPOINT_RADIUS


def read_scores() -> dict:
    file_path = pathlib.Path(__file__).parent.absolute() / "files" / "strava-tracks.csv"
    with open(file_path, newline="", encoding="utf-8") as csv_file:
        table = csv.reader(csv_file, delimiter=",", quotechar='"')
        for row in table:
            yield row


@pytest.fixture
def csv_file():
    file_path = (
        pathlib.Path(__file__).parent.absolute() / "files" / "strava-tracks-new.csv"
    )
    with open(file_path, "a", newline="", encoding="utf-8") as csv_file_handler:
        yield csv.writer(
            csv_file_handler, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
        )


def pytest_generate_tests(metafunc):
    if "route_name" in metafunc.fixturenames:
        metafunc.parametrize(
            "route_name,track_name,score,"
            "route_len,track_len,down_len,short_len,simple_len,match_len,diff",
            read_scores(),
        )


def route_mask_cache(name: str, route: ArrayLike, cache: dict = {}) -> ArrayLike:
    if name not in cache:
        first = rdp(route[:, :2], ROUTE_SIMPLIFY_FACTOR, algo="iter")
        cache[name] = rdp(
            route[:, :2],
            route_down_sample_factor(len(route), len(first)),
            algo="iter",
            return_mask=True,
        )
    return cache[name]


def x_test_np_gpx_brevet(
    route_name: str,
    track_name: str,
    score: float,
    route_len: int,
    track_len: int,
    down_len: int,
    short_len: int,
    simple_len: int,
    match_len: int,
    diff: float,
    gpx_track_point: Tuple[float, float, float, float],
    get_route: List[Tuple[float, float, float, float]],
    get_checkpoints: List[Tuple[float, float, float, float]],
    csv_file,
):
    full_route = np.array(get_route, dtype=np.float64)

    start = timer()
    route_mask = route_mask_cache(route_name, full_route)
    end = timer()
    print(f"{track_name} route rdp time {end - start}")
    route = full_route[route_mask]

    draft = np.array(list(gpx_track_point), dtype=np.float64)
    checkpoints = np.array(get_checkpoints, dtype=np.float64)

    # for point in draft:
    #    csv_file.writerow(point.tolist())

    """
    assert len(route) == 92
    assert len(draft) == 13176
    assert len(checkpoints) == 16

    assert np.sum(route[:, 0]) == 5696.3386417
    assert np.sum(route[:, 1]) == 3014.2516266999996
    assert np.sum(route[:, 3]) == 28733917.29039386
    #                             28733915.214295506

    assert np.sum(draft[:, 0]) == 815628.6317980001
    assert np.sum(draft[:, 1]) == 432893.45070800005
    assert np.sum(draft[:, 2]) == 21463450720585.0
    assert np.sum(draft[:, 3]) == 4136496739.893238
    #                             4140305660.3

    assert np.sum(checkpoints[:, 0]) == 990.5079006000001
    assert np.sum(checkpoints[:, 1]) == 522.7269686
    assert np.sum(checkpoints[:, 3]) == 5280000.0
    """

    assert CHECKPOINT_RADIUS == 100
    start = timer()
    down_sample = down_sample_mask(draft)

    track = clear_stops(
        cut_off_prolog(
            cut_off_epilog(draft[down_sample], checkpoints[-1]),
            checkpoints[0],
        ),
        checkpoints,
    )
    end = timer()
    print(f"{track_name} track cut time {end - start}")

    """
    assert np.sum(track[:, 0]) == 274159.349531
    assert np.sum(track[:, 1]) == 145644.086359
    assert np.sum(track[:, 2]) == 7213116304023.0
    assert np.sum(track[:, 3]) == 1342840286.9559653
    #                             1344077537.5
    """

    start = timer()
    cost, reduced = np_align_track_to_route(route, track)
    cost_reviewed = np_geo_distance_track(route, reduced, factor=0)
    end = timer()
    print(f"{track_name} track align time {end - start}")
    # TODO: review times

    """
    assert len(reduced) == 92
    # assert cost == -32626.082002996744
    assert cost_reviewed == 3696.592902996742

    assert np.sum(reduced[:, 0]) == 5696.3391729999985
    assert np.sum(reduced[:, 1]) == 3014.261073
    assert np.sum(reduced[:, 2]) == 149866262600.0
    assert np.sum(reduced[:, 3]) == 28902879.09926257
    #                               28929489.1
    """

    csv_file.writerow(
        [route_name, track_name, round(cost, 3)]
        + [
            len(full_route),
            len(draft),
            len(draft[down_sample]),
            len(track),
            len(track),
            len(reduced),
        ]
        + [round(cost_reviewed, 3)]
    )

    plt.title(track_name)
    plt.plot(route.T[1], route.T[0], marker="x")
    plt.plot(draft[down_sample].T[1], draft[down_sample].T[0], marker=".")
    plt.plot(reduced.T[1], reduced.T[0], marker="o")
    # plt.show()

    assert len(full_route), len(route) == (int(route_len), int(match_len))
    assert len(draft) == int(track_len)
    assert len(draft[down_sample]) == int(down_len)
    assert len(track) == int(short_len)
    assert len(reduced[reduced.all(axis=1) != None]) == int(match_len)  # noqa: E711

    assert round(cost, 3) == float(score)
    assert round(cost_reviewed, 3) == float(diff)
    # WARNING: Strava distances differ from local calculation
    # assert cost >= -len(reduced) * TRACK_DEVIATION_MAX
    # assert cost_reviewed < len(route) * TRACK_DEVIATION_MIN
