# Dual-Project Contract Implementation Plan

> Execute after design approval. Two independent repositories; no runtime coupling.

## Scope

Implement the first synchronization foundation in both repositories:

1. versioned public synthetic-fixture manifest;
2. stable compatibility-hash comparator;
3. append-only cross-project synchronization ledger;
4. focused tests and CI-friendly commands.

No production deployment, secret access, user-data migration, or formula change is
in this phase.

## Shared Files

Create byte-identical copies in both repositories:

- `references/cross_project_contract/fixture_manifest.v1.json`
- `references/cross_project_contract/sync_ledger.json`
- `scripts/cross_project_contract.py`
- `tests/test_cross_project_contract.py`

The fixture uses only generic public synthetic birth inputs. It declares the
effective Ayanamsa and node mode. It contains a `compatibility_hash`, not a full
internal `result_hash`: the former is generated from the fixed public contract
fields below and is intentionally insensitive to extra report/evidence fields.

```text
birth/effective params
ascendant longitude/sign
D1 Sun..Saturn/Rahu/Ketu longitude/sign
```

## Task 1: Research Repository Contract

Files:

- Modify: `scripts/cross_project_contract.py` (new)
- Modify: `references/cross_project_contract/fixture_manifest.v1.json` (new)
- Modify: `references/cross_project_contract/sync_ledger.json` (new)
- Modify: `tests/test_cross_project_contract.py` (new)

Tests first:

1. fixture accepts only synthetic/public metadata and complete effective settings;
2. local calculation reproduces declared compatibility hash;
3. altered node mode or expected hash produces non-zero comparator result;
4. ledger entries require source/target commit, class, file allow-list, secret
   review, tests, hash result and rollback reference.

Implementation:

1. call common `jyotish_engine.compute_chart_data()` directly;
2. normalize only the contract fields into sorted JSON;
3. SHA-256 the normalized bytes;
4. expose `--manifest`, `--format json`, `--require-match`;
5. validate ledger shape without reading either repository's Git history.

Verification:

```bash
python3 -m pytest -q tests/test_cross_project_contract.py
python3 scripts/cross_project_contract.py --require-match --format json
```

## Task 2: Commercial Repository Port

Working tree: `/tmp/Jyotisha-jesse-ux` only after reading its `AGENTS.md` and
running its pre-work check.

Tests first: copy the same contract tests. The initial test must fail because the
contract files do not exist. Port the source commit's four files without copying
deployment configuration or secrets.

Verification:

```bash
.venv/bin/python -m pytest -q tests/test_cross_project_contract.py
.venv/bin/python scripts/cross_project_contract.py --require-match --format json
```

If the commercial virtual environment does not exist, use its documented Python
environment and report the missing dependency rather than installing into
production or changing deployment configuration.

## Task 3: Bidirectional Check

1. run both comparator commands;
2. compare their JSON `compatibility_hash` and manifest SHA-256;
3. append a research-to-commercial ledger entry with exact commits;
4. run public privacy scanning in both repositories;
5. commit research changes to `codex/release-hygiene-ci` and commercial changes
   to `codex/cross-project-contract`; push both branches, but do not merge or
   deploy commercial `main`.

## Failure Handling

- Hash mismatch: do not normalize it away; record mismatch and identify the
  effective parameter/longitude difference.
- Missing external raw: not relevant to a local compatibility hash; retain its
  existing `blocked` state in reports.
- Private or production identifier found: reject the port, record the failure,
  and do not stage it.
- Existing unrelated dirty files: leave untouched.

## Discovery Adjustment

Jyotisha does not yet contain the research repository's
`domain_calculation_service.py`. This is a phase-two safety port, not a
prerequisite for the shared raw-chart compatibility hash. The phase-one
comparator therefore targets the common engine API and does not claim REST/API
calculation-contract parity.
