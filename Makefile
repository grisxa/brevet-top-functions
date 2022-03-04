PROJECT_ID = baltic-star-cloud

credentials:
	export GOOGLE_APPLICATION_CREDENTIALS=`pwd`/temp/baltic-star-cloud-1866072fbe42.json
	# export FIRESTORE_EMULATOR_HOST="localhost:8080"
	export GCLOUD_PROJECT="baltic-star-cloud"

brevet: credentials
	FIRESTORE_EMULATOR_HOST="localhost:8080" \
	GCLOUD_PROJECT="baltic-star-cloud" \
	GOOGLE_APPLICATION_CREDENTIALS=`pwd`/temp/baltic-star-cloud-1866072fbe42.json \
	functions_framework --target=update_brevet_route --signature-type event --port 9090 --debug

checkpoints: credentials
	FIRESTORE_EMULATOR_HOST="localhost:8080" \
	FIREBASE_AUTH_EMULATOR_HOST="localhost:9099" \
	GCLOUD_PROJECT="baltic-star-cloud" \
	GOOGLE_APPLICATION_CREDENTIALS=`pwd`/temp/baltic-star-cloud-1866072fbe42.json \
	functions_framework --target=create_checkpoints --signature-type http --port 9090 --debug

save: credentials
	GCLOUD_PROJECT="baltic-star-cloud" \
	GOOGLE_APPLICATION_CREDENTIALS=`pwd`/temp/baltic-star-cloud-1866072fbe42.json \
	functions_framework --target=save_results --signature-type http --port 9090 --debug

export: credentials
	GCLOUD_PROJECT="baltic-star-cloud" \
	GOOGLE_APPLICATION_CREDENTIALS=`pwd`/temp/baltic-star-cloud-1866072fbe42.json \
	functions_framework --target=json_export --signature-type http --port 9090 --debug


search: credentials
	GCLOUD_PROJECT="baltic-star-cloud" \
	GOOGLE_APPLICATION_CREDENTIALS=`pwd`/temp/baltic-star-cloud-1866072fbe42.json \
	functions_framework --target=search_activities --signature-type http --port 9090 --debug


watcher: credentials
	FIRESTORE_EMULATOR_HOST="localhost:8080" \
	GCLOUD_PROJECT="baltic-star-cloud" \
	GOOGLE_APPLICATION_CREDENTIALS=`pwd`/temp/baltic-star-cloud-1866072fbe42.json \
	STRAVA='{"client_id": "65987", "client_secret": "b90b1bf1781c19c559794acceadb4ddacbf416ae", "subscription_id": "209124", "verify_token": "RQhWqY8ZsfvEkcbvGJ9x"}' \
	functions_framework --target=strava_watcher --signature-type event --port 9090 --debug

checkin: credentials
	FIRESTORE_EMULATOR_HOST="localhost:8080" \
	GCLOUD_PROJECT="baltic-star-cloud" \
	GOOGLE_APPLICATION_CREDENTIALS=`pwd`/temp/baltic-star-cloud-1866072fbe42.json \
	functions_framework --target=check_in --signature-type http --port 9090 --debug

emulator:
	cd ../baltic-star-cloud && firebase emulators:start --only functions,firestore,auth

angular:
	cd ../baltic-star-cloud && ng serve

deploy-brevet: credentials
	gcloud functions deploy updateBrevetRoute \
	  --entry-point update_brevet_route \
	  --runtime python39 \
	  --timeout 180 \
	  --trigger-event "providers/cloud.firestore/eventTypes/document.update" \
	  --trigger-resource "projects/${PROJECT_ID}/databases/(default)/documents/brevets/{brevetUid}"

deploy-watcher: credentials
	gcloud beta functions deploy stravaWatcher \
	  --entry-point strava_watcher \
	  --runtime python39 \
	  --trigger-topic strava \
	  --timeout 300 \
	  --memory 512MB \
	  --set-secrets 'STRAVA=projects/baltic-star-cloud/secrets/strava:latest'


