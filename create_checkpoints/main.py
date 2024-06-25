import logging
from datetime import timedelta
from typing import List

import firebase_admin
import google.cloud.firestore
import google.cloud.logging
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
    Create checkpoints in a nested collection.

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

        for cp in checkpoints:
            start, end = get_control_window(cp.distance)
            control_data: dict = route_point_to_firestore(cp)
            control_data["displayName"] = cp.name
            control_data["startDate"] = (
                brevet_dict["startDate"] + timedelta(hours=start),
            )
            control_data["endDate"] = (brevet_dict["startDate"] + timedelta(hours=end),)
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

    except Exception as error:
        return json.dumps({"message": str(error)}), 500

    return json.dumps({"data": {"result": "OK"}}), 200


def get_control_window(distance: float) -> tuple[float, float]:
    """
    Calculate the time window on the control point based on the average speed and distance.
    """
    if distance == 0:
        return 0.0, 1.0
    elif distance <= 60:
        return distance / 34 + 0.008333333333334, distance / 20 + 1.008333333333334
    elif 60 < distance <= 200:
        return (
            distance / 34 + 0.008333333333334,
            (distance - 60) / 15 + 4.008333333333334,
        )
    elif 200 < distance <= 400:
        return (distance - 200) / 32 + 5.890686274509805, (
            distance - 60
        ) / 15 + 4.008333333333334
    elif 400 < distance <= 600:
        return (distance - 400) / 30 + 12.140333333333333, (
            distance - 60
        ) / 15 + 4.008333333333334
    elif 600 < distance <= 1000:
        return (distance - 600) / 28 + 18.807, (
            distance - 600
        ) / 11.428571428571429 + 40.008333333333334
    elif 1000 < distance <= 1200:
        return (distance - 1000) / 26 + 33.09304761904762, (
            distance - 1000
        ) / 13.333333333333333 + 75.008333333333334
    elif 1200 < distance <= 1400:
        return (distance - 1200) / 25 + 40.78564102564103, (
            distance - 1200
        ) / 11 + 90.008333333333334
    elif 1400 < distance <= 1800:
        return (distance - 1200) / 25 + 40.78564102564103, (
            distance - 1400
        ) / 10 + 108.19015151515153
    elif 1800 < distance <= 2000:
        return (distance - 1800) / 24 + 64.78533333333334, (
            distance - 1800
        ) / 9 + 148.19033333333334
