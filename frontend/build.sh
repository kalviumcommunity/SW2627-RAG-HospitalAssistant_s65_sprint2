#!/bin/sh
set -eu

printf 'window.APP_CONFIG = { apiBase: "%s" };\n' "$BACKEND_URL" > config.js