deploy-checkpoints: credentials
	gcloud beta functions deploy createCheckpoints \
	  --entry-point create_checkpoints \
	  --runtime python39 \
	  --trigger-http \
	  --allow-unauthenticated

deploy-search: credentials
	gcloud beta functions deploy stravaSearchActivities \
	  --entry-point search_activities \
	  --runtime python39 \
	  --trigger-http \
	  --timeout 300 \
	  --memory 512MB \
	  --allow-unauthenticated

deploy-save: credentials
	gcloud beta functions deploy saveResults \
	  --entry-point save_results \
	  --runtime python39 \
	  --trigger-http \
	  --memory 512MB \
	  --allow-unauthenticated

deploy-export: credentials
	gcloud beta functions deploy jsonExport \
	  --entry-point json_export \
	  --runtime python39 \
	  --trigger-http \
	  --memory 512MB \
	  --allow-unauthenticated

test-brevet:
	# curl https://us-central1-baltic-star-cloud.cloudfunctions.net/updateBrevetRoute
	curl localhost:9090 \
	  -X POST \
	  -H "Content-Type: application/json" \
	  -d '@route_change.json'

#	  -H "Authorization: bearer `gcloud auth print-identity-token`"
#	  -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IjM1MDZmMzc1MjI0N2ZjZjk0Y2JlNWQyZDZiNTlmYThhMmJhYjFlYzIiLCJ0eXAiOiJKV1QifQ.eyJuYW1lIjoi0JPRgNC40LPQvtGA0LjQuSDQkdCw0YLQsNC70L7QsiIsImlzcyI6Imh0dHBzOi8vc2VjdXJldG9rZW4uZ29vZ2xlLmNvbS9iYWx0aWMtc3Rhci1jbG91ZCIsImF1ZCI6ImJhbHRpYy1zdGFyLWNsb3VkIiwiYXV0aF90aW1lIjoxNjQxNjAxOTUwLCJ1c2VyX2lkIjoiR2lOVmZPRWZrSmZLRVhzSWxMNnhxWVhBekdsMSIsInN1YiI6IkdpTlZmT0Vma0pmS0VYc0lsTDZ4cVlYQXpHbDEiLCJpYXQiOjE2NDE2MDE5NTAsImV4cCI6MTY0MTYwNTU1MCwiZW1haWwiOiJncmlzeGFAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImZpcmViYXNlIjp7ImlkZW50aXRpZXMiOnsiZ29vZ2xlLmNvbSI6WyIxMDQ3MTU0MDY2NDY1NzMwOTI0NDIiXSwib2lkYy5iYWx0aWNzdGFyIjpbIjE4MCJdLCJlbWFpbCI6WyJncmlzeGFAZ21haWwuY29tIl19LCJzaWduX2luX3Byb3ZpZGVyIjoiZ29vZ2xlLmNvbSJ9fQ.fBjmdjrdfqD0RSpqEjJNnU3w-WZ_1pyVfsgYdF94O1MRJazl_TRJ43CCZX9mz1Bkfk78hgp7-Zcg8PQFff4mG_-0uhdvE3kJ6H95IciKmyRmoqa8_oL2aMBZ4iDfeExexMSCIheyrT2jXqpKAeK-CYfsvE4KqmZzcS6V3wqrauWtmRfMe14cHlbLnpOBJu_5NIhOhmQsVVTqVuFAQyK4fZT92HGuCZaNN-1WIf_lbxT4F6DXbzQdNVIOBbMFPawo_gVpMpFKCstjwDtbW3RtaIlgePJjO0ofCm6aGqb-4QVFExZVOqXjWowz3mkrzINF-CxkE-kIKpAk9_P5BWtWqw" \
#	  -H "Authorization: Bearer eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJuYW1lIjoiT3JhbmdlIFJhY2Nvb24iLCJlbWFpbCI6Im9yYW5nZS5yYWNjb29uLjM5NkBleGFtcGxlLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJhdXRoX3RpbWUiOjE2NDE1NTI4MjksInVzZXJfaWQiOiJoOTJHUXVsWmgxTlRYa0VEUk9KZzhXNlZJdFIzIiwiZmlyZWJhc2UiOnsiaWRlbnRpdGllcyI6eyJlbWFpbCI6WyJvcmFuZ2UucmFjY29vbi4zOTZAZXhhbXBsZS5jb20iXSwiZ29vZ2xlLmNvbSI6WyI1MTEwMzM5NzQwMzcxNjIxNzQwNTIyNjEyNTQwNDAzMjc2MzkzMDYwIl19LCJzaWduX2luX3Byb3ZpZGVyIjoiZ29vZ2xlLmNvbSJ9LCJpYXQiOjE2NDE2MDUyMzUsImV4cCI6MTY0MTYwODgzNSwiYXVkIjoiYmFsdGljLXN0YXItY2xvdWQiLCJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vYmFsdGljLXN0YXItY2xvdWQiLCJzdWIiOiJoOTJHUXVsWmgxTlRYa0VEUk9KZzhXNlZJdFIzIn0." \

