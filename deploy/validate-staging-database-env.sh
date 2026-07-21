#!/usr/bin/env bash
set -euo pipefail
set +x

ENV_FILE="${1:-.env.staging.database}"

if [ ! -e "$ENV_FILE" ]; then
  echo "staging database environment file is missing" >&2
  exit 1
fi

if [ -L "$ENV_FILE" ]; then
  echo "staging database environment file must not be a symlink" >&2
  exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
  echo "staging database environment path must be a regular file" >&2
  exit 1
fi

if MODE="$(stat -c '%a' "$ENV_FILE" 2>/dev/null)"; then
  :
else
  MODE="$(stat -f '%Lp' "$ENV_FILE")"
fi

if [ "$MODE" != "600" ]; then
  echo "staging database environment file must have mode 0600" >&2
  exit 1
fi

if OWNER="$(stat -c '%u' "$ENV_FILE" 2>/dev/null)"; then
  :
else
  OWNER="$(stat -f '%u' "$ENV_FILE")"
fi

if [ "$OWNER" != "$(id -u)" ]; then
  echo "staging database environment file must be owned by the current user" >&2
  exit 1
fi

definition_count() {
  local key="$1"
  grep -Ec "^[[:space:]]*(export[[:space:]]+)?${key}([[:space:]]*=|[[:space:]]*$)" "$ENV_FILE" || true
}

environment_value() {
  local key="$1"
  sed -n -E "s/^[[:space:]]*(export[[:space:]]+)?${key}[[:space:]]*=[[:space:]]*(.*)$/\\2/p" "$ENV_FILE"
}

is_safe_literal() {
  local value="$1"
  local inner

  # Required values are literal single-line values: use an unquoted token or
  # matching non-empty quotes. Dotenv interpolation, comments, and malformed
  # quoting are rejected rather than evaluated, so generate secrets without $.
  if [ -z "$value" ] || [[ "$value" == *'$'* ]]; then
    return 1
  fi

  case "$value" in
    \"*\")
      inner="${value:1}"
      inner="${inner%?}"
      [ -n "$inner" ] && [[ "$inner" != *'"'* ]]
      ;;
    \'*\')
      inner="${value:1}"
      inner="${inner%?}"
      [ -n "$inner" ] && [[ "$inner" != *"'"* ]]
      ;;
    *\"*|*\'*)
      return 1
      ;;
    *[[:space:]]*|*\#*)
      return 1
      ;;
  esac
}

require_once_non_empty() {
  local key="$1"
  local count
  local value
  count="$(definition_count "$key")"
  value="$(environment_value "$key")"
  if [ "$count" -ne 1 ] || ! is_safe_literal "$value"; then
    echo "required staging database literal is missing, duplicated, or ambiguous: $key" >&2
    exit 1
  fi
}

required=(
  POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD
  SCHEMA_OWNER_PASSWORD IDENTITY_RUNTIME_PASSWORD APP_RUNTIME_PASSWORD
  ADMIN_RUNTIME_PASSWORD MIGRATION_RUNNER_PASSWORD BACKUP_READER_PASSWORD
  STAGING_BACKUP_ENCRYPTION_KEY SCHEMA_DATABASE_URL
)
for key in "${required[@]}"; do
  require_once_non_empty "$key"
done

if [ "$(environment_value POSTGRES_DB)" != "jyotisha" ]; then
  echo "invalid staging database selector: POSTGRES_DB" >&2
  exit 1
fi

if [ "$(environment_value POSTGRES_USER)" != "postgres" ]; then
  echo "invalid staging database selector: POSTGRES_USER" >&2
  exit 1
fi

if ! [[ "$(environment_value SCHEMA_DATABASE_URL)" =~ ^postgresql://schema_owner:([A-Za-z0-9._~-]|%[0-9A-Fa-f]{2})+@postgres:5432/jyotisha$ ]]; then
  echo "invalid staging database selector: SCHEMA_DATABASE_URL" >&2
  exit 1
fi

echo "staging database environment validated"
