#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/wuyongnaren/Documents/印度占星"

FILES=(
  "AGENTS.md"
  "SKILL.md"
  "references/technique_registry.json"
  "references/quick-reference-guide.md"
  "references/strict-workflow-router.md"
  "skills/jyotish-engine-modules/SKILL.md"
  "skills/jyotish-full-reading-integration/SKILL.md"
)

DRY_RUN="${1:-}"

echo "Skill truth whitelist sync set:"
for file in "${FILES[@]}"; do
  echo "  - $file"
done

echo
echo "Diff vs origin/main:"
git -C "$ROOT" diff --stat origin/main -- "${FILES[@]}"

if [[ "$DRY_RUN" == "--dry-run" ]]; then
  echo
  echo "Dry run only. No files copied or pushed."
  exit 0
fi

echo
echo "This script is audit-only by default."
echo "Use it to inspect the exact whitelist before any manual git add/commit/push."
