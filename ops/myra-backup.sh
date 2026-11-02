#!/bin/bash


set -euo pipefail
umask 077

SRC="${MYRA_DIR:-/srv/backend/myra}"
LOCAL="${MYRA_BACKUP_DIR:-/srv/myra-backups}"
FRONTEND="${MYRA_FRONTEND_DIR:-/srv/frontend/dist}"
MIRROR="${MYRA_BACKUP_MIRROR:-/mnt/myra-backups}"
REMOTE_HOST="${MYRA_BACKUP_REMOTE_HOST:-}"
REMOTE_DIR="${MYRA_BACKUP_REMOTE_DIR:-myra-backups}"
REMOTE_TARGET="${REMOTE_HOST}:${REMOTE_DIR%/}/"
SSH_KEY="${MYRA_BACKUP_SSH_KEY:-$HOME/.ssh/id_ed25519}"
LLM_ENV="${MYRA_LLM_ENV_FILE:-/etc/llama-server.env}"
LLM_PRESET="${MYRA_LLM_PRESET:-$HOME/llm/models.ini}"
LLM_UNIT="${MYRA_LLM_UNIT_FILE:-/etc/systemd/system/llama-server.service}"


DB_ORANKENT_DB=6      # orankenti teljes DB dump
DB_ORANKENT_USER=6    # orankenti felhasznaloi dump
NAPI_KONFIG=7         # napi konfig-tarball
NAPI_DB=7             # napi DB masolat
FRONTEND_MEGTART=3    # napi frontend build

STAMP=$(date +%Y%m%d-%H%M)
TODAY=$(date +%Y%m%d)

mkdir -p "$LOCAL/orankent" "$LOCAL/napi"
chmod 700 "$LOCAL"
exec 9>"$LOCAL/.backup.lock"
flock -n 9 || { echo "HIBA: masik mentes mar fut" >&2; exit 1; }


DB_KONTENER="${MYRA_DB_KONTENER:-myra-db}"
WATCH="$SRC/ops/myra-watch.py"

db_env() {
  docker inspect "$DB_KONTENER" --format '{{range .Config.Env}}{{println .}}{{end}}' \
    | sed -n "s/^$1=//p" | head -n1
}
PGU="$(db_env POSTGRES_USER)"
PGD="$(db_env POSTGRES_DB)"
PGU="${PGU:-postgres}"
PGD="${PGD:-$PGU}"

FILELIST=""
PARTIAL=""
STAGE=""
ablak_zar() { python3 "$WATCH" --mentes 0 >/dev/null 2>&1 || true; }
cleanup() {
  ablak_zar
  [ -z "$PARTIAL" ] || rm -f -- "$PARTIAL"
  [ -z "$FILELIST" ] || rm -f -- "$FILELIST"
  [ -z "$STAGE" ] || rm -rf -- "$STAGE"
}
python3 "$WATCH" --mentes 15 >/dev/null
trap cleanup EXIT

archive_ready() {
  [ -s "$1" ] && gzip -t "$1" 2>/dev/null
}

archive_tar() {
  local cel="$1"; shift
  PARTIAL="$cel.partial"
  if ! tar -czf "$PARTIAL" "$@"; then
    echo "HIBA: sikertelen archivum: $cel" >&2
    return 1
  fi
  gzip -t "$PARTIAL"
  mv -- "$PARTIAL" "$cel"
  PARTIAL=""
}

dump() {  # $1=celfajl, tovabbi argumentumok a pg_dump-nak
  local cel="$1"; shift
  PARTIAL="$cel.partial"
  docker exec "$DB_KONTENER" pg_dump -U "$PGU" -d "$PGD" -n public --no-owner \
    --no-privileges --clean --if-exists "$@" | gzip > "$cel.partial"
  gzip -t "$cel.partial"
  mv "$cel.partial" "$cel"
  PARTIAL=""
}

DUMP="$LOCAL/orankent/db-$STAMP.sql.gz"
dump "$DUMP"

if [ ! -s "$DUMP" ] || [ "$(stat -c%s "$DUMP")" -lt 1000 ]; then
  rm -f "$DUMP"
  echo "HIBA: a pg_dump ures vagy csonka, a mentes kimaradt"
  exit 1
fi


