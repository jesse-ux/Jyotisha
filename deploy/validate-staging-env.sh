#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${1:-.env.staging}"

if [ ! -f "$ENV_FILE" ]; then
  echo "staging environment file is missing: $ENV_FILE" >&2
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

echo "staging environment selectors: valid"
