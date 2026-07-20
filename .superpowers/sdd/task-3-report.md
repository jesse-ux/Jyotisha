# Task 3 — Encrypted Local Staging Backups

## Scope delivered

- Added `deploy/backup-staging-postgres.sh DATABASE_ENV_FILE BACKUP_DIRECTORY`.
- Validates the private database environment before reading required values without sourcing or executing the env file.
- Refuses backup destinations with disk usage at or above 70%, creates the explicit destination with mode `0700`, writes encrypted custom PostgreSQL dumps with mode `0600`, and keeps only the newest three exact staging dump names.
- Uses a PID-scoped `.partial` file, `pipefail`, an exit cleanup trap, and same-directory hard-link/no-clobber publication so failed dump/encryption pipelines leave no completed partial archive and successful archives are published atomically.
- Emits only final path/count on success; credentials use environment variables and never command-line arguments.

## TDD evidence

RED (before the script existed):

```text
cd frontend && npm run test:db
FAIL database-backup.test.ts: bash: .../deploy/backup-staging-postgres.sh: No such file or directory
```

GREEN focused integration:

```text
./node_modules/.bin/tsx --test --test-concurrency=1 tests/database-backup.test.ts
pass 1, fail 0
```

The integration starts the real fixture, creates four encrypted dumps at deterministic timestamps, verifies the final three names and modes, decrypts an archive with OpenSSL, and runs `pg_restore --list` (falling back to the fixture container when necessary).

## Final verification

```text
bash -n deploy/backup-staging-postgres.sh                 exit 0
cd frontend && npm run test:db                            12 passed, 0 failed
cd frontend && npm test                                   488 passed, 0 failed
cd frontend && npm run lint                               exit 0
git diff --check                                          exit 0
```

## Pre-scan race follow-up (2026-07-21)

- Lexical component validation now completes before ancestor scanning. Once scanning finds the first absent component, it stops constructing deeper absolute pathnames immediately; creation continues only from the already pinned deepest existing directory.
- A deterministic `BASH_ENV` DEBUG-hook regression inserts a symlink after the first missing component is recorded. The script rejects it from the pinned parent and creates no `backup` path under the symlink target. Creation uses `./$component` for test, mkdir, validation, and `cd -P`, so legal names beginning with `-` are handled as names rather than options.

```text
RED:
cd frontend && npm run test:db
FAIL stops absolute pre-scan traversal when a symlink appears after the first missing component
FAIL creates every absent backup path component privately despite a permissive caller umask

GREEN:
bash -n deploy/backup-staging-postgres.sh                exit 0
cd frontend && npm run test:db                            21 passed, 0 failed
cd frontend && npm test                                   497 passed, 0 failed
cd frontend && npm run lint                               exit 0
git diff --check                                          exit 0
```

## Atomic component-creation follow-up (2026-07-20)

- The sticky root-owned exception now applies only to ancestors. An existing requested backup leaf is separately required to be current-user owned, non-symlink, and non-group/world-writable before the script can chmod or write it; direct canonical `/tmp` is rejected without calling `chmod` or changing its mode.
- The script no longer uses `mkdir -p` for backup paths. It pins the deepest validated existing ancestor, creates each missing component with one plain relative `mkdir`, validates it, and `cd -P`s into it before creating the next. If a concurrent actor creates any component first, including a symlink, the script rejects it without descending through it.

```text
RED:
cd frontend && npm run test:db
FAIL rejects a direct canonical sticky shared backup directory before chmod
FAIL fails safely when a racer inserts a symlink during nested backup path creation

GREEN:
bash -n deploy/backup-staging-postgres.sh                exit 0
cd frontend && npm run test:db                            20 passed, 0 failed
cd frontend && npm test                                   496 passed, 0 failed
cd frontend && npm run lint                               exit 0
git diff --check                                          exit 0
```

## Secure directory-creation follow-up (2026-07-20)

- `umask 077` now executes at script startup, before any possible `mkdir`. The script records the first absent component, then re-walks every component after `mkdir -p`; all newly created directories must be current-user owned, non-symlink directories without group/world write permission before `cd -P` pins the target.
- Existing root-owned sticky shared ancestors, including canonical `/tmp`, are allowed; ordinary group/world-writable ancestors remain rejected. The shared-temporary-root tests canonicalize `/tmp` with `realpathSync`, so they prove validation reaches their deliberately nested symlink and `0777` parent instead of stopping at the standard sticky ancestor.

