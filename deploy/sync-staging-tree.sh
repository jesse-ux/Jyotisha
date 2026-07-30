#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 2 ] || [ ! -d "$1" ] || [ ! -d "$2" ]; then
  echo "usage: sync-staging-tree.sh SOURCE_DIRECTORY DESTINATION_DIRECTORY" >&2
  exit 1
fi

destination_deploy="$2/deploy"
if [ -d "$destination_deploy" ] && [ ! -w "$destination_deploy" ]; then
  docker run --rm --network none --read-only --user 0:0 \
    --cap-drop ALL --cap-add CHOWN --security-opt no-new-privileges \
    -v "$destination_deploy:/destination" postgres:17-alpine \
    chown -R "$(id -u):$(id -g)" /destination
fi

rsync -az --delete --no-owner --no-group \
  --exclude='/.git/' \
  --exclude='/.env*' \
  --exclude='/.docker/' \
  --exclude='/backups/' \
  --exclude='/.state/' \
  --exclude='/.incoming/' \
  --exclude='/frontend/node_modules/' \
  --exclude='/frontend/.next/' \
  "$1/" "$2/"
