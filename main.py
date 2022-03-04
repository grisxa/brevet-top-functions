import logging
import os
import re
from base64 import b64decode
from datetime import datetime, timedelta, tzinfo
from typing import List, Optional

import dateutil.parser
import firebase_admin
import google.cloud.firestore
import google.cloud.logging
import google.cloud.pubsub
from flask import Request, json
from flask_cors import cross_origin
from google.cloud.functions.context import Context
from pytz import timezone, utc
from requests import HTTPError
from timezonefinder import TimezoneFinder

from gcp_utils import (
    route_point_to_firestore,
    firestore_to_track_point,
    create_document,
)
from gcp_utils.auth_decorator import authenticated
from plot_a_route import ROUTE_PREFIX, get_route_info, CheckPoint
from strava import (
    search_strava_activities,
    ActivityNotFound,
    ActivityError,
    auth_token,
    track_alignment,
)
from strava.api import get_activity, refresh_tokens, tokens_expired
from strava.build import build_checkpoint_list
from strava.exceptions import AthleteNotFound

log_client = google.cloud.logging.Client()
log_client.get_default_handler()
log_client.setup_logging(log_level=logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)

firebase_admin.initialize_app()
db_client = google.cloud.firestore.Client()
pub_client = google.cloud.pubsub.PublisherClient()

# logging.basicConfig(filename='run.log', filemode='w', level=logging.DEBUG)


def update_brevet_route(data, context: Context):
    """
    React to a route URI change, download the route details and update the source document.
    Should be attached to a data change trigger.

    :param data: the change dict
    :param context: a calling context including the document path
    """
    logging.debug(f"Data {data}")
    logging.debug(f"Context {context}")

    updates: List[str] = data.get("updateMask", {}).get("fieldPaths", [])
    # not a route update
    if "mapUrl" not in updates:
        return

    map_url: str = (
        data.get("value").get("fields").get("mapUrl", {}).get("stringValue", "")
    )
    doc_path: str = context.resource.split("/documents/")[-1]
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

    if route_info:
        save_route(doc_path, route_info)


def save_route(path: str, data: dict):
    """
    Update a document with new route details.

    :param path: original document path
    :param data: a dict with route info
    """
    doc = db_client.document(path)
    doc.set(data, merge=True)


def strava_watcher(event, context):
    # logging.debug(f"Event {event}")
    # logging.debug(f"Context {context}")

    try:
        # project_id = os.getenv('GCLOUD_PROJECT')

        # Secret Manager exposed to the environment
        secret = json.loads(os.getenv("STRAVA"))

        data = (
            json.loads(b64decode(event["data"]).decode("utf-8"))
            if "@type" in event
            else event
        )
        logging.debug(f"Data {data}")

        if data["subscription_id"] != int(secret["subscription_id"]):
            logging.error("Invalid subscription id")
            raise HTTPError("Invalid parameters")

        if (
            data["object_type"] == "athlete"
            and data["aspect_type"] == "update"
            and data["updates"]["authorized"] == "false"
        ):
            strava_revoke(int(data["object_id"]))

        if data["object_type"] == "activity":
            logging.debug(
                f"Athlete {data['owner_id']} "
                f"activity {data['object_id']} {data['aspect_type']}"
            )
            strava_compare(int(data["owner_id"]), int(data["object_id"]), secret)

        return json.dumps({"data": "OK"}), 200

    except Exception as error:
        logging.error(str(error))
        return json.dumps({"message": str(error)}), 400


def strava_revoke(athlete_id: int):
    """
    Delete Strava tokens by the athlete's request

    :param athlete_id: id to search
    """
    logging.debug(f"Athlete {athlete_id} de-authorization")
    docs = (
        db_client.collection("private")
        .where("strava.athlete_id", "==", athlete_id)
        .stream()
    )
    for doc in docs:
        db_client.document(f"private/{doc.id}").set(
            {"strava": None, "stravaRevoke": True}, merge=True
        )


