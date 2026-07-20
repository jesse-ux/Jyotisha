# Task 3 — Encrypted Local Staging Backups

## Scope delivered

- Added `deploy/backup-staging-postgres.sh DATABASE_ENV_FILE BACKUP_DIRECTORY`.
- Validates the private database environment before reading required values without sourcing or executing the env file.
- Refuses backup destinations with disk usage at or above 70%, creates the explicit destination with mode `0700`, writes encrypted custom PostgreSQL dumps with mode `0600`, and keeps only the newest three exact staging dump names.
- Uses a PID-scoped `.partial` file, `pipefail`, an exit cleanup trap, and same-directory rename so failed dump/encryption pipelines leave no completed partial archive and successful archives are published atomically.
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
