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