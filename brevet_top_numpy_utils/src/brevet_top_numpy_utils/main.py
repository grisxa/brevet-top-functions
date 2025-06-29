import numpy as np
from garmin_fit_sdk import Decoder, Profile, Stream
from gpxpy.gpx import GPX
from numpy import arccos, cos, isnan, radians, sin
from numpy import sum as np_sum

from . import FloatArray

DISTANCE_FACTOR = np.float64(0.001)
EARTH_RADIUS = np.float64(6371e3)
MAX_POINT_DISTANCE = 3000
GARMIN_FIT_BASE = 11930465


def np_geo_distance(
    point: FloatArray,
    track: FloatArray,
    factor: np.float64 = DISTANCE_FACTOR,
) -> FloatArray:
    """
    Calculate a distance from the given point to each point of the track.
    Note: altitude is being ignored.

    :param point: the subject point as [latitude, longitude, altitude, distance from the start]
    :param track: the track as a list of points
    :param factor: "distance from the start" multiplier
    :return: a list of distances
    """
    point_latitude, point_longitude = radians(point[0:2]).astype(np.float64)
    latitude_radians, longitude_radians = radians(track.T[0:2]).astype(np.float64)

    distance_shift = abs(track.T[3] - point[3]) * factor
    return distance_shift + EARTH_RADIUS * arccos(
        sin(point_latitude) * sin(latitude_radians)
        + cos(point_latitude) * cos(latitude_radians) * cos(longitude_radians - point_longitude)
    )


def np_geo_distance_track(
    source: FloatArray,
    target: FloatArray,
    factor: np.float64 = DISTANCE_FACTOR,
) -> np.float64:
    """
    Compares two tracks point by point and returns a total difference between them.
    The track is a NumPy list of float points [latitude, longitude, altitude, distance]
    The distance from start is also considered but may be tuned with the factor parameter
    (say, set to 0).

    :param source: the source track or route
    :param target: the target track
    :param factor: "distance from the start" multiplier
    :return:
    """
    source_lat_radians, source_lon_radians = radians(source.T[0:2].astype(float))
    target_lat_radians, target_lon_radians = radians(target.T[0:2].astype(float))

    distance_shift: FloatArray = abs(target.T[3] - source.T[3]) * factor
    difference: FloatArray = distance_shift + EARTH_RADIUS * arccos(
        sin(source_lat_radians) * sin(target_lat_radians)
        + cos(source_lat_radians) * cos(target_lat_radians) * cos(target_lon_radians - source_lon_radians)
    )
    np.nan_to_num(difference, copy=False, nan=MAX_POINT_DISTANCE)
    return np_sum(difference[~isnan(difference)])


def build_array_from_gpx(data: GPX) -> FloatArray:
    """
    Compose a track sequence out of GPX data. The point's comment may be a distance.

    :param data: the track data from the GPX file
    :return: array of [latitude, longitude, timestamp, distance]
    """
    draft: FloatArray = np.empty(shape=(0, 4), dtype=np.float64)
    for track in data.tracks:
        for segment in track.segments:
            points = [
                [
                    point.latitude,
                    point.longitude,
                    point.time.timestamp(),
                    float(point.comment or 0) / 1000,
                ]
                for point in segment.points
            ]
            draft = np.concatenate((draft, points), axis=0)
    return draft


def build_array_from_fit(data: bytes) -> FloatArray:
    """
    Compose a track sequence out of FIT data.

    :param data: the track data from the FIT file
    :return: array of [latitude, longitude, timestamp, distance]
    """
    stream = Stream.from_byte_array(bytearray(data))
    decoder = Decoder(stream)

    draft: FloatArray = np.empty(shape=(0, 4), dtype=np.float64)
    track_points = []

    def mesg_listener(mesg_num, message):
        if mesg_num == Profile['mesg_num']['RECORD']:
            track_points.append(
                [
                    message.get("position_lat", 0) / GARMIN_FIT_BASE,
                    message.get("position_long", 0) / GARMIN_FIT_BASE,
                    message.get("timestamp").timestamp(),
                    message.get("distance", 0) / 1000,
                ]
            )

    decoder.read(mesg_listener=mesg_listener)
    return np.concatenate((draft, track_points), axis=0)
