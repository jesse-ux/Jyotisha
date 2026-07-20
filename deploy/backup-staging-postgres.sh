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

reject_backup_directory() {
  echo "backup directory must be an absolute path without traversal, aliases, or symlinks" >&2
  exit 1
}

reject_unsafe_backup_directory_ancestor() {
  echo "backup directory ancestor must be owned by the current user or root and not group/world-writable" >&2
  exit 1
}

stat_owner_and_mode() {
  local path="$1"

  if stat -f '%u %Lp' "$path" >/dev/null 2>&1; then
    stat -f '%u %Lp' "$path"
  else
    stat -c '%u %a' "$path"
  fi
}

directory_identity() {
  local path="$1"

  if stat -f '%d:%i' "$path" >/dev/null 2>&1; then
    stat -f '%d:%i' "$path"
  else
    stat -c '%d:%i' "$path"
  fi
}

if [ "$BACKUP_DIRECTORY_INPUT" = "/" ] || [[ "$BACKUP_DIRECTORY_INPUT" != /* ]] || [[ "$BACKUP_DIRECTORY_INPUT" == */ ]] || [[ "$BACKUP_DIRECTORY_INPUT" == *"//"* ]]; then
  reject_backup_directory
fi

IFS='/' read -r -a backup_directory_components <<< "${BACKUP_DIRECTORY_INPUT#/}"
if [ "${#backup_directory_components[@]}" -eq 0 ]; then
  reject_backup_directory
fi

backup_directory_component_path=""
CURRENT_UID="$(id -u)"
for backup_directory_component in "${backup_directory_components[@]}"; do
  if [ -z "$backup_directory_component" ] || [ "$backup_directory_component" = "." ] || [ "$backup_directory_component" = ".." ]; then
    reject_backup_directory
  fi
  backup_directory_component_path="${backup_directory_component_path}/${backup_directory_component}"
  if [ -L "$backup_directory_component_path" ]; then
    reject_backup_directory
  fi
  if [ -e "$backup_directory_component_path" ]; then
    if [ ! -d "$backup_directory_component_path" ]; then
      reject_backup_directory
    fi
    read -r backup_directory_owner backup_directory_mode <<< "$(stat_owner_and_mode "$backup_directory_component_path")"
    if [ "$backup_directory_owner" != "$CURRENT_UID" ] && [ "$backup_directory_owner" != "0" ]; then
      reject_unsafe_backup_directory_ancestor
    fi
    if (( (10#${backup_directory_mode: -2:1} & 2) != 0 || (10#${backup_directory_mode: -1} & 2) != 0 )); then
      reject_unsafe_backup_directory_ancestor
    fi
  fi
done

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
cd -P "$BACKUP_DIRECTORY_INPUT"
BACKUP_DIRECTORY="$(pwd -P)"
if [ "$BACKUP_DIRECTORY" != "$BACKUP_DIRECTORY_INPUT" ] || [ "$BACKUP_DIRECTORY" = "/" ]; then
  reject_backup_directory
fi
BACKUP_DIRECTORY_IDENTITY="$(directory_identity .)"
if [ "$(directory_identity "$BACKUP_DIRECTORY_INPUT")" != "$BACKUP_DIRECTORY_IDENTITY" ]; then
  reject_backup_directory
fi
chmod 0700 .

DISK_USAGE="$(df -Pk . | awk 'NR == 2 { gsub(/%/, "", $5); print $5 }')"
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
FINAL_FILE="$FILE_NAME"
PARTIAL_FILE=".${FILE_NAME}.$$.partial"
LOCK_DIRECTORY=".${FILE_NAME}.lock"
LOCK_ACQUIRED=0

if [ -e "$FINAL_FILE" ] || [ -L "$FINAL_FILE" ]; then
  echo "backup destination already exists" >&2
  exit 1
fi

cleanup_partial() {
  local status="$?"
  if [ -n "${PARTIAL_FILE:-}" ] && [ -e "$PARTIAL_FILE" ]; then
    rm -f "$PARTIAL_FILE"
  fi
  if [ "${LOCK_ACQUIRED:-0}" -eq 1 ] && [ -d "$LOCK_DIRECTORY" ]; then
    rmdir "$LOCK_DIRECTORY" || true
  fi
  exit "$status"
}
trap cleanup_partial EXIT HUP INT TERM

umask 077
if ! mkdir "$LOCK_DIRECTORY"; then
  echo "backup destination is already being created" >&2
  exit 1
fi
LOCK_ACQUIRED=1
: > "$PARTIAL_FILE"
chmod 0600 "$PARTIAL_FILE"

(
  cd "$REPOSITORY_ROOT"
  docker compose -p "${COMPOSE_PROJECT_NAME:-jyotisha-staging}" \
    -f deploy/docker-compose.postgres.yml exec -T postgres \
    pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom --no-owner
) |
openssl enc -aes-256-cbc -salt -pbkdf2 \
  -pass env:STAGING_BACKUP_ENCRYPTION_KEY > "$PARTIAL_FILE"

chmod 0600 "$PARTIAL_FILE"
if ! ln "$PARTIAL_FILE" "$FINAL_FILE"; then
  echo "backup destination already exists" >&2
  exit 1
fi
rm -f "$PARTIAL_FILE"
PARTIAL_FILE=""

completed=()
if ! completed_paths="$(find . -maxdepth 1 -type f -name 'jyotisha-staging-*.dump.enc' -print | LC_ALL=C sort)"; then
  echo "failed to enumerate completed backups" >&2
  exit 1
fi
while IFS= read -r path; do
  name="${path##*/}"
  if [[ "$name" =~ ^jyotisha-staging-[0-9]{8}T[0-9]{6}Z\.dump\.enc$ ]]; then
    completed+=("$name")
  fi
done <<< "$completed_paths"

if [ "${#completed[@]}" -gt 3 ]; then
  for ((index = 0; index < ${#completed[@]} - 3; index += 1)); do
    rm -f "${completed[$index]}"
  done
fi

printf 'path=%s count=%s\n' "$BACKUP_DIRECTORY/$FINAL_FILE" "$(( ${#completed[@]} > 3 ? 3 : ${#completed[@]} ))"
