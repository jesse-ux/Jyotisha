# Skill Single Source of Truth (2026-06-26)

## Decision

The only authoritative Jyotish skill source is:

- `/Users/wuyongnaren/Documents/印度占星`

This repo is the single source of truth for:

- `SKILL.md`
- `references/technique_registry.json`
- `references/strict-workflow-router.md`
- `skills/jyotish-engine-modules/SKILL.md`
- `skills/jyotish-full-reading-integration/SKILL.md`

## Distribution Targets

The following locations are distribution copies only, not development sources:

- `/Users/wuyongnaren/.workbuddy/skills/jyotish-vedic-astrology`
- any other historical `jyotish-vedic-astrology` copies under recovery/archive folders

They must only be updated from the main repo.
They must never overwrite the main repo.

## Sync Whitelist

When syncing the installed skill copy, only sync:

- `SKILL.md`
- `references/technique_registry.json`
- `references/strict-workflow-router.md`
- `skills/jyotish-engine-modules/SKILL.md`
- `skills/jyotish-full-reading-integration/SKILL.md`

## Do Not Sync

Do not sync these into the installed skill copy by default:

- `scripts/*.py`
- `tests/*`
- `jyotish-app/*`
- `node_modules/`
- `dist/`
- runtime reports, smoke outputs, caches, logs

## Operational Rule

1. Edit only the main repo.
2. Commit and push the main repo.
3. If the installed WorkBuddy skill needs updating, sync only the whitelist files from the main repo.
4. Historical copies remain archive/reference only.

## Current Action Taken

On 2026-06-26, the whitelist files from the main repo were synced into:

- `/Users/wuyongnaren/.workbuddy/skills/jyotish-vedic-astrology`

This makes the installed skill copy match the main repo for skill-definition files, while keeping app/backend code in the repo only.
