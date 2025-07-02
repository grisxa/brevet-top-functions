import logging
from datetime import timedelta

import dateutil.parser
import firebase_admin
import google.cloud.firestore
import google.cloud.logging
from brevet_top_misc_utils import get_limit_hours
from flask import Request, json
from flask_cors import cross_origin
from google.cloud.firestore_v1 import GeoPoint

from brevet_top_gcp_utils import route_point_to_firestore
from brevet_top_plot_a_route import ROUTE_PREFIX, get_route_info

log_client = google.cloud.logging.Client()
log_client.get_default_handler()
# log_client.setup_logging(log_level=logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)

firebase_admin.initialize_app()
db_client = google.cloud.firestore.Client()

EARLY_START = 32  # hours before


@cross_origin(methods="POST")
def import_brevet(request: Request):
    """
    Imports a brevet and its checkpoints from a JSON request.
    """
    logging.debug(f"Request {request}")

    # get a source info
    data: dict = request.get_json().get("data", {})

    try:
        start_date = dateutil.parser.isoparse(data.get("startDate"))
        end_date = data.get("endDate")
        open_date = data.get("openDate")
        map_url = data.get("mapUrl")
        length = int(data.get("length") or 0)
        brevet_data = dict(
            length=length,
            name=data.get("name"),
            mapUrl=map_url,
            startDate=start_date,
            endDate=dateutil.parser.isoparse(end_date) if end_date else start_date + timedelta(hours=get_limit_hours(length)),
            openDate=dateutil.parser.isoparse(open_date) if open_date else start_date - timedelta(hours=EARLY_START),
            skip_trim=data.get("skip_trim", False),
        )
        (timestamp, doc) = db_client.collection("brevets").add(brevet_data)
        db_client.collection("brevets").document(doc.id).set(
            {
                "uid": doc.id,
            },
            merge=True,
        )

        brevet_checkpoints = []
        for cp in data.get("checkpoints"):
            point = cp.get("coordinates", {})
            control_data = {
                "displayName": cp.get("name"),
                # TODO: fix the camel case
                "selfcheck": cp.get("selfCheck"),
                "selfCheck": cp.get("selfCheck"),
                "sleep": cp.get("sleep"),
                "distance": cp.get("distance"),
                "coordinates": GeoPoint(latitude=point.get("lat"), longitude=point.get("lng")),
                "brevet": {
                    "uid": doc.id,
                    "name": brevet_data["name"],
                    "length": brevet_data["length"],
                },
            }

            (timestamp, ref) = doc.collection("checkpoints").add(control_data)
            logging.debug(f"New checkpoint {ref.id} / {control_data['displayName']} {control_data['distance']} km")
            doc.collection("checkpoints").document(ref.id).set(
                {
                    "uid": ref.id,
                },
                merge=True,
            )

            brevet_checkpoints.append(
                dict(
                    name=control_data["displayName"],
                    sleep=control_data["sleep"],
                    distance=control_data["distance"],
                    coordinates=control_data["coordinates"],
                    selfCheck=control_data["selfCheck"],
                    uid=ref.id,
                )
            )

        db_client.collection("brevets").document(doc.id).set(
            {
                "checkpoints": brevet_checkpoints,
            },
            merge=True,
        )

        if not map_url.startswith(ROUTE_PREFIX):
            logging.warning(f"Unsupported route {map_url}")
            return

        route_info = get_route_info(map_url)

        db_client.collection("brevets").document(doc.id).set(
            {
                "track": [route_point_to_firestore(point) for point in route_info["track"]],
                "short_track": [route_point_to_firestore(point) for point in route_info["short_track"]],
            },
            merge=True,
        )

    except Exception as error:
        return json.dumps({"message": str(error)}), 500

    return json.dumps({"data": {"result": doc.id}}), 200
