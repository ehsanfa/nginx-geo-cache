from flask import Flask, make_response, request
import redis
import json

app = Flask(__name__)
r = redis.Redis(host='redis', port=6379, db=0)

@app.route('/', methods=["GET"])
def index():
	lat = float(request.args.get("lat"))
	lng = float(request.args.get("long"))
	store_id = int(((lat+lng)%10)*10000)
	store = json.dumps({
		"address": "SAMPLE STORE ADDRESS",
		"name": "SAMPLE STORE NAME",
		"id": store_id
	})
	r.geoadd("stores", lng, lat, store)
	return make_response(store, 200)