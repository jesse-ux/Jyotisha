#!/usr/bin/env bash
set -euo pipefail
set +x

required=(
  INCOMING_PATH DEPLOY_PATH WEB_IMAGE DEPLOY_SHA EXPECTED_PREVIOUS_SHA
  DOCKER_CONFIG
)
for key in "${required[@]}"; do
  if [ -z "${!key:-}" ]; then
    echo "required staging migration input is missing: $key" >&2
    exit 1
  fi
done

[[ "$DEPLOY_SHA" =~ ^[0-9a-f]{40}$ ]] || {
  echo "unsafe staging migration revision" >&2
  exit 1
}
[[ "$WEB_IMAGE" =~ ^ghcr\.io/jesse-ux/jyotisha-web@sha256:[0-9a-f]{64}$ ]] || {
  echo "unsafe staging migration image" >&2
  exit 1
}
case "$INCOMING_PATH" in
  "$DEPLOY_PATH"/.incoming/*) ;;
  *) echo "unsafe incoming staging path" >&2; exit 1 ;;
esac

state_directory="$DEPLOY_PATH/.state"
install -d -m 700 "$state_directory"
exec 9>"$state_directory/mutation.lock"
flock -n 9 || {
  echo "another staging mutation holds the host lock" >&2
  exit 75
}

current_sha="not-deployed"
if [ -f "$state_directory/deployed-revision" ]; then
  current_sha="$(<"$state_directory/deployed-revision")"
else
  existing_web="$(docker ps -aq \
    --filter 'label=com.docker.compose.project=jyotisha-staging' \
    --filter 'label=com.docker.compose.service=web' | head -n 1)"
  if [ -n "$existing_web" ]; then
    discovered_sha="$(docker inspect --format '{{range .Config.Env}}{{println .}}{{end}}' \
      "$existing_web" | sed -n 's/^GITHUB_SHA=//p' | head -n 1)"
    if [ -n "$discovered_sha" ]; then current_sha="$discovered_sha"; fi
  fi
fi
if [ "$current_sha" != "not-deployed" ] && [[ ! "$current_sha" =~ ^[0-9a-f]{40}$ ]]; then
  echo "invalid deployed staging revision state" >&2
  exit 1
fi
[ "$current_sha" = "$EXPECTED_PREVIOUS_SHA" ] || {
  echo "staging revision changed while this migration was waiting" >&2
  exit 1
}
[ "$current_sha" = "not-deployed" ] ||
  [ "$current_sha" = "$DEPLOY_SHA" ] ||
  [ "${FORWARD_REVISION_VERIFIED:-false}" = "true" ] || {
    echo "forward staging revision was not verified" >&2
    exit 1
  }

bash "$INCOMING_PATH/deploy/sync-staging-tree.sh" \
  "$INCOMING_PATH" "$DEPLOY_PATH"

cd "$DEPLOY_PATH"
bash deploy/validate-staging-env.sh \
  .env.staging staging.jyotisha.chat deploy/Caddyfile.staging
bash deploy/validate-staging-database-env.sh .env.staging.database

export DATABASE_ENV_FILE='../.env.staging.database'
compose=(docker compose -p jyotisha-staging -f deploy/docker-compose.postgres.yml)
docker pull "$WEB_IMAGE"
"${compose[@]}" up -d --wait postgres
"${compose[@]}" --profile migration run --rm migrator
"${compose[@]}" exec -T postgres psql -U postgres -d jyotisha -Atc \
  'select filename from migration.schema_migrations order by filename'
