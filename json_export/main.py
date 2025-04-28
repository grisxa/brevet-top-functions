import logging
from datetime import datetime, tzinfo

import firebase_admin
import google.cloud.firestore
import google.cloud.logging
from flask import Request, json
from flask_cors import cross_origin
from google.cloud.firestore import GeoPoint
from pytz import timezone
from timezonefinder import TimezoneFinder

from brevet_top_gcp_utils import resolve_document

log_client = google.cloud.logging.Client()
log_client.get_default_handler()
# log_client.setup_logging(log_level=logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)

firebase_admin.initialize_app()
db_client = google.cloud.firestore.Client()


@cross_origin(methods="GET")
def json_export(request: Request):
    """
    Export the brevet's results to JSON.
    Takes a field selection including the brevet description and rider checkins.

    :param request: HTTP request
    :return: JSON with results
    """
    logging.debug(f"Request {request}")

    if request.path.endswith("/brevets"):
        payload = db_client.document("brevets/list").get().to_dict().get("brevets", [])

        return (
            json.dumps(
                payload,
                ensure_ascii=False,
                default=serialize_google,
            ),
            200,
            {"Content-Type": "application/json"},
        )

    doc_uid: str = request.path.split("/brevet/")[-1]
    logging.info(f"Exporting results of the brevet {doc_uid}")

    try:
        brevet_doc = resolve_document(doc_uid, db=db_client)
    except ValueError as error:
        return json.dumps({"message": str(error)}), 404

    try:
        brevet_dict = brevet_doc.get().to_dict()
        payload = {
            key: brevet_dict.get(key)
            for key in [
                "uid",
                "name",
                "length",
                "startDate",
                "mapUrl",
                "checkpoints",
                "results",
                "track",
            ]
        }
    except Exception as error:
        return json.dumps({"message": str(error)}), 500

    time_zones: list[tzinfo | None] = []  # timezone for every checkpoint in brevet
    for cp in payload["checkpoints"]:
        time_zones.append(time_zone_finder(cp["coordinates"]))

    for r in payload["results"]:
        checkins: list[dict[str, datetime] | None] = payload["results"][r]["checkins"]
        # checkins correspond to checkpoints by order
        # thus cp_time_zone applied to checkin_time by order

        for cp_index, checkin_times in enumerate(checkins):
            # TODO: extract conversion
            cp_timezone = time_zones[cp_index]
            if checkin_times is not None and time_zones[cp_index] is not None:
                for time_index, time in checkin_times.items():
                    checkin_times[time_index] = time.astimezone(cp_timezone)

    if payload["startDate"] is not None and time_zones[0] is not None:
        payload["startDate"] = payload["startDate"].astimezone(time_zones[0])

    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            default=serialize_google,
        ),
        200,
        {"Content-Type": "application/json"},
    )


def serialize_google(x):
    if isinstance(x, datetime):
        return x.isoformat()
    if isinstance(x, GeoPoint):
        return {"lat": x.latitude, "lng": x.longitude}
    return str(x)


# TODO: consider namedtuple("LatLng", ["lat", "lng"])
def time_zone_finder(coordinates: GeoPoint) -> tzinfo | None:
    if coordinates is None:
        return None
    else:
        tzf = TimezoneFinder()
        timezone_name: str = tzf.timezone_at(
            lng=coordinates.longitude, lat=coordinates.latitude
        )
        if timezone_name is None:
            timezone_name = tzf.closest_timezone_at(
                lng=coordinates.longitude, lat=coordinates.latitude
            )
        return timezone(timezone_name)
