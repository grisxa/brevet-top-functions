from itertools import compress
from typing import List, Tuple

from hirschberg import hirschberg
from plot_a_route import geo_distance
from strava.track_point import StravaTrackPoint
from strava.math import DISTANCE_FACTOR


def align_track_to_route(
    route: List[StravaTrackPoint], track: List[StravaTrackPoint]
) -> Tuple[float, List[StravaTrackPoint]]:
    first, second, cost = hirschberg(
        route,
        track,
        deletion_cost=-3000,
        insertion_cost=0,
        cost_function=distance_cost,
    )
    return cost, list(compress(second, first))


def distance_cost(a: StravaTrackPoint, b: StravaTrackPoint) -> float:
    if a is None or b is None:
        return 0
    distance_shift = (
        0
        if a.distance is None or b.distance is None
        else abs(a.distance - b.distance) * DISTANCE_FACTOR
    )
    step_away = geo_distance(a.lat, a.lng, b.lat, b.lng) + distance_shift
    return step_away
