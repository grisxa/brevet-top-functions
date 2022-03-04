from datetime import datetime
from typing import List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pytest
from rdp import rdp

from plot_a_route import (
    ROUTE_SIMPLIFY_FACTOR,
)
from strava import (
    cut_off_prolog,
    cut_off_epilog,
    np_align_track_to_route,
    TRACK_SIMPLIFY_FACTOR,
)


@pytest.mark.parametrize(
    ("track_name", "expected", "length"),
    [
        ("jogging.gpx", -211.33, (39, 7, 7)),
        ("jogging-2.gpx", -722.519, (220, 7, 7)),
        ("jogging-3.gpx", -624.105, (307, 7, 7)),
        ("jogging-5.gpx", -497.027, (265, 7, 7)),
    ],
)
def x_test_gpx_route(
    track_name: str,
    expected: float,
    length: Tuple[int, int, int],
    gpx_route: List[Tuple[float, float, float, float]],
    gpx_track: List[Tuple[float, float, float, float]],
    gpx_waypoints: List[Tuple[float, float, int]],
):
    route = np.array(gpx_route)
    route_mask = rdp(route[:, :2], ROUTE_SIMPLIFY_FACTOR, algo="iter", return_mask=True)
    draft = np.array(gpx_track)
    track = cut_off_prolog(cut_off_epilog(draft, route[-1]), route[0])
    track_mask = rdp(track[:, :3], TRACK_SIMPLIFY_FACTOR, algo="iter", return_mask=True)

    cost, reduced = np_align_track_to_route(route[route_mask], track[track_mask])

    plt.plot(route[route_mask].T[1], route[route_mask].T[0], marker="x")
    plt.plot(reduced.T[1], reduced.T[0], marker="o")
    plt.plot(track[track_mask].T[1], track[track_mask].T[0], marker="+")
    plt.plot(track.T[1], track.T[0], marker=".")
    # plt.show()

    assert round(cost, 3) == expected
    assert (len(track), len(route[route_mask]), len(reduced)) == length


@pytest.mark.parametrize(
    ("track_name", "expected", "length"),
    [
        ("jogging.gpx", -870.924, (39, 6, 6)),
        ("jogging-2.gpx", -867.415, (598, 6, 6)),
        ("jogging-3.gpx", -484.468, (684, 6, 6)),
        ("jogging-5.gpx", -1157.605, (651, 6, 6)),
    ],
)
def x_test_gpx_checkpoints(
    track_name: str,
    expected: float,
    length: Tuple[int, int, int],
    gpx_route: List[Tuple[float, float, float, float]],
    gpx_track: List[Tuple[float, float, float, float]],
    gpx_waypoints: List[Tuple[float, float, int]],
    get_checkpoints: List[Tuple[float, float, float, float]],
):
    checkpoints = np.array(get_checkpoints)

    draft = np.array(gpx_track)
    track = cut_off_prolog(
        cut_off_epilog(draft, get_checkpoints[-1]), get_checkpoints[0]
    )
    track_mask = rdp(track[:, :3], TRACK_SIMPLIFY_FACTOR, algo="iter", return_mask=True)

    cost, reduced = np_align_track_to_route(checkpoints, track[track_mask])

    plt.plot(checkpoints.T[1], checkpoints.T[0], marker="x")
    plt.plot(reduced.T[1], reduced.T[0], marker="o")
    plt.plot(track.T[1], track.T[0], marker=".")
    # plt.show()
    # assert False

    for i, cp in enumerate(reduced):
        # test for NaN
        if cp[3] == cp[3]:
            print(f"control {i}. {cp[0:2]} {cp[3]} {datetime.fromtimestamp(cp[2])}")

    assert round(cost, 3) == expected
    assert (len(draft), len(checkpoints), len(reduced)) == length