test-strava:
	curl localhost:9090 \
	  -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6ImYyNGYzMTQ4MTk3ZWNlYTUyOTE3YzNmMTgzOGFiNWQ0ODg3ZWEwNzYiLCJ0eXAiOiJKV1QifQ.eyJuYW1lIjoi0JPRgNC40LPQvtGA0LjQuSDQkdCw0YLQsNC70L7QsiIsImlzcyI6Imh0dHBzOi8vc2VjdXJldG9rZW4uZ29vZ2xlLmNvbS9iYWx0aWMtc3Rhci1jbG91ZCIsImF1ZCI6ImJhbHRpYy1zdGFyLWNsb3VkIiwiYXV0aF90aW1lIjoxNjQ0ODIzNDYxLCJ1c2VyX2lkIjoicVE3cUZWS1V1QWZ4ejVHUVRCZEU0MmpGOFA4MyIsInN1YiI6InFRN3FGVktVdUFmeHo1R1FUQmRFNDJqRjhQODMiLCJpYXQiOjE2NDQ4MzgwNzIsImV4cCI6MTY0NDg0MTY3MiwiZW1haWwiOiJncmlzeGFAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImZpcmViYXNlIjp7ImlkZW50aXRpZXMiOnsiZ29vZ2xlLmNvbSI6WyIxMDQ3MTU0MDY2NDY1NzMwOTI0NDIiXSwib2lkYy5iYWx0aWNzdGFyIjpbIjE4MCJdLCJlbWFpbCI6WyJncmlzeGFAZ21haWwuY29tIl19LCJzaWduX2luX3Byb3ZpZGVyIjoib2lkYy5iYWx0aWNzdGFyIiwic2lnbl9pbl9hdHRyaWJ1dGVzIjp7ImF0X2hhc2giOiJ3YkZic1JkUlBpZ282NF9PVWNmMFpRIiwiY291bnRyeSI6ItCg0L7RgdGB0LjRjyIsImNpdHkiOiLQodCw0L3QutGCLdCf0LXRgtC10YDQsdGD0YDQsyIsImJpcnRoRGF0ZSI6IjE5NzctMDYtMDUifX19.RcLkWfdWD9dblbrPo73zKST77QFQKtg2I32J0VqkJKVd-6h8y-9-2vLLrYxLOBiR1YfX3fZas4nf9ysGO1s_BPgkGVqfySK67XAjtoYsWwHl8ryw8EaFThqINj9AaetJm-YCi8MudqMPqaAZ6EccmHDPtpsgD1zviuFI7ipO8ADtelPr31awJb-GbmK3qX9TxvH9Ig0Espxrg_1F5C7JqNG_0nTAlSQNh-3s4UqXaAt_-avFJAnuiI_b5b-uBc6NTqOFbdj7azCoDu9pe4PWDsDHIK425Jg-P8QUDnTobUyYF3_CJ-2i8ERiYUUgaMHSo1WQJoXQ7FNuaYE8Oz_ayw" \
	  -X POST \
	  -H "Content-Type:application/json" \
	  -d '{"data": {"brevetUid": "bGJa6nII0SDo521Imv6M", "riderUid": "qQ7qFVKUuAfxz5GQTBdE42jF8P83", "tokens": null}}'

