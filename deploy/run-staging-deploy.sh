#!/usr/bin/env bash
set -euo pipefail
set +x

required=(
  INCOMING_PATH DEPLOY_PATH API_IMAGE WEB_IMAGE DEPLOY_SHA
  EXPECTED_PREVIOUS_SHA ALLOW_ROLLBACK DOCKER_CONFIG STAGING_URL
)
for key in "${required[@]}"; do
  if [ -z "${!key:-}" ]; then
    echo "required staging deployment input is missing: $key" >&2
    exit 1
  fi
done

sha_pattern='^[0-9a-f]{40}$'
digest_pattern='^ghcr\.io/jesse-ux/jyotisha-(api|web)@sha256:[0-9a-f]{64}$'
image_id_pattern='^sha256:[0-9a-f]{64}$'
if [[ ! "$DEPLOY_SHA" =~ $sha_pattern ]] ||
  [[ ! "$API_IMAGE" =~ $digest_pattern ]] ||
  [[ ! "$WEB_IMAGE" =~ $digest_pattern ]]; then
  echo "unsafe staging image identity" >&2
  exit 1
fi
if [ "$ALLOW_ROLLBACK" != "true" ] && [ "$ALLOW_ROLLBACK" != "false" ]; then
  echo "invalid rollback authorization" >&2
  exit 1
fi
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
if [ "$current_sha" != "not-deployed" ] && [[ ! "$current_sha" =~ $sha_pattern ]]; then
  echo "invalid deployed staging revision state" >&2
  exit 1
fi
if [ "$current_sha" != "$EXPECTED_PREVIOUS_SHA" ]; then
  echo "staging revision changed while this deployment was waiting" >&2
  exit 1
fi
if [ "$ALLOW_ROLLBACK" = "false" ] &&
  [ "$current_sha" != "not-deployed" ] &&
  [ "$current_sha" != "$DEPLOY_SHA" ] &&
  [ "${FORWARD_REVISION_VERIFIED:-false}" != "true" ]; then
  echo "forward staging revision was not verified" >&2
  exit 1
fi

container_id() {
  docker ps -aq \
    --filter 'label=com.docker.compose.project=jyotisha-staging' \
    --filter "label=com.docker.compose.service=$1" | head -n 1
}

repo_digest_for_container() {
  local service="$1"
  local repository="$2"
  local id image_id
  id="$(container_id "$service")"
  [ -n "$id" ] || return 0
  image_id="$(docker inspect --format '{{.Image}}' "$id")"
  docker image inspect --format '{{range .RepoDigests}}{{println .}}{{end}}' "$image_id" |
    awk -v prefix="$repository@sha256:" 'index($0, prefix) == 1 { print; exit }'
}

previous_api_image="$(repo_digest_for_container api ghcr.io/jesse-ux/jyotisha-api)"
previous_web_image="$(repo_digest_for_container web ghcr.io/jesse-ux/jyotisha-web)"
previous_api_id=""
previous_web_id=""
if [ -n "$(container_id api)" ]; then
  previous_api_id="$(docker inspect --format '{{.Image}}' "$(container_id api)")"
fi
if [ -n "$(container_id web)" ]; then
  previous_web_id="$(docker inspect --format '{{.Image}}' "$(container_id web)")"
fi

rollback_image() {
  local digest_ref="$1"
  local image_id="$2"
  if [[ "$digest_ref" =~ $digest_pattern ]]; then
    printf '%s' "$digest_ref"
  elif [[ "$image_id" =~ $image_id_pattern ]]; then
    printf '%s' "$image_id"
  fi
}

previous_api_target="$(rollback_image "$previous_api_image" "$previous_api_id")"
previous_web_target="$(rollback_image "$previous_web_image" "$previous_web_id")"

bash "$INCOMING_PATH/deploy/sync-staging-tree.sh" \
  "$INCOMING_PATH" "$DEPLOY_PATH"

cd "$DEPLOY_PATH"
bash deploy/validate-staging-env.sh \
  .env.staging staging.jyotisha.chat deploy/Caddyfile.staging
bash deploy/validate-staging-database-env.sh .env.staging.database

compose=(
  docker compose -p jyotisha-staging --env-file .env.staging
  -f deploy/docker-compose.server.yml -f deploy/docker-compose.postgres.yml
  -f deploy/docker-compose.staging.yml
)
export APP_ENV_FILE='../.env.staging'
export DATABASE_ENV_FILE='../.env.staging.database'
export CADDYFILE_PATH='./Caddyfile.staging'
export SITE_ADDRESS='https://staging.jyotisha.chat'
export ADMIN_SITE_ADDRESS='https://admin.staging.jyotisha.chat'
export GITHUB_SHA="$DEPLOY_SHA"

