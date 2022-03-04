import json
from datetime import datetime

import gpxpy
from numpy.typing import ArrayLike

from strava.api import (
    get_activity,
    auth_token,
    tokens_expired,
    refresh_tokens,
    get_track_points,
)

from argparse import ArgumentParser, Namespace

parser = ArgumentParser()
parser.add_argument("-n", "--name", dest="name", help="athlete's name")
parser.add_argument("-a", "--activity", dest="activity", help="activity number")

args: Namespace = parser.parse_args()

with open(".strava.secret.json", "r") as file:
    secret: dict = json.load(file)

with open(".strava.token.json", "r") as file:
    tokens: dict = json.load(file)

if not args.name or not args.activity:
    parser.print_help()
    raise Exception("Give both name and activity")

if args.name not in tokens:
    raise Exception(f"No such name {args.name}")

token: dict = tokens[args.name]
activity_id: int = int(args.activity)

if tokens_expired(datetime.now(), token):
    token = refresh_tokens(token, secret)
    print(f"Access token {token['access_token']} / expires at {token['expires_at']}")
    tokens[args.name] = token
    with open(".strava.token.json", "w") as file:
        json.dump(tokens, file)

activity: dict = get_activity(activity_id, auth_token(token))
track: ArrayLike = get_track_points([activity], auth_token(token))

gpx = gpxpy.gpx.GPX()

gpx_track = gpxpy.gpx.GPXTrack(name=activity["name"])
gpx.tracks.append(gpx_track)

gpx_segment = gpxpy.gpx.GPXTrackSegment()
gpx_track.segments.append(gpx_segment)

for point in track.tolist():
    gpx_segment.points.append(
        gpxpy.gpx.GPXTrackPoint(
            latitude=point[0],
            longitude=point[1],
            time=datetime.utcfromtimestamp(point[2]),
            # Strava distance
            comment=f"{point[3]}",
        )
    )

filename: str = f"activity-{activity_id}.gpx"
with open(filename, mode="w", encoding="utf-8") as file:
    file.write(gpx.to_xml())

print(f"file written: {filename}")