test-strava-online:
	curl https://us-central1-baltic-star-cloud.cloudfunctions.net/stravaSearchActivities \
	  -H "Authorization: Bearer eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJuYW1lIjoiT3JhbmdlIFJhY2Nvb24iLCJlbWFpbCI6Im9yYW5nZS5yYWNjb29uLjM5NkBleGFtcGxlLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJhdXRoX3RpbWUiOjE2NDE1NTI4MjksInVzZXJfaWQiOiJoOTJHUXVsWmgxTlRYa0VEUk9KZzhXNlZJdFIzIiwiZmlyZWJhc2UiOnsiaWRlbnRpdGllcyI6eyJlbWFpbCI6WyJvcmFuZ2UucmFjY29vbi4zOTZAZXhhbXBsZS5jb20iXSwiZ29vZ2xlLmNvbSI6WyI1MTEwMzM5NzQwMzcxNjIxNzQwNTIyNjEyNTQwNDAzMjc2MzkzMDYwIl19LCJzaWduX2luX3Byb3ZpZGVyIjoiZ29vZ2xlLmNvbSJ9LCJpYXQiOjE2NDE2MDUyMzUsImV4cCI6MTY0MTYwODgzNSwiYXVkIjoiYmFsdGljLXN0YXItY2xvdWQiLCJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vYmFsdGljLXN0YXItY2xvdWQiLCJzdWIiOiJoOTJHUXVsWmgxTlRYa0VEUk9KZzhXNlZJdFIzIn0." \
	  -X POST \
	  -H "Content-Type:application/json" \
	  -d '{"data": {"brevetUid": "bGJa6nII0SDo521Imv6M", "riderUid": "qQ7qFVKUuAfxz5GQTBdE42jF8P83", "tokens": null}}'

test-watcher:
	curl "localhost:9090/baltic-star-cloud/us-central1/stravaWatcher" \
	  -X POST \
	  -H "Content-Type:application/json" \
	  -d '@strava_update.json'

test-checkpoints:
	curl "localhost:9090/baltic-star-cloud/us-central1/create_checkpoints"  \
	  -H "Authorization: Bearer eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJuYW1lIjoiT3JhbmdlIFJhY2Nvb24iLCJlbWFpbCI6Im9yYW5nZS5yYWNjb29uLjM5NkBleGFtcGxlLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJhdXRoX3RpbWUiOjE2NDE1NTI4MjksInVzZXJfaWQiOiJoOTJHUXVsWmgxTlRYa0VEUk9KZzhXNlZJdFIzIiwiZmlyZWJhc2UiOnsiaWRlbnRpdGllcyI6eyJlbWFpbCI6WyJvcmFuZ2UucmFjY29vbi4zOTZAZXhhbXBsZS5jb20iXSwiZ29vZ2xlLmNvbSI6WyI1MTEwMzM5NzQwMzcxNjIxNzQwNTIyNjEyNTQwNDAzMjc2MzkzMDYwIl19LCJzaWduX2luX3Byb3ZpZGVyIjoiZ29vZ2xlLmNvbSJ9LCJpYXQiOjE2NDE2MDUyMzUsImV4cCI6MTY0MTYwODgzNSwiYXVkIjoiYmFsdGljLXN0YXItY2xvdWQiLCJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vYmFsdGljLXN0YXItY2xvdWQiLCJzdWIiOiJoOTJHUXVsWmgxTlRYa0VEUk9KZzhXNlZJdFIzIn0." \
	  -X POST \
	  -H "Content-Type:application/json" \
	  -d '{"data": {"brevetUid": "bGJa6nII0SDo521Imv6M"}}'

