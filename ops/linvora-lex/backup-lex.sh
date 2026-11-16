#!/usr/bin/env bash
set -euo pipefail
umask 077
test "$(id -u)" = 0 || { echo 'Root required' >&2; exit 2; }
APP=/srv/kosmos-lex/app
BACKUPS=/srv/kosmos-lex/backups
install -d -m 0700 -o root -g root "$BACKUPS"
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
SQL="$BACKUPS/kosmoslex-$STAMP.dump"
MEDIA="$BACKUPS/kosmoslex-media-$STAMP.tar.gz"
runuser -u postgres -- pg_dump -Fc kosmoslex > "$SQL"
pg_restore --list "$SQL" >/dev/null
tar -C "$APP" -czf "$MEDIA" media
chmod 600 "$SQL" "$MEDIA"
sha256sum "$SQL" "$MEDIA" > "$BACKUPS/kosmoslex-$STAMP.sha256"
chmod 600 "$BACKUPS/kosmoslex-$STAMP.sha256"
echo "BACKUP_SQL=$SQL"
echo "BACKUP_MEDIA=$MEDIA"
echo "BACKUP_VALIDATED"
