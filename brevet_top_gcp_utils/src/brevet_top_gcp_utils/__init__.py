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

