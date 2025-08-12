from __future__ import annotations

import json
import logging
import os
from base64 import b64decode
from datetime import datetime

import firebase_admin
from google.cloud import functions_v1
import google.cloud.logging
import gpxpy
from brevet_top_gcp_utils import (create_document, firestore_to_track_point,
                                  get_checkpoints, resolve_document)
from brevet_top_gcp_utils.auth_decorator import authenticated
from brevet_top_numpy_utils import FloatArray, build_array_from_gpx, build_array_from_fit
from brevet_top_plot_a_route.utils import geo_distance
from brevet_top_strava import (ActivityError, build_checkpoint_list,
                               track_alignment, ActivityNotFound)
from flask import Request
from flask_cors import cross_origin
from pytz import utc

log_client = google.cloud.logging.Client()
log_client.get_default_handler()
log_client.setup_logging(log_level=logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)

firebase_admin.initialize_app()
db_client = google.cloud.firestore.Client()


@cross_origin(methods="POST")
@authenticated
def upload_track(request: Request, auth: dict):
    """
    Compare the GPX track to a brevet route / checkpoints

    :param request: HTTP request
    :param auth: exposed authorization header
    """
    logging.debug(f"Request {request}")

    data: dict = request.get_json().get("data", {})

    # brevet.top document uid
    brevet_uid: str | None = data.get("brevetUid")

    # brevet.top rider uid
    rider_uid: str | None = data.get("riderUid")

    # GPX track as a text
    track: str = data.get("track", "")

    if not track:
        return json.dumps({"data": {"message": "No track given", "error": 400}}), 400

    if not brevet_uid:
        return json.dumps({"data": {"message": "Provide either a brevet UID", "error": 400}}), 400

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

    # Update distances
    for i in range(1, len(draft)):
        lat1, lng1, _, distance1 = draft[i - 1]
        lat2, lng2, _, distance2 = draft[i]
        if distance2:
            continue
        draft[i][3] = distance1 + geo_distance(lat1, lng1, lat2, lng2)

    try:
        logging.info(f"Uploading track to brevet {brevet_uid} rider {rider_uid}")
        if rider_uid != auth.get("uid"):
            return (
                json.dumps(
                    {
                        "data": {
                            "message": f"Forbidden access to {rider_uid}",
                            "error": 403,
                        }
                    }
                ),
                403,
            )

        try:
            brevet_doc = resolve_document(brevet_uid, db=db_client)
        except ValueError as error:
            return json.dumps({"data": {"message": str(error), "error": 404}}), 404

        brevet_dict = brevet_doc.get().to_dict()

        # convert stored GeoPoints
        brevet_dict["short_track"] = [
            #  TODO: rename to shortTrack
            firestore_to_track_point(p)
            for p in brevet_dict.get("short_track", [])
        ]

        # prepare a list of control points (check-in / check-out) mandatory to visit
        cps = brevet_dict["checkpoints"]
        if cps:
            cps = [{**cp, "coordinates": firestore_to_track_point(cp)} for cp in cps if cp.get("uid")]
        else:
            cps = get_checkpoints(brevet_dict["uid"], db=db_client)
        checkpoints, ids = build_checkpoint_list(cps)

        # the main alignment routine
        points = track_alignment(brevet_dict, draft, checkpoints)
        logging.info(f"{len(points)} points found")

        # register check-ins / check-outs
        for i, cp in enumerate(points):
            # test for NaN
            if cp[2] == cp[2]:
                create_rider_barcode(
                    data["riderUid"],
                    code=ids[i],
                    time=datetime.fromtimestamp(int(cp[2]), tz=utc),
                )
        client = functions_v1.CloudFunctionsServiceClient()
        client.call_function(request=functions_v1.CallFunctionRequest(
            name=client.cloud_function_path(
                project=os.getenv('GCLOUD_PROJECT'),
                location=os.getenv('FUNCTION_REGION'),
                function="saveResults",
            ),
            data='{"data": {"brevetUid": "%s"}}' % brevet_dict["uid"]
        ))

        return json.dumps({"data": {"message": len(points)}}), 200

    except (ActivityError, ActivityNotFound) as error:
        return json.dumps({"data": {"message": str(error), "error": 400}}), 200
    except Exception as error:
        logging.exception(error)
        return json.dumps({"data": {"message": str(error), "error": 500}}), 500


def create_rider_barcode(rider_uid: str, code: str, time: datetime) -> str:
    return create_document(
        f"riders/{rider_uid}/barcodes",
        {
            "code": code,
            "control": rider_uid,
            "owner": rider_uid,
            "time": time,
            "message": "new",
        },
        db=db_client,
    )
