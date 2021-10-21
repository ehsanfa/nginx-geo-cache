from flask import Flask, make_response, request
import json

app = Flask(__name__)

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
	return make_response(store, 200)