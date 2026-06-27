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

echo "About to stage only these skill-truth files:"
for file in "${FILES[@]}"; do
  echo "  - $file"
done

echo
echo "Diff vs origin/main:"
git -C "$ROOT" diff --stat origin/main -- "${FILES[@]}"

echo
git -C "$ROOT" add -- "${FILES[@]}"
echo "Staged whitelist files only."

echo
echo "Current staged diff summary:"
git -C "$ROOT" diff --cached --stat -- "${FILES[@]}"
