import logging
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

    # retrieve document
    brevet_doc = db_client.document(f"brevets/{doc_uid}")
    brevet_dict = brevet_doc.get().to_dict()

    try:
        checkpoints: List[dict] = [
            cp.to_dict()
            for cp in db_client.document(f"brevets/{doc_uid}")
            .collection("checkpoints")
            .get()
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
                    db_client.document(f"brevets/{doc_uid}/checkpoints/{cp['uid']}")
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
