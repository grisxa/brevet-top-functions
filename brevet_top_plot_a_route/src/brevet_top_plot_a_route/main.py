import logging
from typing import Optional

from brevet_top_plot_a_route.utils import get_map_id_from_url, download_data

from .exceptions import RouteNotFound
from .route import Route

API_PREFIX: str = "https://www.plotaroute.com/get_route.asp"


def get_route_info(url: str) -> Optional[dict]:
    """
    Download the route details using Plot A Route API. Returns track, short_track, checkpoints, etc.

    :param url: original route link
    :return: a dict with the route details or None
    """
    # allow ids like 12345.6 - the server is rounding to int
    map_id: int = get_map_id_from_url(url)

    route_data: dict = download_data(f"{API_PREFIX}?RouteID={map_id}")
    if "Error" in route_data:
        raise RouteNotFound(route_data["Error"])
    route = Route.from_dict(route_data)
    try:
        route.make_tracks()
    except ValueError as error:
        logging.error(f"Route track error {url} : {error}")
        return None

    try:
        route.checkpoints = route.find_checkpoints()
    except ValueError as error:
        logging.error(f"Route checkpoint error {url} : {error}")

    return {
        "checkpoints": route.checkpoints,
        "name": route.route_name,
        "length": round(route.distance / 1000),  # km
        "mapUrl": url,
        "track": route.track,
        "short_track": route.short_track,
    }
