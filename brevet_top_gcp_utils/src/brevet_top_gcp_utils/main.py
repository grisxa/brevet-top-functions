import logging
import re
from typing import Optional, Tuple

import google.cloud.firestore
import google.cloud.logging
from google.cloud.firestore import DocumentReference, GeoPoint

from brevet_top_plot_a_route import RoutePoint

log_client = google.cloud.logging.Client()
log_client.get_default_handler()
# log_client.setup_logging(log_level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)


def route_point_to_firestore(point: RoutePoint) -> dict:
    """
    Convert a RoutePoint to a storable format.

    :param point: a RoutePoint
    :return: a dict with attributes
    """
    return {"distance": point.distance, "coordinates": GeoPoint(point.lat, point.lng)}


def firestore_to_track_point(data: dict) -> Tuple[float, float, float, float]:
    """
    Convert a stored point dict to a tuple of coordinates and a distance

    :param data: a dict with the point details
    :return: a tuple (latitude, longitude, distance, timestamp=0)
    """
    coordinates: Optional[GeoPoint] = data.get("coordinates")
    if isinstance(coordinates, GeoPoint):
        return (
            coordinates.latitude,
            coordinates.longitude,
            0.0,
            data.get("distance", 0.0),
        )
    return 0.0, 0.0, 0.0, 0.0


def create_document(
    collection_path: str, data: dict, db=google.cloud.firestore.Client()
) -> str:
    """
    Add a document and update uid property.

    :param collection_path: a collection to add the document to
    :param data: the document contents
    :param db: a client to use and share
    :return: id of the new document
    """
    timestamp, doc_ref = db.collection(collection_path).add(data)
    doc_ref.update({"uid": doc_ref.id})
    return doc_ref.id


def resolve_document(
    doc_uid: str, db=google.cloud.firestore.Client()
) -> DocumentReference:
    """
    Resolves an optional numeric alias of an existing document using its brevet_uid reference.
    If a document uid is given then just passes it.
    The alias is another document in the aliases collection with the brevet_uid attribute.

    :param doc_uid: the document uid or a numeric alias
    :param db: a client to use and share
    :return: the document reference
    """
    if re.match("^\\d+$", doc_uid):
        logging.info(f"Looking for alias of {doc_uid}")
        alias_doc = db.document(f"aliases/{doc_uid}")
        alias_dict = alias_doc.get().to_dict()
        if not alias_dict:
            raise ValueError(f"Alias {doc_uid} not found")

        # retrieve reference
        return alias_dict.get("brevet_uid")
    else:
        # retrieve document
        return db.document(f"brevets/{doc_uid}")


def get_checkpoints(brevet_uid: str, db=google.cloud.firestore.Client()) -> list[dict]:
    """
    Retrieves the checkpoint list from the brevet document with sorting by distance and coordinates conversion.

    :param brevet_uid: the brevet UID
    :param db: a client to use and share
    :return: a list of checkpoint dictionaries
    """

    checkpoints: list = [cp.to_dict() for cp in db.document(f"brevets/{brevet_uid}").collection("checkpoints").get()]
    checkpoints.sort(key=lambda x: x.get("distance", 0))
    return [{**cp, "coordinates": firestore_to_track_point(cp)} for cp in checkpoints if cp.get("uid")]
