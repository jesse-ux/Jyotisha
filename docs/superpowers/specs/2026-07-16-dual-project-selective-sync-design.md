# Dual-Project Selective Synchronization Design

Date: 2026-07-16

## Scope

Two repositories remain independently deployable and independently releasable.

| Repository | Role | Primary success measure |
| --- | --- | --- |
| `732642856/yinduzhanxing` | Backup/research implementation | Calculation correctness, evidence closure, reproducible regressions |
| `jesse-ux/Jyotisha` | Commercial product | Safe user experience, authenticated delivery, deployable operations |

No repository becomes a submodule, package dependency, or required runtime peer of
the other. Cross-project work is a reviewed copy with an auditable provenance
record, not automatic mirroring.

## Directional Adoption

### Research to commercial

Port only a passing, self-contained change plus its focused tests:

- effective calculation parameters and result hashes;
- runtime-truth evidence manifests and honest external-oracle status;
- Prashna server-authoritative context and blocked approximate verdicts;
- precision-timing output gate;
- privacy, report-renderer isolation, Origin/capability-token/TTL controls;
- external parity diagnostics and Western evidence packet contracts.

### Commercial to research

Port only configuration-free product patterns plus tests:

- mobile consultation flow and accessibility improvements;
- authenticated account/session and credit contracts using local test doubles;
- Docker, health checks, CI workflow structure and deployment documentation;
- user-facing error, timeout and degradation presentation.

Never copy production secrets, server addresses, SSH material, Supabase project
identifiers, live user records, payment credentials, or production `.env` files.

## Shared Contract

Each project will contain the same versioned fixture manifest. For every fixture it
must record birth input, effective parameters, local result hash, evidence packet
schema version, external-oracle state and required test IDs.

The acceptance command compares only public, synthetic fixtures. A mismatch blocks
the port; it never overwrites either project automatically. External parity fields
must use `local_operational`, `externally_verified`, and `prediction_validated` as
separate states.

## Sync Ledger

Each port gets one ledger row:

| Field | Requirement |
| --- | --- |
| source repository and commit | immutable source reference |
| target repository and commit | immutable landing reference |
| change class | calculation, evidence, security, UX, deployment, or docs |
| copied files and dependency delta | explicit allow-list |
| secret/privacy review | pass required |
| focused tests | command and result |
| hash-contract result | pass, mismatch, or not applicable |
| rollback | source and target commit references |

## Delivery Order

1. Add the identical public cross-project fixture manifest, comparator and sync
   ledger schema to both repositories.
2. Port research safety/correctness gates into Jyotisha, preserving its production
   deployment constraints.
3. Port Jyotisha product patterns into the backup repository using local-only
   configuration and test doubles.
4. Add CI acceptance in each repository that validates its own copy of the shared
   fixture manifest.
5. Only after two successful directional ports, evaluate reusable extraction. No
   repository merge is in scope.

## Failure Policy

- A missing external raw artifact is `blocked`, never `verified`.
- A missing local scratch file cannot fail a public release truth gate.
- Any copied calculation path that changes a public fixture result hash requires
  manual review and fresh external-oracle comparison.
- Any commercial-origin file containing a production identifier or secret is
  rejected before staging.
