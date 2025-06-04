#!/bin/bash

# fallback if not set
: "${DOMAIN:=localhost}"
: "${PORT:=5173}"

export ORIGINS="http://${DOMAIN}:${PORT}"

export VITE_API_URL="http://${DOMAIN}:8080/api/v1"
export VITE_SOCKET_URL="http://${DOMAIN}:8080"

redis-server --daemonize yes && \
cd ./back_end/ && \
gunicorn -c gunicorn_config.py run:app & \
cd ./front_end/ && \
npm run dev