test-save:
	curl "localhost:9090/baltic-star-cloud/us-central1/save_results"  \
	  -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IjI3ZGRlMTAyMDAyMGI3OGZiODc2ZDdiMjVlZDhmMGE5Y2UwNmRiNGQiLCJ0eXAiOiJKV1QifQ.eyJuYW1lIjoiR3JpZ29yeSBCYXRhbG92IiwicGljdHVyZSI6Imh0dHBzOi8vbGg1Lmdvb2dsZXVzZXJjb250ZW50LmNvbS8tVTZLeTJjLTVHUFkvQUFBQUFBQUFBQUkvQUFBQUFBQUFBQUEvQU1adXVjbFQyeDlVN0pod3pSczU3YkRnM01jY1hNNTFDQS9waG90by5qcGciLCJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vYmFsdGljLXN0YXItY2xvdWQiLCJhdWQiOiJiYWx0aWMtc3Rhci1jbG91ZCIsImF1dGhfdGltZSI6MTY0NDk2ODA5NSwidXNlcl9pZCI6IklJQ21LNEJlWVVQSVZScFFpWm9XbjVTRnJpaDEiLCJzdWIiOiJJSUNtSzRCZVlVUElWUnBRaVpvV241U0ZyaWgxIiwiaWF0IjoxNjQ1NDk2MjI2LCJleHAiOjE2NDU0OTk4MjYsImVtYWlsIjoiZ3JpZ29yeS5iYXRhbG92QGdtYWlsLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJmaXJlYmFzZSI6eyJpZGVudGl0aWVzIjp7Imdvb2dsZS5jb20iOlsiMTE2MTMyMjIwMTYzMDc1MzI0MTYzIl0sImVtYWlsIjpbImdyaWdvcnkuYmF0YWxvdkBnbWFpbC5jb20iXX0sInNpZ25faW5fcHJvdmlkZXIiOiJnb29nbGUuY29tIn19.X_-0OKZ9mL7QGQAR6-cgEU6jG_tQ3TQHaQeluvlBPbKmj4LJuO1FAWETFCuwQiBkDZ4GFdIfK-jZPHv1-eTRGwACm9WvqHKKkwbnPTq-RxTPRSogg6ocukP8rPMUFsEDVprrWtUE3caeu2bxM31ggzZIdd5ex8eLaG73UOD2n6ZInp7ZAsZp7eJcarQlFv6P_V2KCVRmhyMDu5Jt0sLyi8PCw4kuNsl5GsCEah3qE6YcrGq9EHEOSz0glleddOLQvZ33AkNIfZbpaVUG4eIjdX4nsDpoaYG12XEGM5lwWLHAo0b-VbjKv7S10TSFMDulycntByOQIHAfF_78XCx6iA" \
	  -X POST \
	  -H "Content-Type:application/json" \
	  -d '{"data": {"brevetUid": "3qoaMn3vtrB9tCYssTgX"}}'

test-export:
	curl "localhost:9090/baltic-star-cloud/us-central1/export_json/brevet/UGCiVCQv9DapyCEcb75u"  \
	  -X GET

test-checkin:
	curl "localhost:9090/baltic-star-cloud/us-central1/check_in"  \
	  -X POST \
	  -H "Content-Type:application/json" \
	  -d '{"data": {"time": "1636436787", "controlUid": "CsJgqUa6w9RVy8yGsaNh", "riderUid": "78HM3eyMTqhEelqc7gBP5Sv4pPG2"}}'

# gcloud api-gateway api-configs create hello-config-3 --api=hello-api-2 --openapi-spec=api/openapi2.yaml  --backend-auth-service-account=python-baltic-star-cloud@baltic-star-cloud.iam.gserviceaccount.com
# gcloud api-gateway gateways update hello-gateway-2 --api-config=hello-config-3 --api=hello-api-2 --location=us-central1 --project=baltic-star-cloud


test:
	GCLOUD_PROJECT="baltic-star-cloud" \
	GOOGLE_APPLICATION_CREDENTIALS=`pwd`/temp/baltic-star-cloud-1866072fbe42.json \
	python -m pytest -vv
