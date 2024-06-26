import numpy as np

from brevet_top_numpy_utils import FloatArray, np_geo_distance

# from plot_a_route import geo_distance

CHECKPOINT_RADIUS = 100  # meters
DOWN_SAMPLE_INTERVAL = 100  # meters
LOOKUP_AHEAD_POINTS = 200


def clear_stops(track: FloatArray, checkpoints: FloatArray) -> FloatArray:
    """
    Remove track points around checkpoints where the rider likely to stop.

    :param track: the track points
    :param checkpoints: the checkpoint list
    :return: reduced track
    """
    mask = [True] * track.shape[0]
    for cp in checkpoints:
        mask = mask & (np_geo_distance(cp, track, factor=np.float64(0.0)) > CHECKPOINT_RADIUS)
    return track[mask]


def cut_off_epilog(track: FloatArray, end: FloatArray) -> FloatArray:
    """
    Remove points after the last route point.

    :param track: a sequence of track points
    :param end: the last point [latitude, longitude, timestamp, distance]
    :return: the rest of the track before the end point
    """
    if len(track) < 2:
        return track
    backwards: FloatArray = np.flipud(track)
    # index of the nearest point to the finish
    offset: int = np.argmax(np_geo_distance(end, backwards) < CHECKPOINT_RADIUS)  # type: ignore[assignment]
    return np.flipud(backwards[offset:])


def cut_off_prolog(track: FloatArray, start: FloatArray) -> FloatArray:
    """
    Remove points before the start route point.

    :param track: a sequence of track points
    :param start: the start point [latitude, longitude, timestamp, distance]
    :return: the rest of the track after the start point
    """
    if len(track) < 2:
        return track
    # index of the nearest point to the start
    offset: int = np.argmax(np_geo_distance(start, track) < CHECKPOINT_RADIUS)  # type: ignore[assignment]
    # how many meters before the start
    prolog: np.float64 = track[offset][3]
    # decrease the distance column
    track[offset:, 3] = track[offset:, 3] - prolog
    return track[offset:]


def down_sample_mask(
    track: FloatArray,
    ahead: int = LOOKUP_AHEAD_POINTS,
    interval: int = DOWN_SAMPLE_INTERVAL,
) -> FloatArray:
    """
    Reduce track by leaving one point every interval (meters).
    Updates the number of points to look ahead dynamically according to the current results.

    :param track: the track to process
    :param ahead: [dynamic] number of points to look ahead (defaults to 200)
    :param interval: minimal distance between points
    :return: a mask [True|False] for the source points
    """
    mask = np.full(shape=(track.shape[0]), fill_value=False, dtype=bool)
    i = 0
    # till the end of the track
    while i < track.shape[0] - 1:
        # accept the current point
        mask[i] = True
        # build a distance vector ahead : [ i+1, ... i+ahead ]
        distance: FloatArray = np_geo_distance(track[i], track[i + 1 : i + ahead + 1])  # noqa: E203
        # find the first point far enough
        offset: int = np.argmax(~np.isnan(distance) & (distance > interval))  # type: ignore[assignment]
        if offset == 0:
            # the first point is good
            if not np.isnan(distance[0]) and distance[0] > interval:
                i += 1
            # not found in the current interval
            else:
                # finish searching
                if i + ahead > track.shape[0]:
                    break
                # increase the interval
                ahead = int(ahead * 1.5)
                continue
        # jump to that point
        else:
            i += offset + 1
        # decrease the interval
        ahead = int((ahead + offset + 19) / 2)
    return mask