def search_strava_riders(athlete_id: int) -> List[dict]:
    return [
        db_client.document(f"private/{doc.id}").get().to_dict()
        for doc in db_client.collection("private")
        .where("strava.athlete_id", "==", int(athlete_id))
        .stream()
    ]


def search_brevets(start_date: datetime) -> List[dict]:
    logging.debug(
        f"Lookup brevets in {start_date - timedelta(hours=12)} / {start_date + timedelta(hours=12)}"
    )
    return [
        db_client.document(f"brevets/{doc.id}").get().to_dict()
        for doc in db_client.collection("brevets")
        # lookup +/- 12 hours from the activity start date
        .where("startDate", ">", start_date - timedelta(hours=12))
        .where("startDate", "<", start_date + timedelta(hours=12))
        .stream()
    ]


def strava_compare(athlete_id: int, activity_id: int, secret: dict):
    riders = search_strava_riders(athlete_id)

    if len(riders) < 1:
        raise AthleteNotFound(f"Can't find athlete {athlete_id}")

    activity: Optional[dict] = None

    for rider_dict in riders:
        logging.debug(f"Rider {rider_dict['uid']}")

        tokens = rider_dict["strava"]
        if tokens_expired(datetime.now(), tokens):
            tokens = refresh_tokens(tokens, secret)
            db_client.document(f"private/{rider_dict['uid']}").set(
                {"strava": tokens}, merge=True
            )

        activity = activity or get_activity(activity_id, auth_token(tokens))

    if not activity:
        raise ActivityNotFound(f"Can't download activity {activity_id}")

    if activity["type"] != "Ride":
        raise ActivityNotFound(f"Not a ride {activity_id}")

    start_date: datetime = dateutil.parser.isoparse(activity.get("start_date", ""))
    logging.debug(f"Search for start date {start_date}")

    brevets = search_brevets(start_date)
    if len(brevets) < 1:
        raise Exception(f"Brevet on {start_date} not found")

    for brevet_dict in brevets:
        logging.debug(f"Brevet {brevet_dict['uid']}")

        # convert stored GeoPoints
        brevet_dict["short_track"] = [
            firestore_to_track_point(p) for p in brevet_dict.get("short_track", [])
        ]

        # prepare a list of control points (check-in / check-out) necessary to visit
        checkpoints, ids = build_checkpoint_list(get_checkpoints(brevet_dict["uid"]))
        # logging.debug(f"Checkpoints {checkpoints} / {ids}")

        # start searching
        points = track_alignment(
            brevet_dict, riders[0]["strava"], [activity], checkpoints
        )

        # register check-ins / check-outs
        for i, cp in enumerate(points):
            # test for NaN
            if cp[2] == cp[2]:
                for rider_dict in riders:
                    logging.debug(
                        f"Check-in {brevet_dict['name']}/{ids[i]} "
                        f"{rider_dict['providers'][0]['displayName']}/{rider_dict['uid']} "
                        f"{datetime.fromtimestamp(cp[2], tz=utc)}"
                    )
                    create_rider_barcode(
                        rider_dict["uid"],
                        code=ids[i],
                        time=datetime.fromtimestamp(cp[2], tz=utc),
                    )


def create_rider_barcode(rider_uid: str, code: str, time: datetime) -> str:
    return create_document(
        f"riders/{rider_uid}/barcodes",
        {
            "code": code,
            "control": rider_uid,
            "owner": rider_uid,
            "time": time,
            "message": "new",
        },
        db=db_client,
    )