"${compose[@]}" config --quiet
"${compose[@]}" pull api web
"${compose[@]}" up -d --no-build --pull never --wait postgres

set +e
"${compose[@]}" --profile migration-check run --rm migration-checker
check_status=$?
set -e
if [ "$check_status" -eq 3 ]; then
  echo "pending migrations: run Migrate Staging Database for $DEPLOY_SHA" >&2
  exit 3
fi
if [ "$check_status" -ne 0 ]; then
  echo "staging migration check failed safely" >&2
  exit "$check_status"
fi

switched=false
rollback() {
  local status=$?
  if [ "$switched" = "true" ] &&
    [ -n "$previous_api_target" ] &&
    [ -n "$previous_web_target" ] &&
    [[ "$current_sha" =~ $sha_pattern ]]; then
    echo "staging verification failed; restoring prior application images" >&2
    API_IMAGE="$previous_api_target" WEB_IMAGE="$previous_web_target" \
      GITHUB_SHA="$current_sha" \
      "${compose[@]}" up -d --no-build --remove-orphans api web caddy || true
  fi
  exit "$status"
}
trap rollback ERR

switched=true
"${compose[@]}" up -d --no-build --remove-orphans

verify_container_image() {
  local service="$1"
  local expected_ref="$2"
  local id expected_id running_id repo_digests
  id="$(container_id "$service")"
  [ -n "$id" ]
  expected_id="$(docker image inspect --format '{{.Id}}' "$expected_ref")"
  running_id="$(docker inspect --format '{{.Image}}' "$id")"
  [ "$running_id" = "$expected_id" ]
  repo_digests="$(docker image inspect --format '{{range .RepoDigests}}{{println .}}{{end}}' "$expected_id")"
  grep -Fqx "$expected_ref" <<<"$repo_digests"
}
verify_container_image api "$API_IMAGE"
verify_container_image web "$WEB_IMAGE"

"${compose[@]}" exec -T \
  -e EXPECTED_SHA="$DEPLOY_SHA" -e STAGING_URL="$STAGING_URL" \
  -e STAGING_ADMIN_URL="https://admin.staging.jyotisha.chat" \
  web node --input-type=module <<'NODE'
const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
let login;
for (let attempt = 0; attempt < 12; attempt += 1) {
  try {
    login = await fetch(`${process.env.STAGING_URL}/login`);
    if (login.ok) break;
  } catch {}
  await delay(5_000);
}
if (!login?.ok) process.exit(1);
const adminLogin = await fetch(`${process.env.STAGING_ADMIN_URL}/login`);
if (!adminLogin.ok) process.exit(1);
const adminRoot = await fetch(process.env.STAGING_ADMIN_URL, { redirect: "manual" });
if (
  adminRoot.status !== 302 ||
  adminRoot.headers.get("location") !== "/admin/codes"
) process.exit(1);
const adminSession = await fetch(`${process.env.STAGING_ADMIN_URL}/api/auth/get-session`);
if (!adminSession.ok) process.exit(1);
const account = await fetch(`${process.env.STAGING_URL}/api/account`);
if (account.status !== 401) process.exit(1);
const publicHealth = await fetch(`${process.env.STAGING_URL}/api/health`);
const publicBody = await publicHealth.json();
if (!publicHealth.ok || publicBody.deployment?.gitCommit !== process.env.EXPECTED_SHA) {
  process.exit(1);
}
const privateHealth = await fetch("http://api:5200/api/health");
const privateBody = await privateHealth.json();
if (!privateHealth.ok || privateBody.status !== "ok" || privateBody.swisseph_available !== true) {
  process.exit(1);
}
NODE

revision_file="$state_directory/deployed-revision.tmp.$$"
printf '%s\n' "$DEPLOY_SHA" >"$revision_file"
chmod 600 "$revision_file"
mv -f "$revision_file" "$state_directory/deployed-revision"
trap - ERR

printf 'previous_sha=%s\nprevious_api_image=%s\nprevious_api_id=%s\n' \
  "$current_sha" "${previous_api_image:-not-deployed}" "${previous_api_id:-not-deployed}"
printf 'previous_web_image=%s\nprevious_web_id=%s\nverified_sha=%s\n' \
  "${previous_web_image:-not-deployed}" "${previous_web_id:-not-deployed}" "$DEPLOY_SHA"
