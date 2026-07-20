#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 2 ] || [ ! -d "$1" ] || [ ! -d "$2" ]; then
  echo "usage: sync-staging-tree.sh SOURCE_DIRECTORY DESTINATION_DIRECTORY" >&2
  exit 1
fi

rsync -az --delete \
  --exclude='/.git/' \
  --exclude='/.env*' \
  --exclude='/backups/' \
  --exclude='/.state/' \
  --exclude='/.incoming/' \
  --exclude='/frontend/node_modules/' \
  --exclude='/frontend/.next/' \
  "$1/" "$2/"
