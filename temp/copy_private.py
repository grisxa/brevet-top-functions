import logging

import google.cloud.firestore
import google.cloud.logging

log_client = google.cloud.logging.Client()
logging.basicConfig(level=logging.DEBUG)
db_client = google.cloud.firestore.Client()

for doc in db_client.collection("private").stream():
    rider: dict = db_client.document(f"private/{doc.id}").get().to_dict()

    logging.debug(f"rider {rider['uid']}")
    db_client.document(f"private/{doc.id}").set(
        {
            "alive": True,
        },
        merge=True,
    )

exit(0)

for doc in db_client.collection("riders").stream():
    rider: dict = db_client.document(f"riders/{doc.id}").get().to_dict()
    providers: list = rider.pop("providers", [])
    if len(providers) < 1:
        continue
    logging.debug(f"rider {rider['displayName']}")
    db_client.document(f"private/{doc.id}").set(
        {
            "uid": doc.id,
            "providers": providers,
        },
        merge=True,
    )
    db_client.document(f"riders/{doc.id}").set(rider, merge=False)
