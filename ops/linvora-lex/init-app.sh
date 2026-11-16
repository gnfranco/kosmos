#!/usr/bin/env bash
set -euo pipefail
APP=/srv/kosmos-lex/app
test "$(id -u)" = 0 || { echo "Run as root" >&2; exit 2; }
cd "$APP"
manage() { runuser -u kosmoslex -- "$APP/.venv/bin/python" manage.py "$@"; }
manage check
manage migrate --noinput
manage createcachetable
manage installwatson
manage buildwatson
manage setup_schedules
manage collectstatic --noinput
manage check --deploy
echo "KOSMOS_LEX_DJANGO_READY"
