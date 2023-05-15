import logging
import re
from datetime import datetime
from typing import List

import firebase_admin
import google.cloud.firestore
import google.cloud.logging
from flask import Request, json
from flask_cors import cross_origin

log_client = google.cloud.logging.Client()
log_client.get_default_handler()
# log_client.setup_logging(log_level=logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)

firebase_admin.initialize_app()
db_client = google.cloud.firestore.Client()


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
        brevet_doc = resolve_document(doc_uid)
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
                for doc in (
                    brevet_doc.collection("checkpoints")
                    .document(cp["uid"])
                    .collection("riders")
                    .get()
                ):
                    checkin = doc.to_dict()
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
                    times: List[datetime] = [
                        t for t in checkin["time"] if t.microsecond
                    ] + [t for t in checkin["time"] if not t.microsecond]
                    if len(times) < 1:
                        continue
                    brevet_dict["results"][rider_uid]["checkins"][i] = times[0]
            brevet_doc.set(brevet_dict, merge=True)
    except Exception as error:
        logging.error(f"Saving results error {error}")
        return json.dumps({"message": str(error)}), 500

    return json.dumps({"data": f"/json/brevet/{doc_uid}"}), 200


def resolve_document(doc_uid: str):
    if re.match("^\\d+$", doc_uid):
        logging.info(f"Looking for alias of {doc_uid}")
        alias_doc = db_client.document(f"aliases/{doc_uid}")
        alias_dict = alias_doc.get().to_dict()
        if not alias_dict:
            raise ValueError(f"Alias {doc_uid} not found")

        # retrieve reference
        return alias_dict.get("brevet_uid")
    else:
        # retrieve document
        return db_client.document(f"brevets/{doc_uid}")
