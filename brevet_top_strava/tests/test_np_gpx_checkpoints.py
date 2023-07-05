import csv
import pathlib
from datetime import datetime
from typing import List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pytest

from brevet_top_strava import CONTROL_DEVIATION_FACTOR
from brevet_top_strava.math import np_align_track_to_route, np_geo_distance_track
from brevet_top_strava.simplify import clear_stops, down_sample_mask, CHECKPOINT_RADIUS
from brevet_top_strava.simplify import cut_off_prolog, cut_off_epilog


def read_scores() -> dict:
    file_path = (
        pathlib.Path(__file__).parent.absolute() / "files" / "strava-checkpoints.csv"
    )
    with open(file_path, newline="", encoding="utf-8") as csv_file:
        table = csv.reader(csv_file, delimiter=",", quotechar='"')
        for row in table:
            yield *row[0:3], row[3:6], row[6], row[7:]


@pytest.fixture
def csv_file():
    file_path = (
        pathlib.Path(__file__).parent.absolute()
        / "files"
        / "strava-checkpoints-new.csv"
    )
    with open(file_path, "a", newline="", encoding="utf-8") as csv_file_handler:
        yield csv.writer(
            csv_file_handler, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
        )


def pytest_generate_tests(metafunc):
    if "score" in metafunc.fixturenames:
        metafunc.parametrize(
            "route_name,track_name,score,length,diff,time", read_scores()
        )


def x_test_gpx_checkpoints(
    route_name: str,
    track_name: str,
    score: float,
    length: List[int],
    diff: float,
    time: List[float],
    gpx_track_point: Tuple[float, float, float, float],
    get_checkpoints: List[Tuple[float, float, float, float]],
    csv_file,
):
    checkpoints = np.array(get_checkpoints, dtype=np.float64)
    draft = np.array(list(gpx_track_point), dtype=np.float64)

    assert CHECKPOINT_RADIUS == 100
    down_sample = down_sample_mask(draft)
    track = clear_stops(
        cut_off_prolog(
            cut_off_epilog(draft[down_sample], checkpoints[-1]),
            checkpoints[0],
        ),
        checkpoints,
    )

    cost, reduced = np_align_track_to_route(checkpoints, track)
    cost_reviewed = np_geo_distance_track(checkpoints, reduced, factor=0)

    csv_file.writerow(
        [route_name, track_name, round(cost, 3)]
        + [len(checkpoints), len(track), len(reduced)]
        + [round(cost_reviewed, 3)]
        + reduced.T[2].tolist()
    )

    for i, cp in enumerate(reduced):
        # test for NaN
        if cp[3] == cp[3]:
            pass
            print(
                f"control {i}. {cp[0:2]} {cp[3]} {datetime.fromtimestamp(cp[2])} / {cp[2]}"
            )

    plt.plot(checkpoints.T[1], checkpoints.T[0], marker="x")
    plt.plot(reduced.T[1], reduced.T[0], marker="o")
    plt.plot(track.T[1], track.T[0], marker=".")
    # plt.show()

    assert round(cost, 3) == float(score)
    assert round(cost_reviewed, 3) == float(diff)
    assert cost_reviewed < (len(checkpoints) / 2.0 + 1) * CONTROL_DEVIATION_FACTOR
    assert [len(checkpoints), len(track), len(reduced)] == [int(ln) for ln in length]

    # TODO: check times
    assert time == [str(cp[2]) for cp in reduced]
    # assert False
