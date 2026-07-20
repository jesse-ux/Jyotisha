#!/usr/bin/env bash
set -euo pipefail
set +x

if [ "$#" -ne 2 ]; then
  echo "usage: backup-staging-postgres.sh DATABASE_ENV_FILE BACKUP_DIRECTORY" >&2
  exit 1
fi

SCRIPT_DIRECTORY="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPOSITORY_ROOT="$(cd "$SCRIPT_DIRECTORY/.." && pwd)"
VALIDATOR="$SCRIPT_DIRECTORY/validate-staging-database-env.sh"

DATABASE_ENV_FILE="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
export DATABASE_ENV_FILE
BACKUP_DIRECTORY_INPUT="$2"

if [ "$BACKUP_DIRECTORY_INPUT" = "/" ]; then
  echo "backup directory must not be the filesystem root" >&2
  exit 1
fi

"$VALIDATOR" "$DATABASE_ENV_FILE" >/dev/null

read_environment_value() {
  local key="$1"
  local value

  value="$(sed -n -E "s/^[[:space:]]*(export[[:space:]]+)?${key}[[:space:]]*=[[:space:]]*(.*)$/\\2/p" "$DATABASE_ENV_FILE")"
  case "$value" in
    \"*\") value="${value#\"}"; value="${value%\"}" ;;
    \'*\') value="${value#\'}"; value="${value%\'}" ;;
  esac
  printf '%s' "$value"
}

POSTGRES_DB="$(read_environment_value POSTGRES_DB)"
POSTGRES_USER="$(read_environment_value POSTGRES_USER)"
STAGING_BACKUP_ENCRYPTION_KEY="$(read_environment_value STAGING_BACKUP_ENCRYPTION_KEY)"
export STAGING_BACKUP_ENCRYPTION_KEY

mkdir -p "$BACKUP_DIRECTORY_INPUT"
chmod 0700 "$BACKUP_DIRECTORY_INPUT"
BACKUP_DIRECTORY="$(cd "$BACKUP_DIRECTORY_INPUT" && pwd -P)"

DISK_USAGE="$(df -Pk "$BACKUP_DIRECTORY" | awk 'NR == 2 { gsub(/%/, "", $5); print $5 }')"
if ! [[ "$DISK_USAGE" =~ ^[0-9]+$ ]] || [ "$DISK_USAGE" -ge 70 ]; then
  echo "backup directory disk usage must be below 70 percent" >&2
  exit 1
fi

BACKUP_TIMESTAMP="${BACKUP_TIMESTAMP:-$(date -u +%Y%m%dT%H%M%SZ)}"
if ! [[ "$BACKUP_TIMESTAMP" =~ ^[0-9]{8}T[0-9]{6}Z$ ]]; then
  echo "backup timestamp must use YYYYMMDDTHHMMSSZ" >&2
  exit 1
fi

FILE_NAME="jyotisha-staging-${BACKUP_TIMESTAMP}.dump.enc"
FINAL_FILE="$BACKUP_DIRECTORY/$FILE_NAME"
PARTIAL_FILE="$BACKUP_DIRECTORY/.${FILE_NAME}.$$.partial"

if [ -e "$FINAL_FILE" ] || [ -L "$FINAL_FILE" ]; then
  echo "backup destination already exists" >&2
  exit 1
fi

cleanup_partial() {
  local status="$?"
  if [ -n "${PARTIAL_FILE:-}" ] && [ -e "$PARTIAL_FILE" ]; then
    rm -f "$PARTIAL_FILE"
  fi
  exit "$status"
}
trap cleanup_partial EXIT HUP INT TERM

umask 077
: > "$PARTIAL_FILE"
chmod 0600 "$PARTIAL_FILE"

cd "$REPOSITORY_ROOT"
docker compose -p "${COMPOSE_PROJECT_NAME:-jyotisha-staging}" \
  -f deploy/docker-compose.postgres.yml exec -T postgres \
  pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom --no-owner |
openssl enc -aes-256-cbc -salt -pbkdf2 \
  -pass env:STAGING_BACKUP_ENCRYPTION_KEY > "$PARTIAL_FILE"

chmod 0600 "$PARTIAL_FILE"
mv "$PARTIAL_FILE" "$FINAL_FILE"
PARTIAL_FILE=""

completed=()
while IFS= read -r path; do
  name="${path##*/}"
  if [[ "$name" =~ ^jyotisha-staging-[0-9]{8}T[0-9]{6}Z\.dump\.enc$ ]]; then
    completed+=("$name")
  fi
done < <(find "$BACKUP_DIRECTORY" -maxdepth 1 -type f -name 'jyotisha-staging-*.dump.enc' -print | LC_ALL=C sort)

if [ "${#completed[@]}" -gt 3 ]; then
  for ((index = 0; index < ${#completed[@]} - 3; index += 1)); do
    rm -f "$BACKUP_DIRECTORY/${completed[$index]}"
  done
fi

printf 'path=%s count=%s\n' "$FINAL_FILE" "$(( ${#completed[@]} > 3 ? 3 : ${#completed[@]} ))"