@cross_origin(methods="POST")
def check_in(request: Request):
    """
    Register a rider at the control point.

    :param request:
    :return:
    """
    logging.debug(f"Request {request}")
    try:
        # get a source info
        data: dict = request.get_json().get("data", {})
        rider_uid: str = data["riderUid"]
        control_uid: str = data["controlUid"]
        time: datetime = (
            datetime.fromtimestamp(float(data["time"]), tz=utc)
            if data["time"] is not None
            else datetime.now()
        )

        doc_uid = create_rider_barcode(rider_uid, code=control_uid, time=time)
    except Exception as error:
        return json.dumps({"message": str(error)}), 500

    return json.dumps({"data": doc_uid}), 200


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
            control_data: dict = route_point_to_firestore(cp)
            control_data["displayName"] = cp.name
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


@cross_origin(methods="POST")
@authenticated
def search_activities(request: Request, auth: dict):
    """
    Find suitable Strava activities given a brevet and a user.

    :param request: HTTP request
    :param auth: exposed authorization header
    :return: HTTP response
    """
    logging.debug(f"Request {request}")
    logging.debug(f"Auth {auth}")

    # get a source info
    data: dict = request.get_json().get("data", {})
    logging.info(
        f"Search activities for brevet {data['brevetUid']} user {data['riderUid']}"
    )

    if data["riderUid"] != auth["uid"]:
        return (
            json.dumps(
                {
                    "data": {
                        "message": f"Forbidden access to {data['riderUid']}",
                        "error": 403,
                    }
                }
            ),
            403,
        )

    # retrieve documents
    brevet_dict = db_client.document(f"brevets/{data['brevetUid']}").get().to_dict()
    rider_dict = db_client.document(f"private/{data['riderUid']}").get().to_dict()

    tokens = data.get("tokens") or rider_dict["strava"]

    # convert stored GeoPoints
    brevet_dict["short_track"] = [
        firestore_to_track_point(p) for p in brevet_dict.get("short_track", [])
    ]

    try:
        # prepare a list of control points (check-in / check-out) necessary to visit
        checkpoints, ids = build_checkpoint_list(get_checkpoints(data["brevetUid"]))

        logging.debug(f"Checkpoints {checkpoints} / {ids}")

        # start searching
        points = search_strava_activities(brevet_dict, tokens, checkpoints)

        # register check-ins / check-outs
        for i, cp in enumerate(points):
            # test for NaN
            if cp[2] == cp[2]:
                create_rider_barcode(
                    data["riderUid"],
                    code=ids[i],
                    time=datetime.fromtimestamp(cp[2], tz=utc),
                )
    except HTTPError as error:
        return (
            json.dumps({"data": {"message": error.response.reason}}),
            error.response.status_code,
        )

    except ActivityNotFound as error:
        return json.dumps({"data": {"message": str(error), "error": 404}}), 200

    except ActivityError as error:
        return json.dumps({"data": {"message": str(error), "error": 404}}), 200

    except Exception as error:
        return json.dumps({"data": {"message": str(error), "error": 500}}), 500

    return json.dumps({"data": {"message": len(points)}}), 200


def get_checkpoints(brevet_uid: str) -> List[dict]:
    checkpoints: list = [
        cp.to_dict()
        for cp in db_client.document(f"brevets/{brevet_uid}")
        .collection("checkpoints")
        .get()
    ]
    checkpoints.sort(key=lambda x: x.get("distance", 0))
    return [
        {**cp, "coordinates": firestore_to_track_point(cp)}
        for cp in checkpoints
        if cp.get("uid")
    ]