USERDUMP="$LOCAL/orankent/userdata-$STAMP.sql.gz"
dump "$USERDUMP" --exclude-table-data=public.knowledge_chunks
if [ ! -s "$USERDUMP" ] || [ "$(stat -c%s "$USERDUMP")" -lt 1000 ]; then
  rm -f "$USERDUMP"
  echo "FIGYELEM: a felhasznaloi mentes ures vagy csonka, kimaradt"
fi
ablak_zar


if ! archive_ready "$LOCAL/napi/konfig-$TODAY.tar.gz"; then


  STAGE=$(mktemp -d "$LOCAL/.stage-$TODAY.XXXXXX")
  mkdir -p "$STAGE/konfig"
  for f in /etc/caddy/Caddyfile /etc/fail2ban/filter.d /etc/fail2ban/jail.d \
           /etc/systemd/system/myra-watch.service /etc/systemd/system/myra-backup.service \
           /etc/systemd/system/myra-backup.timer /etc/myra/ops.env \
           "$LLM_ENV" "$LLM_PRESET" "$LLM_UNIT"; do
    [ -e "$f" ] || continue
    mkdir -p "$STAGE/konfig$(dirname "$f")"
    cp -r -- "$f" "$STAGE/konfig$f"
  done
  {
    echo "# WireGuard nyilvantartas (privat kulcsok szandekosan nincsenek benne)"
    wg show 2>/dev/null || echo "wg show nem elerheto"
    echo "# Publikus kulcsok:"
    cat /etc/wireguard/*.pub 2>/dev/null || true
  } > "$STAGE/konfig/wireguard-allapot.txt"
  archive_tar "$LOCAL/napi/konfig-$TODAY.tar.gz" -C "$STAGE" konfig
  rm -rf -- "$STAGE"
  STAGE=""
fi

if ! archive_ready "$LOCAL/napi/myra-$TODAY.tar.gz"; then
  FILELIST=$(mktemp "$LOCAL/.backup-files.XXXXXX")
  (
    cd "$SRC"
    {
      printf '%s\0' .env docker-compose.yml docker-compose.override.yml
      find backend ops -path backend/data -prune -o \
        -type d \( -name __pycache__ -o -name .venv -o -name venv -o -name .pytest_cache -o -name .ruff_cache -o -name node_modules \) -prune -o -type f -print0
      if [ -d backend/data/kb_pdfs ]; then find backend/data/kb_pdfs -type f -print0; fi
    }
  ) > "$FILELIST"
  archive_tar "$LOCAL/napi/myra-$TODAY.tar.gz" -C "$SRC" --null -T "$FILELIST"
  rm -f -- "$FILELIST"
  FILELIST=""
fi
if ! archive_ready "$LOCAL/napi/db-$TODAY.sql.gz"; then
  PARTIAL="$LOCAL/napi/db-$TODAY.sql.gz.partial"
  cp -- "$DUMP" "$PARTIAL"
  gzip -t "$PARTIAL"
  mv -- "$PARTIAL" "$LOCAL/napi/db-$TODAY.sql.gz"
  PARTIAL=""
fi


if [ -d "$FRONTEND" ] && ! archive_ready "$LOCAL/napi/frontend-$TODAY.tar.gz"; then
  archive_tar "$LOCAL/napi/frontend-$TODAY.tar.gz" -C "$FRONTEND" .
fi


torles_darabszam() {  # $1=mappa $2=minta $3=megtartott darab
  ls -1t "$1"/$2 2>/dev/null | tail -n +$(( $3 + 1 )) | while read -r f; do rm -f "$f"; done || true
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


if [ -n "$REMOTE_HOST" ]; then
  ssh -i "$SSH_KEY" -o BatchMode=yes -o ConnectTimeout=8 "$REMOTE_HOST" true
  rsync -a --delete -e "ssh -i $SSH_KEY -o BatchMode=yes" "$LOCAL/" "$REMOTE_TARGET"
  echo "off-host backup target updated"
else
  echo "FIGYELEM: nincs beallitva off-host backup cel"
fi

echo "mentes kesz: $DUMP ($(du -h "$DUMP" | cut -f1)), helyben: $(du -sh "$LOCAL" | cut -f1), darabok: $(ls -1 "$LOCAL/orankent" | wc -l) orankenti + $(ls -1 "$LOCAL/napi" | wc -l) napi"
