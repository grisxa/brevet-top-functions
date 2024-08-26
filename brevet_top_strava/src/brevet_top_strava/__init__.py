import logging
from timeit import default_timer as timer
from typing import List

import numpy as np

from brevet_top_numpy_utils import FloatArray, np_geo_distance_track

from .api import (auth_token, get_activities, get_activity, get_track_points,  # noqa: F401
                  refresh_tokens, TimeWindow, time_window, tokens_expired)  # noqa: F401
from .build import build_checkpoint_list  # noqa: F401
from .exceptions import ActivityError, ActivityNotFound, AthleteNotFound  # noqa: F401
from .math import np_align_track_to_route
from .simplify import (clear_stops, cut_off_epilog, cut_off_prolog,
                       down_sample_mask)

TRACK_SIMPLIFY_FACTOR: float = 0.0005
TRACK_DEVIATION_MAX: int = 200
TRACK_DEVIATION_MIN: int = 200
CONTROL_DEVIATION_FACTOR: int = 500


def search_strava_activities(brevet: dict, tokens: dict, checkpoints: FloatArray) -> FloatArray:
    """
    Search for activities in Strava matching the given brevet.
    """
    # get a list of Strava activities in the given time window
    activities: List[dict] = get_activities(time_window(brevet), auth_token(tokens))
    if len(activities) < 1:
        message = "No tracks found"
        logging.error(message)
        raise ActivityNotFound(message)

    # retrieve activities and transform to a track
    track: FloatArray = get_track_points(sorted(activities, key=lambda a: a["start_date"]), auth_token(tokens))

    return track_alignment(brevet, track, checkpoints)


def track_alignment(
    brevet: dict,
    draft: FloatArray,
    checkpoints: FloatArray,
) -> FloatArray:
    logging.info(f"Full track length {len(draft)}")

    start = timer()
    down_sample = down_sample_mask(draft)

    shortened: FloatArray = clear_stops(
        draft[down_sample]
        if brevet.get("skip_trim")
        else cut_off_prolog(
            cut_off_epilog(draft[down_sample], checkpoints[-1]),
            checkpoints[0],
        ),
        checkpoints,
    )
    logging.info(f"Short track length {len(shortened)}")

    if len(shortened) < 1:
        message = "Empty track"
        logging.error(message)
        raise ActivityNotFound(message)

    # evaluate route / track similarity TODO: rename to shortTrack
    short_track = brevet.get('short_track', [])
    cost, reduced = np_align_track_to_route(np.array(short_track), shortened)
    # WARNING: Strava distances differ from local calculation
    if cost < -brevet.get("trackDeviation", len(reduced) * TRACK_DEVIATION_MAX):
        message = f"Track deviation {cost}"
        logging.error(message)
        raise ActivityError(message)

    # re-calculate the cost ignoring distance from the start
    cost_reviewed = np_geo_distance_track(np.array(short_track), reduced, factor=np.float64(0))
    track_time = timer()
    logging.info(f"Total track difference {cost} / {cost_reviewed}, took {track_time-start} sec.")

    if cost_reviewed > brevet.get("trackDeviation", len(reduced) * TRACK_DEVIATION_MIN):
        message = f"Track deviation {cost_reviewed}"
        logging.error(message)
        raise ActivityError(message)

    # TODO: include checkpoints in the route and compare to the reduced track instead of shortened
    # evaluate checkpoints / track similarity
    cost, reduced = np_align_track_to_route(np.array(checkpoints), shortened)
    # re-calculate the cost ignoring distance from the start
    cost_reviewed = np_geo_distance_track(np.array(checkpoints), reduced, np.float64(0))
    cp_time = timer()
    logging.info(f"Total checkpoint difference {cost_reviewed}, took {cp_time-track_time} sec.")

    if cost_reviewed > brevet.get("controlDeviation", (len(checkpoints) / 2.0 + 1) * CONTROL_DEVIATION_FACTOR):
        message = f"Control point deviation {cost_reviewed}"
        logging.error(message)
        raise ActivityError(message)

    if len(reduced) < len(checkpoints) / 2.0 + 1:
        message = "Checkpoint missing"
        logging.error(message)
        raise ActivityError(message)

    # plt.plot(np.array(points).T[1], np.array(points).T[0], marker='x')
    # plt.plot(reduced.T[1], reduced.T[0], marker='o')
    # plt.plot(track.T[1], track.T[0], marker='.')
    # plt.show()

    # report controls / timestamps
    return reduced.tolist()


if __name__ == "__main__":
    # firebase.functions().useEmulator("localhost", 5001);
    pass
