from typing import Tuple

from numpy_hirschberg import align

from brevet_top_numpy_utils import FloatArray, np_geo_distance

MAX_POINT_DISTANCE = 3000


def np_align_track_to_route(route: FloatArray, track: FloatArray) -> Tuple[float, FloatArray]:
    """
    Compare route and track sequences.

    :param route: original sequence to compare to
    :param track: GPS recorded points
    :return: a tuple (score, points)

    Use the score to decide if the match is good enough.
    Points are in form of array [latitude, longitude, timestamp, distance] or None
    """
    # logging.info(f"route len {len(route)} / track len {len(track)}")
    first, second, distance = align(
        route,
        track,
        deletion_cost=-MAX_POINT_DISTANCE,
        insertion_cost=0,
        cost_function=np_geo_distance,
    )
    mask = first.all(axis=1) != None  # noqa: E711
    second = second[mask]
    # second = second[second.all(axis=1) != None]  # noqa: E711
    return distance, second.astype(float)
