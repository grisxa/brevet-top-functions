import json
import logging
from base64 import b64decode

import google.cloud.logging
import gpxpy
import numpy as np
from brevet_top_numpy_utils import FloatArray
from brevet_top_strava import (ActivityError, track_alignment, ActivityNotFound)
from flask import Request
from flask_cors import cross_origin
from garmin_fit_sdk import Decoder, Stream, Profile
from gpxpy.gpx import GPX
from more_itertools import flatten

log_client = google.cloud.logging.Client()
log_client.get_default_handler()
log_client.setup_logging(log_level=logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)

GARMIN_FIT_BASE = 11930465
TRACK_DEVIATION_FACTOR: int = 600
CONTROL_DEVIATION_FACTOR: int = 500


@cross_origin(methods="POST")
def upload_track_other(request: Request):
    """
    Compare the GPX track to a brevet route / checkpoints

    :param request: HTTP request
    """
    logging.debug(f"Request {request}")

    data: dict = request.get_json().get("data", {})

    # checkpoints as a list of [latitude, longitude, distance, 0]
    checkpoints = data.get("checkpoints", [])

    # GPX track as a text
    track: str = data.get("track", "")

    if not track:
        return json.dumps({"data": {"message": "No track given", "error": 400}}), 400

    if not checkpoints:
        return json.dumps({"data": {"message": "Provide a checkpoint list", "error": 400}}), 400

    track_data = b64decode(track.removeprefix("data:application/octet-stream;base64,"))
    if track_data.startswith(b'<?xml'):
        draft: FloatArray = build_array_from_gpx(gpxpy.parse(track_data))
    elif track_data[8:12] == b'.FIT':
        draft: FloatArray = build_array_from_fit(track_data)
    else:
        return json.dumps({"data": {"message": "Unsupported file type", "error": 400}}), 400

    logging.info(f"{len(draft)} points in the track")

    if len(draft) == 0:
        return json.dumps({"data": {"message": "Empty track", "error": 400}}), 400

    try:
        distance = checkpoints[-1][2]
        brevet = {
            "short_track": checkpoints,
            "trackDeviation": distance * TRACK_DEVIATION_FACTOR,
            "controlDeviation": len(checkpoints) * CONTROL_DEVIATION_FACTOR,
        }
        copies = list(flatten([cp] * 2 for cp in checkpoints))

        if len(checkpoints) == 1:
            checkpoints = np.array(copies[0:-1], dtype=np.float64)
        else:
            checkpoints = np.array(copies[1:-1], dtype=np.float64)
        points = track_alignment(brevet, draft, checkpoints)

        return json.dumps({"data": {"message": points}}), 200
    except (ActivityError, ActivityNotFound) as error:
        return json.dumps({"data": {"message": str(error), "error": 400}}), 200
    except Exception as error:
        logging.exception(error)
        return json.dumps({"data": {"message": str(error), "error": 500}}), 500

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
            track_points.append([
                message.get("position_lat", 0) / GARMIN_FIT_BASE,
                message.get("position_long", 0) / GARMIN_FIT_BASE,
                message.get("timestamp").timestamp(),
                message.get("distance", 0) / 1000,
            ])

    decoder.read(mesg_listener=mesg_listener)
    return np.concatenate((draft, track_points), axis=0)