```text
RED:
cd frontend && npm run test:db
FAIL rejects destructive backup directory aliases and symlink components before mutation
FAIL creates every absent backup path component privately despite a permissive caller umask
The prior policy rejected canonical /tmp and only set umask after mkdir.

GREEN:
bash -n deploy/backup-staging-postgres.sh                exit 0
cd frontend && npm run test:db                            18 passed, 0 failed
cd frontend && npm test                                   494 passed, 0 failed
cd frontend && npm run lint                               exit 0
git diff --check                                          exit 0
```

## TOCTOU follow-up (2026-07-20)

- Before `mkdir`/`cd`, the script walks all existing absolute-target ancestors, rejects symlinks, requires current-user-or-root ownership, and rejects group/world-writable modes. The unsafe-parent regression uses `realpathSync` for the macOS temporary root, so its nested symlink and `0777` parent are the components actually reached by validation.
- After creation it enters the directory with `cd -P`, verifies the canonical path and directory identity, and keeps the working directory pinned. Disk check, lock, partial/final publication, inventory, `find`, and rotation all use `.` or relative filenames; success still prints the canonical absolute archive path.

```text
RED:
cd frontend && npm run test:db
FAIL rejects unsafe writable backup parents before creating the target
The old script created the target and then failed only at the disk check, rather than rejecting the unsafe ancestor.

GREEN:
bash -n deploy/backup-staging-postgres.sh                exit 0
cd frontend && npm run test:db                            17 passed, 0 failed
cd frontend && npm test                                   493 passed, 0 failed
cd frontend && npm run lint                               exit 0
git diff --check                                          exit 0
```

## Self-review and caveats

- Reviewed the final diff for secret exposure, output scope, filename filtering, rotation boundaries, portable shell options, and atomic/cleanup behavior; no task-scope finding remained.
- This Mac's actual filesystem usage is at least 70%, which correctly makes the production script refuse a backup. The integration test supplies a controlled `df` executable reporting 10% usage so it can exercise the real Docker/PostgreSQL/OpenSSL/`pg_restore` flow without weakening the production guard.
- The mandatory repository pre-work gate remains host-blocked for its known unrelated reason: system Python 3.9 lacks pytest (and cannot import the project's Python 3.10+ syntax). No Task 3 change touches that gate.

## Follow-up safety hardening (2026-07-20)

Implementation:

- Rejects `/`, relative paths, repeated/trailing separators, `.`/`..` traversal, and every existing symlink component before the script can create, chmod, write, or delete under the requested backup path. After `mkdir -p`, it resolves physically and requires the exact non-root input before chmod.
- Acquires a per-archive directory lock using portable exclusive `mkdir`; publishes with a same-directory hard link (`ln`) rather than overwrite-capable `mv`; removes partial and owned lock artifacts on every handled exit.
- Captures `find | LC_ALL=C sort` into a variable under `pipefail` and fails before retention deletion if enumeration fails. Retention remains the newest exact three archives.
- The collision regression no longer mocks `mv`. It runs two same-timestamp processes through a slow, successful dump producer, proves exactly one success/archive, decrypts it, and verifies no lock/partial remains. The existing integration still uses real PostgreSQL dump, OpenSSL decryption, and `pg_restore --list`.

Exact RED/GREEN evidence:

```text
RED against 6008d2f (before this implementation):
cd frontend && npm run test:db -- --test-name-pattern='rejects destructive|same-second|find enumeration|refuses full'
tests 16; pass 14; fail 2
- root/alias handling returned the old root-only message instead of the required pre-mutation rejection
- two same-second invocations both succeeded (2 !== 1)

GREEN after implementation:
bash -n deploy/backup-staging-postgres.sh                exit 0
cd frontend && npm run test:db                            16 passed, 0 failed
cd frontend && npm test                                   492 passed, 0 failed
cd frontend && npm run lint                               exit 0
git diff --check                                          exit 0
```
