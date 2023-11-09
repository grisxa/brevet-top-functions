from typing import Tuple, Optional

import google.cloud.firestore
from google.cloud.firestore_v1 import GeoPoint

from brevet_top_plot_a_route import RoutePoint


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

    :param db: a client to use and share
    :param collection_path: a collection to add the document to
    :param data: the document contents
    :return: id of the new document
    """
    timestamp, doc_ref = db.collection(collection_path).add(data)
    doc_ref.update({"uid": doc_ref.id})
    return doc_ref.id
