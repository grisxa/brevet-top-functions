import logging
from datetime import timedelta, datetime
from typing import List, Tuple, Final

import numpy as np
import requests

from float_array import FloatArray
from strava.build import get_track_start_point, build_track

AUTH_BASE_URL: str = "https://www.strava.com/oauth"
API_BASE_URL: str = "https://www.strava.com/api/v3"
STREAM_OPTIONS: Final[dict] = {
    "keys": "latlng,time",
    "key_by_type": True,
}


def auth_token(tokens: dict) -> str:
    token_type: str = tokens.get("token_type", "Bearer")
    access_token: str = tokens.get("access_token", "none")
    return f"{token_type} {access_token}" if token_type else "Bearer none"


def tokens_expired(date: datetime, tokens: dict) -> bool:
    return date.timestamp() >= tokens.get("expires_at", 0)


def refresh_tokens(tokens: dict, config: dict) -> dict:
    try:
        data = {
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "grant_type": "refresh_token",
            "refresh_token": tokens["refresh_token"],
        }
        req = requests.post(f"{AUTH_BASE_URL}/token", data)
        req.raise_for_status()
        reply = req.json()
        reply["athlete_id"] = tokens["athlete_id"]
        return reply
    except Exception as error:
        logging.error(f"HTTP error: {error}")
        raise


def time_window(brevet: dict) -> dict:
    """
    Compose HTTP parameters considering start and end time.
    Reserve a 2-hour gap before the start and after the end.

    :param brevet: a dict with the brevet details
    :return: a dict with parameters
    """
    after = brevet.get("startDate")
    before = brevet.get("endDate")
    params = {}
    if after is not None:
        params["after"] = (after - timedelta(hours=2)).timestamp()
    if before is not None:
        params["before"] = (before + timedelta(hours=2)).timestamp()
    # logging.info(f"activity time window {params}")
    return params


def download_data(url: str, headers: dict, params: dict = None):
    """
    Generic data downloader

    :param url: a link to request
    :param headers: additional HTTP headers
    :param params: additional request parameters
    :return: JSON response
    """
    try:
        req = requests.get(url, headers=headers, params=params)
        req.raise_for_status()
        return req.json()
    except Exception as error:
        logging.error(f"HTTP error: {error}")
        raise


def get_activities(brevet: dict, token: str) -> List[dict]:
    headers = {"Authorization": token}

    activities: List[dict] = download_data(
        f"{API_BASE_URL}/athlete/activities", headers, params=time_window(brevet)
    )

    # Take bike rides only
    return list(filter(lambda a: a["type"] == "Ride", activities))


def get_activity(activity_id: int, token: str) -> dict:
    headers = {"Authorization": token}

    activity: dict = download_data(f"{API_BASE_URL}/activities/{activity_id}", headers)
    return activity


def get_track_points(activities: List[dict], token: str) -> FloatArray:
    """
    Download Strava streams for the given activities and transform to a track point list.

    :param activities: a list of Strava activities
    :param token: Authorization header value
    :return: a list of points as tuples (latitude, longitude, timestamp, distance)
    """
    headers = {"Authorization": token}
    draft: FloatArray = np.empty(shape=(0, 4), dtype=np.float64)
    distance = 0

    # order activities by the start date
    for activity in activities:
        logging.debug(
            f"activity {activity.get('name')}/{activity.get('id')} {activity.get('start_date')}"
        )
        activity_id = activity.get("id")
        first_point: Tuple[float, float, float, float] = get_track_start_point(activity)

        stream: dict = download_data(
            f"{API_BASE_URL}/activities/{activity_id}/streams",
            headers,
            params=STREAM_OPTIONS,
        )
        draft = np.concatenate(
            (
                draft,
                build_track(
                    start_timestamp=first_point[2],
                    start_distance=distance,
                    stream=stream,
                ),
            )
        )
        distance = draft[-1][3]

    return draft