#!/usr/bin/env bash
set -euo pipefail
APP=/srv/kosmos-lex/app
ENV_FILE="$APP/config/.env"
test "$(id -u)" = 0 || { echo "Run as root" >&2; exit 2; }
test -d "$APP/.git" || { echo "App checkout missing" >&2; exit 2; }
id kosmoslex >/dev/null
if ! test -e "$ENV_FILE"; then
  PG_PASS=$(openssl rand -hex 32)
  SECRET=$(openssl rand -hex 48)
  TMP=$(mktemp)
  cat >"$TMP" <<EOF
SECRET_KEY=$SECRET
DEBUG=False
ENV=dev
ALLOWED_HOSTS=lex.linvora.com.br,127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=https://lex.linvora.com.br
PUBLIC_BASE_URL=https://lex.linvora.com.br
TIME_ZONE=America/Sao_Paulo
DB_NAME=kosmoslex
DB_USER=kosmoslex
DB_PASSWORD=$PG_PASS
DB_HOST=127.0.0.1
DB_PORT=5432
EMAIL_BACKEND=console
EMAIL_NOTIFICATIONS=False
STORAGE_BACKEND=local
SEMANTIC_AUTO_INDEX=False
EOF
  install -o kosmoslex -g kosmoslex -m 0600 "$TMP" "$ENV_FILE"
  rm -f "$TMP"
  echo "APP_ENV_CREATED"
else
  echo "APP_ENV_REUSED"
fi
PG_PASS=$(sed -n 's/^DB_PASSWORD=//p' "$ENV_FILE")
if ! runuser -u postgres -- psql -Atqc "SELECT 1 FROM pg_roles WHERE rolname='kosmoslex'" | grep -qx 1; then
  runuser -u postgres -- psql -v ON_ERROR_STOP=1 -c "CREATE ROLE kosmoslex LOGIN PASSWORD '$PG_PASS';" >/dev/null
  echo "DB_ROLE_CREATED"
else
  echo "DB_ROLE_REUSED"
fi
if ! runuser -u postgres -- psql -Atqc "SELECT 1 FROM pg_database WHERE datname='kosmoslex'" | grep -qx 1; then
  runuser -u postgres -- createdb --owner=kosmoslex kosmoslex
  echo "DATABASE_CREATED"
else
  echo "DATABASE_REUSED"
fi
runuser -u postgres -- psql -v ON_ERROR_STOP=1 -d kosmoslex -c 'CREATE EXTENSION IF NOT EXISTS vector; CREATE EXTENSION IF NOT EXISTS pg_trgm;' >/dev/null
echo "EXTENSIONS_READY"
install -o kosmoslex -g kosmoslex -d -m 0700 "$APP/logs" "$APP/media" "$APP/.dev-sessions"
echo "BOOTSTRAP_OK"
