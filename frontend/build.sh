#!/bin/sh
set -eu

case "$BACKEND_URL" in
  http://*|https://*) api_base="$BACKEND_URL" ;;
  *) api_base="https://$BACKEND_URL" ;;
esac

printf 'window.APP_CONFIG = { apiBase: "%s" };\n' "$api_base" > config.js
