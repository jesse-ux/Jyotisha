#!/usr/bin/env bash
set -euo pipefail
set +x

required=(DEPLOY_PATH EXPECTED_DEPLOY_SHA ROLLOUT_AUDIENCE STAGING_URL)
for key in "${required[@]}"; do
  if [ -z "${!key:-}" ]; then
    echo "required staging rollout input is missing: $key" >&2
    exit 1
  fi
done

sha_pattern='^[0-9a-f]{40}$'
uuid_pattern='^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
[[ "$EXPECTED_DEPLOY_SHA" =~ $sha_pattern ]] || {
  echo "invalid expected deployment SHA" >&2
  exit 1
}
case "$ROLLOUT_AUDIENCE" in
  paused|smoke_only|public) ;;
  *) echo "invalid rollout audience" >&2; exit 1 ;;
esac

smoke_user_ids="${SYNTHETIC_SMOKE_USER_IDS:-}"
if [ "$ROLLOUT_AUDIENCE" = "smoke_only" ]; then
  [ -n "$smoke_user_ids" ] || {
    echo "smoke_only requires at least one synthetic user UUID" >&2
    exit 1
  }
  IFS=',' read -ra smoke_users <<<"$smoke_user_ids"
  for user_id in "${smoke_users[@]}"; do
    [[ "$user_id" =~ $uuid_pattern ]] || {
      echo "invalid synthetic smoke user UUID" >&2
      exit 1
    }
  done
else
  [ -z "$smoke_user_ids" ] || {
    echo "synthetic smoke users are only valid for smoke_only" >&2
    exit 1
  }
fi

state_directory="$DEPLOY_PATH/.state"
env_file="$DEPLOY_PATH/.env.staging"
install -d -m 700 "$state_directory"
exec 9>"$state_directory/mutation.lock"
flock -n 9 || {
  echo "another staging mutation holds the host lock" >&2
  exit 75
}

compose_files=(
  -f deploy/docker-compose.server.yml
  -f deploy/docker-compose.postgres.yml
  -f deploy/docker-compose.staging.yml
)

[ -f "$env_file" ] || {
  echo "staging environment file is missing" >&2
  exit 1
}
current_sha="$(<"$state_directory/deployed-revision")"
[ "$current_sha" = "$EXPECTED_DEPLOY_SHA" ] || {
  echo "deployed staging revision does not match the approved rollout SHA" >&2
  exit 1
}

case "$ROLLOUT_AUDIENCE" in
  public)
    creation_enabled=true
    smoke_sha="$EXPECTED_DEPLOY_SHA"
    smoke_user_ids=""
    ;;
  smoke_only)
    creation_enabled=true
    smoke_sha=""
    ;;
  paused)
    creation_enabled=false
    smoke_sha=""
    smoke_user_ids=""
    ;;
esac

backup="$(mktemp "$state_directory/rectification-rollout-backup.XXXXXX")"
temporary="$(mktemp "$DEPLOY_PATH/.env.staging.rollout.XXXXXX")"
declare -a compose=()
cleanup() { rm -f -- "$backup" "$temporary"; }
rollback() {
  local status=$?
  cp -p -- "$backup" "$env_file"
  if [ "${#compose[@]}" -gt 0 ]; then
    "${compose[@]}" up -d --no-build --pull never --force-recreate --no-deps web rectification-v4-worker >/dev/null 2>&1 || true
  fi
  exit "$status"
}
trap cleanup EXIT
cp -p -- "$env_file" "$backup"

awk \
  -v create="$creation_enabled" \
  -v migrations="true" \
  -v smoke_sha="$smoke_sha" \
  -v smoke_users="$smoke_user_ids" '
BEGIN {
  values["RECTIFICATION_V3_CREATE_ENABLED"] = create
  values["RECTIFICATION_V3_MIGRATIONS_READY"] = migrations
  values["RECTIFICATION_V3_SYNTHETIC_SMOKE_SHA"] = smoke_sha
  values["RECTIFICATION_V3_SYNTHETIC_SMOKE_USER_IDS"] = smoke_users
}
{
  split($0, parts, "=")
  key = parts[1]
  if (key in values) {
    if (!(key in written)) print key "=" values[key]
    written[key] = 1
    next
  }
  print
}
END {
  for (key in values) if (!(key in written)) print key "=" values[key]
}
' "$env_file" >"$temporary"
chmod 600 "$temporary"

cd "$DEPLOY_PATH"
bash deploy/validate-staging-env.sh "$temporary" staging.jyotisha.chat deploy/Caddyfile.staging
mv -f -- "$temporary" "$env_file"
trap rollback ERR

web_container="$(docker ps -aq --filter 'label=com.docker.compose.project=jyotisha-staging' --filter 'label=com.docker.compose.service=web' | head -n 1)"
[ -n "$web_container" ] || {
  echo "staging web container is missing" >&2
  false
}
export WEB_IMAGE="$(docker inspect --format '{{.Config.Image}}' "$web_container")"
export APP_ENV_FILE='../.env.staging'
export DATABASE_ENV_FILE='../.env.staging.database'
export CADDYFILE_PATH='./Caddyfile.staging'
export SITE_ADDRESS='https://staging.jyotisha.chat'
export ADMIN_SITE_ADDRESS='https://admin.staging.jyotisha.chat'
export GITHUB_SHA="$EXPECTED_DEPLOY_SHA"
compose=(docker compose -p jyotisha-staging --env-file .env.staging "${compose_files[@]}")

"${compose[@]}" config --quiet
"${compose[@]}" up -d --no-build --pull never --force-recreate --no-deps web rectification-v4-worker

health=""
for _ in $(seq 1 30); do
  health="$(curl --fail --silent --show-error "$STAGING_URL/api/health" 2>/dev/null || true)"
  expected_ready=false
  [ "$ROLLOUT_AUDIENCE" = public ] && expected_ready=true
  if grep -Fq "\"gitCommit\":\"$EXPECTED_DEPLOY_SHA\"" <<<"$health" &&
    grep -Fq "\"creationAudience\":\"$ROLLOUT_AUDIENCE\"" <<<"$health" &&
    grep -Fq "\"readyForNewCases\":$expected_ready" <<<"$health"; then
    trap - ERR
    printf 'rectification rollout audience=%s deployed_sha=%s ready_for_new_cases=%s\n' \
      "$ROLLOUT_AUDIENCE" "$EXPECTED_DEPLOY_SHA" "$([ "$ROLLOUT_AUDIENCE" = public ] && echo true || echo false)"
    exit 0
  fi
  sleep 2
done

echo "staging rollout health verification failed" >&2
false
