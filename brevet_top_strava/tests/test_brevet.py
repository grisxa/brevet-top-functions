import json
import pathlib
from datetime import datetime, timedelta, timezone
from timeit import default_timer as timer
from typing import List, Tuple

import dateutil.parser
import numpy as np
from matplotlib import pyplot as plt
from rdp import rdp

from brevet_top_numpy_utils import FloatArray
from brevet_top_plot_a_route import ROUTE_SIMPLIFY_FACTOR, route_down_sample_factor
from brevet_top_strava import (
    down_sample_mask,
    np_align_track_to_route,
    np_geo_distance_track,
    TRACK_DEVIATION_MAX,
)
from brevet_top_strava.simplify import (
    CHECKPOINT_RADIUS,
    cut_off_epilog,
    cut_off_prolog,
    clear_stops,
)


def brevet_registry() -> dict:
    file_path = (
        pathlib.Path(__file__).parent.absolute() / "files" / "brevet-registry.json"
    )
    with open(file_path, encoding="utf-8") as registry:
        return json.load(registry)


def read_registry(brevet_registry: dict):
    for brevet_name in brevet_registry.keys():
        route_path = f"{brevet_name}/route.gpx"

        tracks = brevet_registry[brevet_name].pop("tracks", {})
        for track_name in tracks.keys():
            track_path = f"{brevet_name}/{track_name}.gpx"

            # if track_path != "20210814-карельский-600/седова-11344374-5799784598.gpx":
            #    continue

            yield route_path, track_path, brevet_registry[brevet_name], tracks[
                track_name
            ]


def pytest_generate_tests(metafunc):
    if "route_name" in metafunc.fixturenames:
        metafunc.parametrize(
            "route_name,track_name,route_info,track_info",
            read_registry(brevet_registry()),
        )


def route_mask_cache(name: str, route: FloatArray, cache: dict = {}) -> FloatArray:
    if name not in cache:
        first_try = rdp(route[:, :2], ROUTE_SIMPLIFY_FACTOR, algo="iter")
        cache[name] = rdp(
            route[:, :2],
            route_down_sample_factor(len(route), len(first_try)),
            algo="iter",
            return_mask=True,
        )
    return cache[name]


def x_test_brevet(
    route_name: str,
    track_name: str,
    route_info: dict,
    track_info: dict,
    get_route: List[Tuple[float, float, float, float]],
    get_track: List[Tuple[float, float, float, float]],
    get_checkpoints: List[Tuple[float, float, float, float]],
):
    # check if the route has been read correctly
    assert len(get_route) == route_info["points"]["full"]
    assert len(get_checkpoints) == route_info["checkpoints"]

    # check if the track has been read correctly
    assert len(get_track) == track_info["points"]["full"]

    full_route = np.array(get_route, dtype=np.float64)
    full_track = np.array(get_track, dtype=np.float64)
    checkpoints = np.array(get_checkpoints, dtype=np.float64)

    assert ROUTE_SIMPLIFY_FACTOR == 0.001
    start = timer()
    route_mask = route_mask_cache(route_name, full_route)
    end = timer()
    print(f"\n{track_name} route rdp time {end - start}")

    route = full_route[route_mask]
    assert len(route) == route_info["points"]["short"]

    assert CHECKPOINT_RADIUS == 100
    start = timer()
    sample_mask = down_sample_mask(full_track)
    short = full_track[sample_mask]
    if route_info.get("skip_trim"):
        trim = short
    else:
        trim = cut_off_prolog(
            cut_off_epilog(short, checkpoints[-1]),
            checkpoints[0],
        )
    track = clear_stops(trim, checkpoints)
    end = timer()
    print(f"{track_name} track cut time {end - start}")

    assert len(short) == track_info["points"]["short"]
    assert len(trim) == track_info["points"]["trim"]
    assert len(track) == track_info["points"]["clean"]

    start = timer()
    cost, reduced = np_align_track_to_route(route, track)
    difference = np_geo_distance_track(route, reduced, factor=0)
    end = timer()
    print(f"{track_name} track align time {end - start}")

    assert len(reduced) == track_info["points"]["reduced"]
    assert round(cost, 3) == track_info["score"][0]
    assert round(difference, 3) == track_info["diff"][0]

    # WARNING: Strava distances differ from local calculation
    if track_info["pass"]:
        pass
        assert cost >= -len(reduced) * TRACK_DEVIATION_MAX
    else:
        assert cost < -len(reduced) * TRACK_DEVIATION_MAX

    start = timer()
    cost, reduced = np_align_track_to_route(checkpoints, track)
    difference = np_geo_distance_track(checkpoints, reduced, factor=0)
    end = timer()
    print(f"{track_name} checkpoints align time {end - start}")

    assert round(cost, 3) == track_info["score"][1]
    assert round(difference, 3) == track_info["diff"][1]

    plt.title(track_name)
    plt.plot(route.T[1], route.T[0], marker="x")
    plt.plot(reduced.T[1], reduced.T[0], marker="o")
    # plt.show()

    # TODO: missing CP must have NaN
    visited = reduced[np.all(~np.isnan(reduced), axis=1)]
    assert len(visited) == len(track_info["checkpoints"])
    time_gap = timedelta(minutes=2)
    for i, cp in enumerate(visited):
        real_date = dateutil.parser.isoparse(track_info["checkpoints"][i])
        found_date = datetime.fromtimestamp(cp[2], tz=timezone.utc)
        print(f"control {i}. {cp[0:2]} {cp[3]} {found_date.isoformat()} / {cp[2]}")
        assert (real_date - time_gap) <= found_date <= (real_date + time_gap)
