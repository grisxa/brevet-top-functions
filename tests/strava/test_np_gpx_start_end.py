import csv
import pathlib
from typing import List, Tuple

import numpy as np
import pytest

from strava.simplify import clear_stops
from strava.simplify import cut_off_prolog, cut_off_epilog


def read_scores() -> dict:
    file_path = (
        pathlib.Path(__file__).parent.absolute() / "files" / "strava-start-end.csv"
    )
    with open(file_path, newline="", encoding="utf-8") as csv_file:
        table = csv.reader(csv_file, delimiter=",", quotechar='"')
        for row in table:
            yield row[0], row[1], [float(x) for x in row[2:]]


@pytest.fixture
def csv_file():
    file_path = (
        pathlib.Path(__file__).parent.absolute() / "files" / "strava-start-end-new.csv"
    )
    with open(file_path, "a", newline="", encoding="utf-8") as csv_file_handler:
        yield csv.writer(
            csv_file_handler, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
        )


def pytest_generate_tests(metafunc):
    if "points" in metafunc.fixturenames:
        metafunc.parametrize("route_name,track_name,points", read_scores())


def x_test_gpx_start_end(
    route_name: str,
    track_name: str,
    points: List[float],
    gpx_track: List[Tuple[float, float, float, float]],
    get_checkpoints: List[Tuple[float, float, float, float]],
    csv_file,
):
    draft = np.array(gpx_track)
    epilog = cut_off_epilog(draft, get_checkpoints[-1])
    prolog = cut_off_prolog(epilog, get_checkpoints[0])
    clear = clear_stops(prolog, get_checkpoints)

    csv_file.writerow(
        [route_name, track_name]
        + prolog[0].tolist()
        + epilog[-1].tolist()
        + clear[0].tolist()
        + clear[-1].tolist()
    )

    assert prolog[0].tolist() == points[0:4]
    assert epilog[-1].tolist() == points[4:8]
    assert clear[0].tolist() == points[8:12]
    assert clear[-1].tolist() == points[12:16]

    """
    assert (
        datetime.fromtimestamp(prolog[0][2], tz=timezone.utc).isoformat(),
        datetime.fromtimestamp(epilog[-1][2], tz=timezone.utc).isoformat(),
        datetime.fromtimestamp(clear[0][2], tz=timezone.utc).isoformat(),
        datetime.fromtimestamp(clear[-1][2], tz=timezone.utc).isoformat(),
    ) == "1234"
    """
