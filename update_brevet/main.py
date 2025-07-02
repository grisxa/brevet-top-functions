import logging
import os
from datetime import datetime, timedelta
from typing import List

import dateutil.parser
import firebase_admin
import google.cloud.firestore
import google.cloud.logging
from google.cloud.functions.context import Context

from brevet_top_gcp_utils import route_point_to_firestore
from brevet_top_plot_a_route import ROUTE_PREFIX, get_route_info

from brevet_top_misc_utils import get_limit_hours, get_control_window

log_client = google.cloud.logging.Client()
log_client.get_default_handler()
log_client.setup_logging(log_level=os.getenv("LOG_LEVEL", "WARNING"))
logging.basicConfig(level=os.getenv("LOG_LEVEL", "WARNING"))

firebase_admin.initialize_app()
db_client = google.cloud.firestore.Client()

EARLY_START = 32  # hours before

def update_brevet(data, context: Context):
    """
    React to a brevet attributes change: start date, length.
    Should be attached to a data change trigger.

    :param data: the change dict
    :param context: a calling context including the document path
    """
    logging.debug(f"Data {data}")
    logging.debug(f"Context {context}")
    doc_path: str = context.resource.split("/documents/")[-1]
    updates: List[str] = data.get("updateMask", {}).get("fieldPaths", [])
    if "startDate" in updates or "length" in updates:
        update_time(doc_path, data)
    elif "mapUrl" in updates:
        update_route(doc_path, data)
    else:
        logging.warning("No supported attribute changes")


def update_time(doc_path: str, data: dict):
    start_date: datetime = dateutil.parser.isoparse(
        data.get("value").get("fields").get("startDate", {}).get("timestampValue", "")
    )
    length: int = int(
        data.get("value").get("fields").get("length", {}).get("integerValue", "0")
    )

    logging.info(f"Brevet change of {doc_path} to {start_date} / {length} km")

    if length and start_date:
        change = {
            "endDate": start_date + timedelta(hours=get_limit_hours(length)),
            "openDate": start_date - timedelta(hours=EARLY_START),
        }
        save_doc(doc_path, change)

    if start_date:
        for cp in db_client.document(doc_path).collection("checkpoints").get():
            checkpoint = cp.to_dict()
            start, end = get_control_window(checkpoint.get("distance", 0))
            save_doc(
                f"{doc_path}/checkpoints/{checkpoint['uid']}",
                {
                    "startDate": start_date + timedelta(hours=start),
                    "endDate": start_date + timedelta(hours=end),
                },
            )


def save_doc(path: str, data: dict):
    """
    Update the document with new details.

    :param path: original document path
    :param data: a dict with the document change
    """
    doc = db_client.document(path)
    doc.set(data, merge=True)


def update_route(doc_path: str, data: dict):
    """
    React to a route URI change, download the route details and update the source document.
    Should be attached to a data change trigger.

    :param data: the change dict
    :param context: a calling context including the document path
    """

    map_url: str = (
        data.get("value").get("fields").get("mapUrl", {}).get("stringValue", "")
    )

    logging.info(f"Route change of {doc_path} to {map_url}")

    if not map_url.startswith(ROUTE_PREFIX):
        logging.error(f"Unsupported route {map_url}")
        return

    route_info = get_route_info(map_url)
    route_info["track"] = [
        route_point_to_firestore(point) for point in route_info["track"]
    ]
    route_info["short_track"] = [
        route_point_to_firestore(point) for point in route_info["short_track"]
    ]
    route_info.pop("checkpoints")

    save_doc(doc_path, route_info)
