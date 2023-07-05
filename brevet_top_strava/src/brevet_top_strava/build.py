from typing import List, Tuple

import dateutil.parser
import numpy as np

from brevet_top_numpy_utils import FloatArray


def build_checkpoint_list(
    checkpoints: List[dict],
) -> Tuple[FloatArray, List[str]]:
    """
    Reshape a checkpoint list of dicts to a list of arrays for a better performance.

    :param checkpoints: a list of checkpoints {coordinates: [latitude, longitude], distance, uid}
    :return: a list of [latitude, longitude, distance, timestamp=0], and a uid list

    Each point is copied twice - excluding the start and the end - to match check-in and check-out.
    """
    ids: List[str] = []
    points: List[Tuple[float, float, float, float]] = []
    for cp in checkpoints:
        points.extend(
            (
                (
                    cp["coordinates"][0],
                    cp["coordinates"][1],
                    cp.get("distance", 0) * 1000,
                    0,
                ),
            )
            * 2
        )
        ids.extend([cp["uid"]] * 2)
    if len(checkpoints) == 1:
        return np.array(points[0:-1], dtype=np.float64), ids[0:-1]
    return np.array(points[1:-1], dtype=np.float64), ids[1:-1]


def get_track_start_point(activity: dict) -> Tuple[float, float, float, float]:
    """
    Select the first point of the track

    :param activity: Strava activity dict
    :return: a tuple (latitude, longitude, timestamp, distance=0)
    """
    lat: float = float(activity["start_latlng"][0])
    lng: float = float(activity["start_latlng"][1])
    try:
        date: float = dateutil.parser.isoparse(
            activity.get("start_date", "")
        ).timestamp()
    except ValueError:
        return lat, lng, 0.0, 0.0

    return lat, lng, date, 0.0


def build_track(
    start_timestamp: float, start_distance: float, stream: dict
) -> FloatArray:
    """
    Compose a track sequence out of Strava streams.

    :param start_timestamp: timestamp of the start point
    :param start_distance: distance shift of the start point
    :param stream: Strava streams {latlng, distance, time}
    :return: array of [latitude, longitude, timestamp, distance]
    """
    lat, lng = np.array(stream.get("latlng", {}).get("data", []), dtype=np.float64).T
    distance: FloatArray = (
        np.array(stream.get("distance", {}).get("data", []), dtype=np.float64)
        + start_distance
    )
    time: FloatArray = (
        np.array(stream.get("time", {}).get("data", []), dtype=np.float64)
        + start_timestamp
    )

    return np.array([lat, lng, time, distance], dtype=np.float64).T
