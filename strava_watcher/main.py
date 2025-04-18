import logging
import os
from base64 import b64decode
from datetime import datetime, timedelta
from typing import List, Optional

import dateutil.parser
import firebase_admin
import google.cloud.firestore
import google.cloud.logging
from flask import json
from google.cloud import functions_v1
from google.cloud.functions.context import Context
from pytz import utc
from requests import HTTPError

from brevet_top_gcp_utils import create_document, firestore_to_track_point, get_checkpoints
from brevet_top_numpy_utils import FloatArray
from brevet_top_strava import (ActivityError, ActivityNotFound, AthleteNotFound, auth_token, build_checkpoint_list,
                               get_activity, get_track_points, refresh_tokens, tokens_expired, track_alignment)

log_client = google.cloud.logging.Client()
log_client.get_default_handler()
log_client.setup_logging(log_level=os.getenv("LOG_LEVEL", "INFO"))
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

firebase_admin.initialize_app()
db_client = google.cloud.firestore.Client()


def strava_watcher(event, context: Context):
    try:
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

        # detect athlete unsubscription
        if (
            data["object_type"] == "athlete"
            and data["aspect_type"] == "update"
            and data["updates"]["authorized"] == "false"
        ):
            strava_revoke(int(data["object_id"]))

        # detect activity update
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


def strava_compare(athlete_id: int, activity_id: int, secret: dict):
    """
    Compare the Strava activity and a brevet route
    :param athlete_id: The athlete id to search for
    :param activity_id: The activity to test
    :param secret: Secret Manager exposed to the environment
    """
    # may be several accounts linked to the same Strava athlete
    riders = search_strava_riders(athlete_id)

    if len(riders) < 1:
        raise AthleteNotFound(f"Can't find athlete {athlete_id}")

    activity: Optional[dict] = None

    for rider_dict in riders:
        logging.info(f"Rider {rider_dict['uid']}")

        # use the athlete's tokens
        tokens = rider_dict["strava"]
        if tokens_expired(datetime.now(), tokens):
            logging.debug("Strava token has expired, refreshing")
            rider_dict["strava"] = tokens = refresh_tokens(tokens, secret)
            db_client.document(f"private/{rider_dict['uid']}").set(
                {"strava": tokens}, merge=True
            )

        activity = activity or get_activity(activity_id, auth_token(tokens))

    if not activity:
        raise ActivityNotFound(f"Can't download activity {activity_id}")

    # only Ride activities are being supported
    if activity["type"] != "Ride":
        raise ActivityNotFound(f"Not a ride {activity_id}")

    start_date: datetime = dateutil.parser.isoparse(activity.get("start_date", ""))
    logging.debug(f"Search for start date {start_date}")

    brevets = search_brevets(start_date)
    if len(brevets) < 1:
        raise Exception(f"Brevet on {start_date} not found")

    client = functions_v1.CloudFunctionsServiceClient()
    for brevet_dict in brevets:
        logging.info(f"Brevet {brevet_dict['uid']}")

        # convert stored GeoPoints
        brevet_dict["short_track"] = [
            firestore_to_track_point(p) for p in brevet_dict.get("short_track", [])
        ]

        # prepare a list of control points (check-in / check-out) necessary to visit
        checkpoints, ids = build_checkpoint_list(get_checkpoints(brevet_dict["uid"], db=db_client))
        # logging.debug(f"Checkpoints {checkpoints} / {ids}")

        # start searching
        try:
            # retrieve activities and transform to a track
            track: FloatArray = get_track_points(sorted([activity], key=lambda a: a["start_date"]), auth_token(riders[0]["strava"]))
            points = track_alignment(
                brevet_dict, track, checkpoints
            )
        except (ActivityNotFound, ActivityError) as error:
            logging.error(f"Activity error {error}")
            continue

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
        client.call_function(request=functions_v1.CallFunctionRequest(
            name=client.cloud_function_path(
                project=os.getenv('GCLOUD_PROJECT'),
                location=os.getenv('FUNCTION_REGION'),
                function="saveResults",
            ),
            data='{"data": {"brevetUid": "%s"}}' % brevet_dict["uid"]
        ))


def search_strava_riders(athlete_id: int) -> List[dict]:
    """
    Query the database for private/{rider}/strava.athlete_id to match the given id
    """
    return [
        db_client.document(f"private/{doc.id}").get().to_dict()
        for doc in db_client.collection("private")
        .where("strava.athlete_id", "==", int(athlete_id))
        .stream()
    ]


def search_brevets(start_date: datetime) -> List[dict]:
    logging.debug(
        f"Lookup brevets in {start_date - timedelta(hours=2)} / {start_date + timedelta(hours=2)}"
    )
    return [
        db_client.document(f"brevets/{doc.id}").get().to_dict()
        for doc in db_client.collection("brevets")
        # lookup +/- 12 hours from the activity start date
        .where("startDate", ">", start_date - timedelta(hours=2))
        .where("startDate", "<", start_date + timedelta(hours=2))
        .stream()
    ]


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
