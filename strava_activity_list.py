import json
import logging
from argparse import ArgumentParser, Namespace
from datetime import datetime
from typing import List

import google.cloud.firestore

from strava.api import (
    tokens_expired,
    refresh_tokens,
    get_activities, auth_token,
)

parser = ArgumentParser()
parser.add_argument("-n", "--name", dest="name", help="athlete's name")
parser.add_argument("-b", "--brevet", dest="brevet", help="brevet uid")

args: Namespace = parser.parse_args()

with open(".strava.secret.json", "r") as file:
    secret: dict = json.load(file)

with open(".strava.token.json", "r") as file:
    tokens: dict = json.load(file)

if not args.name or not args.brevet:
    parser.print_help()
    raise Exception("Give both name and brevet")

if args.name not in tokens:
    raise Exception(f"No such name {args.name}")

db_client = google.cloud.firestore.Client()

token: dict = tokens[args.name]

brevet_dict = db_client.document(f"brevets/{args.brevet}").get().to_dict()
if brevet_dict is None:
    raise Exception(f"Brevet {args.brevet} not found")

if tokens_expired(datetime.now(), token):
    token = refresh_tokens(token, secret)
    print(f"Access token {token['access_token']} / expires at {token['expires_at']}")
    tokens[args.name] = token
    with open(".strava.token.json", "w") as file:
        json.dump(tokens, file)

activities: List[dict] = get_activities(brevet_dict, auth_token(token))
for activity in activities:
    print(
        f"activity {activity.get('name')} / {activity.get('id')} {activity.get('start_date')}"
    )
