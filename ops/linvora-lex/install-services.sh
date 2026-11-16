#!/usr/bin/env bash
set -euo pipefail
APP=/srv/kosmos-lex/app
TEMPLATE="$APP/ops/linvora-lex"
test "$(id -u)" = 0 || { echo "Run as root" >&2; exit 2; }
test -x "$APP/.venv/bin/gunicorn" || { echo "Python env missing" >&2; exit 2; }
install -o root -g root -m 0644 "$TEMPLATE/kosmos-lex.service" /etc/systemd/system/kosmos-lex.service
install -o root -g root -m 0644 "$TEMPLATE/kosmos-lex-worker.service" /etc/systemd/system/kosmos-lex-worker.service
# Root-owned backup executable: the kosmoslex Git checkout is writable by the app user.
install -o root -g root -m 0750 "$TEMPLATE/backup-lex.sh" /usr/local/sbin/kosmos-lex-backup
install -o root -g root -m 0644 "$TEMPLATE/kosmos-lex-backup.service" /etc/systemd/system/kosmos-lex-backup.service
install -o root -g root -m 0644 "$TEMPLATE/kosmos-lex-backup.timer" /etc/systemd/system/kosmos-lex-backup.timer
systemctl daemon-reload
systemctl enable --now kosmos-lex.service kosmos-lex-worker.service kosmos-lex-backup.timer
systemctl is-active --quiet kosmos-lex.service
systemctl is-active --quiet kosmos-lex-worker.service
systemctl is-active --quiet kosmos-lex-backup.timer
echo "SERVICES_ACTIVE"
# Production HTTPS is handled by the existing Caddy instance.
# The Django account login + email/TOTP is the single user-facing authentication.
install -o root -g root -m 0644 "$TEMPLATE/lex.caddy.template" /etc/caddy/lex.caddy
if ! grep -Fxq 'import /etc/caddy/lex.caddy' /etc/caddy/Caddyfile; then
  cp -p /etc/caddy/Caddyfile /etc/caddy/Caddyfile.before-kosmos-lex-20261116
  printf '\n# Kosmos Lex pilot (separate host)\nimport /etc/caddy/lex.caddy\n' >> /etc/caddy/Caddyfile
fi
if ! caddy validate --config /etc/caddy/Caddyfile; then
  echo "CADDY_VALIDATION_FAILED; no reload" >&2
  exit 1
fi
systemctl reload caddy
systemctl is-active --quiet caddy
echo "CADDY_RELOADED"
