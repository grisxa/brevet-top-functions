import logging

import firebase_admin
import google.cloud.logging
from flask import Request, json
from flask_cors import cross_origin
from google.cloud.firestore import Query

from brevet_top_gcp_utils.auth_decorator import authenticated

log_client = google.cloud.logging.Client()
log_client.get_default_handler()
log_client.setup_logging(log_level=logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)

firebase_admin.initialize_app()
db_client = google.cloud.firestore.Client()


@cross_origin(methods="POST")
@authenticated
def save_brevet_list(request: Request, auth: dict):
    """
    Create/update the brevet list (index)

    :param request: HTTP request
    :param auth: Authentication tokens
    :return:
    """
    logging.debug(f"Request {request}")

    rider_dict = db_client.document(f"private/{auth['uid']}").get().to_dict()
    if not rider_dict["admin"]:
        return (
            json.dumps({"data": {"message": "Forbidden operation", "error": 403}}),
            403,
        )

    try:
        brevet_list = []
        for doc in db_client.collection("brevets").order_by("startDate", direction=Query.DESCENDING).stream():
            brevet_dict = db_client.document(f"brevets/{doc.id}").get().to_dict()
            brevet_list.append({
                key: brevet_dict.get(key)
                for key in [
                    "uid",
                    "name",
                    "length",
                    "startDate",
                    "mapUrl",
                    "endDate",
                ]
            })
        # retrieve document
        list_doc = db_client.document("brevets/list")
        list_dict = list_doc.get().to_dict()

        # update the list
        list_dict["brevets"] = brevet_list
        db_client.collection("brevets").document("list").set(list_dict, merge=True)
    except Exception as error:
        return json.dumps({"message": str(error)}), 500

    return json.dumps({"message": "Saved"}), 200
