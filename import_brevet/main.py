import logging

import dateutil.parser
import firebase_admin
import google.cloud.firestore
import google.cloud.logging
from flask import Request, json
from flask_cors import cross_origin
from google.cloud.firestore_v1 import GeoPoint

log_client = google.cloud.logging.Client()
log_client.get_default_handler()
# log_client.setup_logging(log_level=logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)

firebase_admin.initialize_app()
db_client = google.cloud.firestore.Client()


@cross_origin(methods="POST")
def import_brevet(request: Request):
    """
    Imports a brevet and its checkpoints from a JSON request.
    """
    logging.debug(f"Request {request}")

    # get a source info
    data: dict = request.get_json().get("data", {})

    try:
        brevet_data = dict(
            length=data.get("length"),
            name=data.get("name"),
        )
        (timestamp, doc) = db_client.collection("brevets").add(brevet_data)
        db_client.collection("brevets").document(doc.id).set(
            {
                "uid": doc.id,
            },
            merge=True,
        )

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
                }
            }

            (timestamp, ref) = doc.collection("checkpoints").add(control_data)
            logging.debug(f"New checkpoint {ref.id} / {control_data['displayName']} {control_data['distance']} km")
            doc.collection("checkpoints").document(ref.id).set(
                {
                    "uid": ref.id,
                },
                merge=True,
            )
        db_client.collection("brevets").document(doc.id).set(
            {
                "startDate": dateutil.parser.isoparse(data.get("startDate")),
            },
            merge=True,
        )
        db_client.collection("brevets").document(doc.id).set(
            {
                "mapUrl": data.get("mapUrl"),
            },
            merge=True,
        )

    except Exception as error:
        return json.dumps({"message": str(error)}), 500

    return json.dumps({"data": {"result": doc.id}}), 200