@cross_origin(methods="POST")
@authenticated
def save_results(request: Request, auth: dict):
    """
    Save the brevet's results as a checkpoint list and a checkin list.

    :param request: HTTP request
    :param auth: Authentication tokens
    :return: a link to a JSON report
    """
    logging.debug(f"Request {request}")

    # get a source info
    data: dict = request.get_json().get("data", {})

    # TODO : extract to a decorator
    rider_dict = db_client.document(f"private/{auth['uid']}").get().to_dict()
    if not rider_dict["admin"]:
        return (
            json.dumps({"data": {"message": "Forbidden operation", "error": 403}}),
            403,
        )

    doc_uid: str = data["brevetUid"]
    logging.info(f"Saving results of the brevet {doc_uid}")

    # retrieve document
    brevet_doc = db_client.document(f"brevets/{doc_uid}")
    brevet_dict = brevet_doc.get().to_dict()

    try:
        checkpoints: List[dict] = [
            cp.to_dict()
            for cp in db_client.document(f"brevets/{doc_uid}")
            .collection("checkpoints")
            .get()
        ]
        checkpoints.sort(key=lambda x: x.get("distance", 0))

        if len(checkpoints) > 0:
            brevet_dict["checkpoints"] = []
            brevet_dict["results"] = {}
            for i, cp in enumerate(checkpoints):
                brevet_dict["checkpoints"].append(
                    {
                        "uid": cp["uid"],
                        "name": cp["displayName"],
                        "distance": cp["distance"],
                        "coordinates": cp["coordinates"],
                    }
                )
                for doc in (
                    db_client.document(f"brevets/{doc_uid}/checkpoints/{cp['uid']}")
                    .collection("riders")
                    .get()
                ):
                    checkin = doc.to_dict()
                    rider_uid = checkin["uid"]
                    if rider_uid not in brevet_dict["results"]:
                        brevet_dict["results"][rider_uid] = {
                            "uid": rider_uid,
                            "code": checkin.get("code"),
                            "name": checkin["name"],
                            "checkins": [None] * len(checkpoints),
                        }
                    brevet_dict["results"][rider_uid]["checkins"][i] = checkin["time"][
                        0
                    ]
            brevet_doc.set(brevet_dict, merge=True)
    except Exception as error:
        return json.dumps({"message": str(error)}), 500

    return json.dumps({"data": f"/json/brevet/{doc_uid}"}), 200


@cross_origin(methods="GET")
def json_export(request: Request):
    """
    Export the brevet's results to JSON.
    Takes a field selection including the brevet description and rider checkins.

    :param request: HTTP request
    :return: JSON with results
    """
    logging.debug(f"Request {request}")

    doc_uid: str = request.path.split("/brevet/")[-1]
    if not doc_uid or re.match("\\W", doc_uid):
        logging.error(f"Wrong document ID {doc_uid}")
        return json.dumps({"message": f"Wrong document ID {doc_uid}"}), 400

    logging.info(f"Exporting results of the brevet {doc_uid}")

    try:
        # retrieve document
        brevet_doc = db_client.document(f"brevets/{doc_uid}")
        brevet_dict = brevet_doc.get().to_dict()

        payload = {
            key: brevet_dict.get(key)
            for key in [
                "uid",
                "name",
                "length",
                "startDate",
                "mapUrl",
                "checkpoints",
                "results",
            ]
        }
    except Exception as error:
        return json.dumps({"message": str(error)}), 500

    tzf = TimezoneFinder()
    time_zones = []
    for cp in payload["checkpoints"]:
        coordinates = cp.pop('coordinates')
        if coordinates is None:
            time_zones.append(None)
        else:
            timezone_name: str = tzf.timezone_at(lng=coordinates.longitude, lat=coordinates.latitude)
            if timezone_name is None:
                timezone_name = tzf.closest_timezone_at(lng=coordinates.longitude, lat=coordinates.latitude)
            time_zones.append(timezone(timezone_name))

    for r in payload["results"]:
        dates = payload["results"][r]["checkins"]

        for i, d in enumerate(dates):
            # TODO: extract conversion
            if d is not None and time_zones[i] is not None:
                dates[i] = d.astimezone(time_zones[i])
    if payload["startDate"] is not None and time_zones[0] is not None:
        payload["startDate"] = payload["startDate"].astimezone(time_zones[0])

    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            default=lambda x: x.isoformat() if type(x) == datetime else str(x),
        ),
        200,
        {"Content-Type": "application/json"},
    )


if __name__ == "__main__":
    pass
