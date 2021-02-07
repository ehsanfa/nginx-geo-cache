The following approach uses `Nginx` to serve the user with already cached `geolocation` based data based on the `location` of the user.

Assume we have an application, which gets the `latitude` and the `longitude` of the user, searches through a database which in this sample application, saves "stores" based on their location, and responds to the user with the nearest store to them.
Now imagine that in a reasonable time in the future, we get another request from another user based in a similar geographical location, e.g. in a 10km radius. In this case, we can use the same data we served to the first user.

To reach this goal we can have a cache database, in this case, Redis, to save the response alongside the location of the user and use it for the upcoming requests nearby the original user.

This approach aims to move the caching part of the mentioned application above to the `Nginx`. This way if the incoming request already has cached data, there's no need to bother the application about it. `Nginx` just serves the user with cached data and this could have a huge performance impact when we have a reasonable portion of `HITs` on our caching mechanism.

Let's take a look at how I've done it.

The application has three services:
- A web application, in this case, a simple Flask app, to generate responses.
- A `Nginx` to get the request, check for any existing data, and serving to the user.
- A database, in this case, `Redis`, to save the cached data.

```
version: '3'
services:
  nginx:
    build:
      context: ./nginx
      dockerfile: deploy/Dockerfile
    ports:
      - 8080:80
  app:
    build:
      context: ./app
      dockerfile: deploy/Dockerfile
  redis:
    image: redis:6-alpine
```

## 1. Application
As mentioned above, the application is a simple `Flask` app, which gets the request from the user and serves an arbitrary response.
The request in this case simply contains a `lat` for the latitude and a `long` for the longitude of the user. Then it simply calculates a store `id`, saves it to the `Redis`, and serves the user.
```
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
```

## 2. Nginx
This is the place that all the magic happens. Let start with the `Dockerfile`.
```
FROM openresty/openresty:alpine-fat

RUN luarocks install redis-lua

COPY ./src/conf.d /etc/nginx/conf.d
COPY ./src/modules /usr/local/openresty/nginx
```
The reason I've chosen `openresty` is that it already has the `lua` builtin. But it'd be more reasonable to compile an `Nginx` from scratch with additional `lua` functionalities.

We also need the `lua` to interact with `Redis`, so we need to install it using `luarocks install redis-lua`.

And at last, we need to copy our `Nginx` configuration files and written `lua` modules to the container. We'll get to them next.

Now for the `Nginx` configuration we simply need a location to handle the caching, in this case, the root endpoint.
```
location = / {
	content_by_lua_file cache.lua;
}
```
The content of the response is produced by a `lua` file, named `cache.lua`. We'll get to that later.
We also need an internal location, which cannot be accessible from the outside of `Nginx`, to handle requests to the `Flask` application. We'll get to that later too.
```
location = /app {
    	internal;
    	proxy_pass http://app:80/;
    }
}
```

Now it comes to the main part of the whole application, the `cache.lua` file that handles the caching. This file gets parameters from the request, searches through the `redis` database for any near records, serves the user if anything is found, and otherwise requests to the upstream application.
```
local redis = require 'redis'

redis.commands.georadius = redis.command('GEORADIUS')

local client = redis.connect('redis', 6379)
local lat = ngx.var.arg_lat
local long = ngx.var.arg_long

if not lat or not long then
	ngx.status = 400
	ngx.say("please insert lat and long parameters")
	ngx.exit(ngx.OK)
end

local cache_radius = 10
local cache_radius_unit = "km"

local cached_value = client:georadius("stores", long, lat, cache_radius, cache_radius_unit, "ASC")[1]
if cached_value then
	ngx.header["Content-Type"] = "application/json"
	return ngx.say(cached_value)
end
local res = ngx.location.capture("/app", {
	args = {
		lat = lat,
		long = long
	}
})
ngx.status = res.status  
return ngx.say(res.body)
```

## 3. redis
The redis part is completely straightforward. There's no customization or anything special happening, it just runs a container from a `redis` standard docker repository and handles the save and the load requests.