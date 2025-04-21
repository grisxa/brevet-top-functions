import logging
from datetime import datetime
from typing import List

import firebase_admin
import google.cloud.firestore
import google.cloud.logging
from flask import Request, json
from flask_cors import cross_origin
from google.api_core.datetime_helpers import DatetimeWithNanoseconds

from brevet_top_gcp_utils import resolve_document

log_client = google.cloud.logging.Client()
log_client.get_default_handler()
# log_client.setup_logging(log_level=logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)

firebase_admin.initialize_app()
db_client = google.cloud.firestore.Client()

MANUAL_MICROSECONDS = 123456


@cross_origin(methods="POST")
def save_results(request: Request):
    """
    Save the brevet's results as a checkpoint list and a checkin list.

    :param request: HTTP request
    :return: a link to a JSON report
    """
    logging.debug(f"Request {request}")

    # get a source info
    data: dict = request.get_json().get("data", {})

    doc_uid: str = data.get("brevetUid")
    logging.info(f"Saving results of the brevet {doc_uid}")

    try:
        brevet_doc = resolve_document(doc_uid, db=db_client)
    except ValueError as error:
        return json.dumps({"message": str(error)}), 404

    brevet_dict = brevet_doc.get().to_dict()

    try:
        checkpoints: List[dict] = [
            cp.to_dict() for cp in brevet_doc.collection("checkpoints").get()
        ]
        checkpoints.sort(key=lambda x: x.get("distance", 0))

        if len(checkpoints) > 0:
            brevet_dict["checkpoints"] = []
            brevet_dict["results"] = {}
            for i, cp in enumerate(checkpoints):
                brevet_dict["checkpoints"].append(
                    {
                        "uid": cp["uid"],
                        "name": cp["displayName"],
                        "distance": cp["distance"],
                        "coordinates": cp["coordinates"],
                        "sleep": cp.get("sleep"),
                        # note the camelCase
                        "selfCheck": cp.get("selfcheck"),
                    }
                )
                for checkin_doc in (
                    brevet_doc.collection("checkpoints")
                    .document(cp["uid"])
                    .collection("riders")
                    .get()
                ):
                    checkin = checkin_doc.to_dict()
                    rider_uid = checkin["uid"]
                    if rider_uid not in brevet_dict["results"]:
                        brevet_dict["results"][rider_uid] = {
                            "uid": rider_uid,
                            "code": checkin.get("code"),
                            "name": checkin["name"],
                            "checkins": [None] * len(checkpoints),
                        }
                    if checkin.get("time") is None:
                        logging.error(
                            f"Empty time of rider {rider_uid} {checkin['name']}"
                        )
                    checkin_times: List[datetime] = checkin_reorder(checkin["time"])
                    if len(checkin_times) < 1:
                        continue
                    brevet_dict["results"][rider_uid]["checkins"][i] = checkin_times
                    brevet_dict["results"][rider_uid]["checkins"] : list[list[datetime]|None]
            brevet_doc.set(brevet_dict, merge=True)
    except Exception as error:
        logging.error(f"Saving results error {error}")
        return json.dumps({"message": str(error)}), 500

    return json.dumps({"data": f"/json/brevet/{doc_uid}"}), 200


def is_manual_checkin(checkin: DatetimeWithNanoseconds) -> bool:
    """The time entered manually by a volunteer"""
    return checkin.microsecond == MANUAL_MICROSECONDS


def is_strava_checkin(checkin: DatetimeWithNanoseconds) -> bool:
    """The time imported from Strava"""
    return checkin.microsecond == 0 and checkin.nanosecond == 0


def is_self_checkin(checkin: DatetimeWithNanoseconds) -> bool:
    """The time entered by the rider"""
    return (
        checkin.microsecond != 0 or checkin.nanosecond != 0
    ) and checkin.microsecond != MANUAL_MICROSECONDS


def checkin_reorder(
    checkins: list[DatetimeWithNanoseconds],
) -> list[DatetimeWithNanoseconds]:
    return (
        [t for t in checkins if is_manual_checkin(t)]
        + [t for t in checkins if is_self_checkin(t)]
        + [t for t in checkins if is_strava_checkin(t)]
    )
