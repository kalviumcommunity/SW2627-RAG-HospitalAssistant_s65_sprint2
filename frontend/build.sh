#!/bin/sh
set -eu

case "$BACKEND_URL" in
  http://*|https://*) api_base="$BACKEND_URL" ;;
  *) api_base="https://$BACKEND_URL" ;;
esac
api_base="${api_base%/}"

printf 'window.APP_CONFIG = { apiBase: "%s" };\n' "$api_base" > config.js
