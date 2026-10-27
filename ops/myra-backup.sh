#!/bin/bash









set -uo pipefail

SRC="${MYRA_DIR:-/srv/backend/myra}"
LOCAL="${MYRA_BACKUP_DIR:-/srv/myra-backups}"
FRONTEND="${MYRA_FRONTEND_DIR:-/srv/myra}"
MIRROR="${MYRA_BACKUP_MIRROR:-/mnt/myra-backups}"
REMOTE_HOST="${MYRA_BACKUP_REMOTE_HOST:-}"
REMOTE_DIR="${MYRA_BACKUP_REMOTE_DIR:-myra-backups}"
REMOTE_TARGET="${REMOTE_HOST}:${REMOTE_DIR%/}/"
SSH_KEY="${MYRA_BACKUP_SSH_KEY:-$HOME/.ssh/id_ed25519}"


DB_ORANKENT_DB=6      # orankenti teljes DB dump
DB_ORANKENT_USER=6    # orankenti felhasznaloi dump
NAPI_KONFIG=7         # napi konfig-tarball
NAPI_DB=7             # napi DB masolat
FRONTEND_MEGTART=3    # napi frontend build

STAMP=$(date +%Y%m%d-%H%M)
TODAY=$(date +%Y%m%d)

mkdir -p "$LOCAL/orankent" "$LOCAL/napi"
chmod 700 "$LOCAL"


eval "$(python3 - "$SRC/.env" <<'PY'
import shlex, sys
from urllib.parse import urlparse, unquote
env = {}
for sor in open(sys.argv[1], encoding="utf-8"):
    sor = sor.strip()
    if sor and not sor.startswith("#") and "=" in sor:
        k, v = sor.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
u = urlparse(env.get("DATABASE_URL", "").replace("postgresql+asyncpg://", "postgresql://"))
ertekek = {
    "PGHOST": u.hostname or "",
    "PGPORT": str(u.port or 5432),
    "PGDATABASE": (u.path or "/postgres").lstrip("/") or "postgres",
    "PGUSER": unquote(u.username or ""),
    "PGPASSWORD": unquote(u.password or ""),
    "PGSSLMODE": env.get("DATABASE_SSL_MODE") or "require",
    "PGCONNECT_TIMEOUT": "15",
}
for k, v in ertekek.items():
    print(f"export {k}={shlex.quote(v)}")
PY
)"
if [ -z "${PGHOST:-}" ]; then
  echo "HIBA: nincs DATABASE_URL az .env-ben, a mentes kimaradt"
  exit 1
fi

DUMP="$LOCAL/orankent/db-$STAMP.sql.gz"
pg_dump -n public --no-owner --no-privileges --clean --if-exists | gzip > "$DUMP"

if [ ! -s "$DUMP" ] || [ "$(stat -c%s "$DUMP")" -lt 1000 ]; then
  rm -f "$DUMP"
  echo "HIBA: a pg_dump ures vagy csonka, a mentes kimaradt"
  exit 1
fi


USERDUMP="$LOCAL/orankent/userdata-$STAMP.sql.gz"
pg_dump -n public --no-owner --no-privileges --clean --if-exists \
  --exclude-table-data=public.knowledge_chunks | gzip > "$USERDUMP"
if [ ! -s "$USERDUMP" ] || [ "$(stat -c%s "$USERDUMP")" -lt 1000 ]; then
  rm -f "$USERDUMP"
  echo "FIGYELEM: a felhasznaloi mentes ures vagy csonka, kimaradt"
fi
unset PGPASSWORD


if [ ! -f "$LOCAL/napi/myra-$TODAY.tar.gz" ]; then



  STAGE="$LOCAL/.stage-$TODAY"
  rm -rf "$STAGE"; mkdir -p "$STAGE/konfig"
  for f in /etc/caddy/Caddyfile /etc/fail2ban/filter.d /etc/fail2ban/jail.d \
           /etc/systemd/system/myra-watch.service /etc/systemd/system/myra-backup.service \
           /etc/systemd/system/myra-backup.timer; do
    [ -e "$f" ] || continue
    cp -r "$f" "$STAGE/konfig/" 2>/dev/null || true
  done
  {
    echo "# WireGuard nyilvantartas (privat kulcsok szandekosan nincsenek benne)"
    wg show 2>/dev/null || echo "wg show nem elerheto"
    echo "# Publikus kulcsok:"
    cat /etc/wireguard/*.pub 2>/dev/null || true
  } > "$STAGE/konfig/wireguard-allapot.txt"
  tar -czf "$LOCAL/napi/konfig-$TODAY.tar.gz" -C "$STAGE" konfig 2>/dev/null
  rm -rf "$STAGE"

  tar -czf "$LOCAL/napi/myra-$TODAY.tar.gz" -C "$SRC" \
    .env docker-compose.yml docker-compose.override.yml \
    backend/server.py backend/data/kb_pdfs 2>/dev/null
  cp "$DUMP" "$LOCAL/napi/db-$TODAY.sql.gz"
fi



if [ -d "$FRONTEND" ] && [ ! -f "$LOCAL/napi/frontend-$TODAY.tar.gz" ]; then
  tar -czf "$LOCAL/napi/frontend-$TODAY.tar.gz" -C "$FRONTEND" . 2>/dev/null
fi


torles_darabszam() {  # $1=mappa $2=minta $3=megtartott darab
  ls -1t "$1"/$2 2>/dev/null | tail -n +$(( $3 + 1 )) | while read -r f; do rm -f "$f"; done
}
torles_darabszam "$LOCAL/orankent" 'db-*.sql.gz'       "$DB_ORANKENT_DB"
torles_darabszam "$LOCAL/orankent" 'userdata-*.sql.gz' "$DB_ORANKENT_USER"
torles_darabszam "$LOCAL/napi"     'myra-*.tar.gz'     "$NAPI_KONFIG"
torles_darabszam "$LOCAL/napi"     'db-*.sql.gz'       "$NAPI_DB"
torles_darabszam "$LOCAL/napi"     'frontend-*.tar.gz' "$FRONTEND_MEGTART"
torles_darabszam "$LOCAL/napi"     'konfig-*.tar.gz'   "$NAPI_KONFIG"


if mountpoint -q /mnt/win; then
  mkdir -p "$MIRROR"
  rsync -a --delete "$LOCAL/" "$MIRROR/"
else
  echo "FIGYELEM: /mnt/win nincs csatolva, a tukrozes kimaradt"
fi


if [ -n "$REMOTE_HOST" ] && ssh -i "$SSH_KEY" -o BatchMode=yes -o ConnectTimeout=8 "$REMOTE_HOST" true 2>/dev/null; then
  if rsync -a --delete -e "ssh -i $SSH_KEY -o BatchMode=yes" "$LOCAL/" "$REMOTE_TARGET" 2>/dev/null; then
    echo "off-host backup target updated"
  else
    echo "FIGYELEM: az rsync a távoli mentési célra nem sikerult"
  fi
else
  echo "FIGYELEM: az off-host SSH backup nem sikerult"
fi

echo "mentes kesz: $DUMP ($(du -h "$DUMP" | cut -f1)), helyben: $(du -sh "$LOCAL" | cut -f1), darabok: $(ls -1 "$LOCAL/orankent" | wc -l) orankenti + $(ls -1 "$LOCAL/napi" | wc -l) napi"
