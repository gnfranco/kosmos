#!/usr/bin/env bash
set -euo pipefail
APP=/srv/kosmos-lex/app
EMAIL="${1:-}"
test "$(id -u)" = 0 || { echo "Run as root" >&2; exit 2; }
case "$EMAIL" in *@*.*) ;; *) echo "Provide an admin email address" >&2; exit 2;; esac
python3 - "$APP/config/.env" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
s = p.read_text()
if "EMAIL_BACKEND=console" in s:
    s = s.replace("EMAIL_BACKEND=console", """EMAIL_BACKEND=smtp
EMAIL_HOST=127.0.0.1
EMAIL_PORT=25
EMAIL_USE_TLS=False
SERVER_EMAIL=noreply@linvora.com.br
DEFAULT_FROM_EMAIL=noreply@linvora.com.br
BILLING_FROM_EMAIL=noreply@linvora.com.br""", 1)
    p.write_text(s)
print("SMTP_LOCAL_CONFIGURED")
PY
if grep -q '^DJANGO_ADMIN_EMAIL=' /root/kosmos-lex-access.txt; then
  echo "ADMIN_ALREADY_BOOTSTRAPPED"
else
  PASSWORD=$(openssl rand -hex 16)
  cd "$APP"
  runuser -u kosmoslex -- env DJANGO_SUPERUSER_USERNAME=lexadmin DJANGO_SUPERUSER_EMAIL="$EMAIL" DJANGO_SUPERUSER_PASSWORD="$PASSWORD" "$APP/.venv/bin/python" manage.py createsuperuser --noinput
  umask 077
  printf 'DJANGO_ADMIN_EMAIL=%s\nDJANGO_ADMIN_PASSWORD=%s\n' "$EMAIL" "$PASSWORD" >> /root/kosmos-lex-access.txt
  chmod 600 /root/kosmos-lex-access.txt
  echo "ADMIN_CREATED"
fi
systemctl restart kosmos-lex.service kosmos-lex-worker.service
systemctl is-active --quiet kosmos-lex.service
systemctl is-active --quiet kosmos-lex-worker.service
echo "LEX_ADMIN_AND_EMAIL_READY"
