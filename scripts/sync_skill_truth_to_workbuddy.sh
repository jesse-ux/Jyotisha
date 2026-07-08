#!/usr/bin/env bash
set -euo pipefail

ROOT="<repo>"
WB="<home>/.workbuddy/skills/jyotish-vedic-astrology"

mkdir -p "$WB/references"
mkdir -p "$WB/skills/jyotish-engine-modules"
mkdir -p "$WB/skills/jyotish-full-reading-integration"

cp "$ROOT/AGENTS.md" "$WB/AGENTS.md"
cp "$ROOT/SKILL.md" "$WB/SKILL.md"
cp "$ROOT/references/technique_registry.json" "$WB/references/technique_registry.json"
cp "$ROOT/references/quick-reference-guide.md" "$WB/references/quick-reference-guide.md"
cp "$ROOT/references/strict-workflow-router.md" "$WB/references/strict-workflow-router.md"
cp "$ROOT/skills/jyotish-engine-modules/SKILL.md" "$WB/skills/jyotish-engine-modules/SKILL.md"
cp "$ROOT/skills/jyotish-full-reading-integration/SKILL.md" "$WB/skills/jyotish-full-reading-integration/SKILL.md"
cp "$ROOT/mcp_server.py" "$WB/mcp_server.py"

echo "synced skill truth files to workbuddy"
