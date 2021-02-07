FROM openresty/openresty:alpine-fat

RUN luarocks install redis-lua

COPY ./src/conf.d /etc/nginx/conf.d
COPY ./src/modules /usr/local/openresty/nginx