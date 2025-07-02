import logging
from datetime import timedelta
from typing import List

import firebase_admin
import google.cloud.firestore
import google.cloud.logging
from brevet_top_misc_utils import get_control_window
from flask import Request, json
from flask_cors import cross_origin

from brevet_top_gcp_utils import route_point_to_firestore
from brevet_top_gcp_utils.auth_decorator import authenticated
from brevet_top_plot_a_route import CheckPoint, get_route_info

log_client = google.cloud.logging.Client()
log_client.get_default_handler()
log_client.setup_logging(log_level=logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)

firebase_admin.initialize_app()
db_client = google.cloud.firestore.Client()


@cross_origin(methods="POST")
@authenticated
def create_checkpoints(request: Request, auth: dict):
    """
    Create checkpoints in a nested collection and in the brevet document.

    :param request: HTTP request
    :param auth: Authentication tokens
    :return:
    """
    logging.debug(f"Request {request}")

    # get a source info
    data: dict = request.get_json().get("data", {})

    rider_dict = db_client.document(f"private/{auth['uid']}").get().to_dict()
    if not rider_dict["admin"]:
        return (
            json.dumps({"data": {"message": "Forbidden operation", "error": 403}}),
            403,
        )

    doc_uid: str = data["brevetUid"]
    logging.info(f"Create checkpoints for brevet {doc_uid}")

    # retrieve document
    doc = db_client.document(f"brevets/{doc_uid}")
    brevet_dict = doc.get().to_dict()

    try:
        info: dict = get_route_info(brevet_dict["mapUrl"])
        checkpoints: List[CheckPoint] = info.pop("checkpoints")
        checkpoint_list = []

        for cp in checkpoints:
            start, end = get_control_window(cp.distance)
            control_data: dict = route_point_to_firestore(cp)
            control_data["displayName"] = cp.name
            control_data["startDate"] = brevet_dict["startDate"] + timedelta(hours=start)
            control_data["endDate"] = brevet_dict["startDate"] + timedelta(hours=end)
            control_data["brevet"] = {
                "uid": doc_uid,
                "name": brevet_dict["name"],
                "length": brevet_dict["length"],
            }
            (timestamp, ref) = doc.collection("checkpoints").add(control_data)
            logging.debug(f"New checkpoint {ref.id} / {cp.name} {cp.distance} km")
            doc.collection("checkpoints").document(ref.id).set(
                {
                    "uid": ref.id,
                },
                merge=True,
            )
            checkpoint_list.append({
                "uid": ref.id,
                "name": cp.name,
                "distance": cp.distance,
                "coordinates": control_data["coordinates"],
            })
        doc.set(
            {
                "checkpoints": checkpoint_list
            },
            merge=True,
        )

    except Exception as error:
        return json.dumps({"message": str(error)}), 500

    return json.dumps({"data": {"result": "OK"}}), 200
