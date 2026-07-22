#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${1:-.env.staging}"

if [ ! -f "$ENV_FILE" ]; then
  echo "staging environment file is missing: $ENV_FILE" >&2
  exit 1
fi

if [ -L "$ENV_FILE" ]; then
  echo "staging environment file must not be a symlink" >&2
  exit 1
fi

if MODE="$(stat -c '%a' "$ENV_FILE" 2>/dev/null)"; then
  :
else
  MODE="$(stat -f '%Lp' "$ENV_FILE")"
fi

if [ "$MODE" != "600" ]; then
  echo "staging environment file must have mode 0600" >&2
  exit 1
fi

require_selector() {
  local key="$1"
  local expected="$2"
  local count
  local definition_pattern

  definition_pattern="^[[:space:]]*(export[[:space:]]+)?${key}([[:space:]]*=|[[:space:]]*$)"
  count="$(grep -Ec "$definition_pattern" "$ENV_FILE" || true)"
  if [ "$count" -ne 1 ] || ! grep -Fqx "${key}=${expected}" "$ENV_FILE"; then
    echo "invalid staging selector: $key" >&2
    exit 1
  fi
}

require_selector APP_ENV_FILE ../.env.staging
require_selector CADDYFILE_PATH ./Caddyfile.staging
require_selector SITE_ADDRESS https://staging.jyotisha.chat
require_selector ADMIN_SITE_ADDRESS https://admin.staging.jyotisha.chat
require_selector AUTH_PROVIDER supabase
require_selector SELF_HOSTED_IDENTITY_ENABLED true
require_selector AUTH_USER_ORIGIN https://staging.jyotisha.chat
require_selector AUTH_ADMIN_ORIGIN https://admin.staging.jyotisha.chat

require_literal() {
  local key="$1"
  local minimum_length="$2"
  local count value
  count="$(grep -Ec "^${key}=" "$ENV_FILE" || true)"
  if [ "$count" -ne 1 ]; then
    echo "invalid staging identity setting: $key" >&2
    exit 1
  fi
  value="$(grep -E "^${key}=" "$ENV_FILE")"
  value="${value#*=}"
  if [ "${#value}" -lt "$minimum_length" ] ||
    [[ "$value" == *'$'* || "$value" == *'"'* || "$value" == *"'"* ]]; then
    echo "invalid staging identity setting: $key" >&2
    exit 1
  fi
  LITERAL_VALUE="$value"
}

require_literal IDENTITY_DATABASE_URL 50
identity_database_url="$LITERAL_VALUE"
if ! [[ "$identity_database_url" =~ ^postgresql://identity_runtime:([A-Za-z0-9._~-]|%[0-9A-Fa-f]{2})+@postgres:5432/jyotisha$ ]]; then
  echo "invalid staging identity setting: IDENTITY_DATABASE_URL" >&2
  exit 1
fi

require_literal BETTER_AUTH_USER_SECRET 32
user_secret="$LITERAL_VALUE"
require_literal BETTER_AUTH_ADMIN_SECRET 32
admin_secret="$LITERAL_VALUE"
if [ "$user_secret" = "$admin_secret" ]; then
  echo "staging identity secrets must be different" >&2
  exit 1
fi
require_literal RESEND_API_KEY 10
require_literal RESEND_FROM_EMAIL 5
if [[ "$LITERAL_VALUE" != *@* ]]; then
  echo "invalid staging identity setting: RESEND_FROM_EMAIL" >&2
  exit 1
fi

echo "staging environment selectors: valid"
