# VedAstro identity closure plan — 2026-07-19

## Current status

VedAstro hosted API remains observation-only.

Reason: hosted output can be replayed, but build identity, method semantics, and deployment version are not archived. Stable mismatch replay proves the conflict is not random transport noise; it does not prove which side is true.

## Acceptable closure paths

### Path A — hosted metadata

Required from upstream:

- hosted build version;
- source commit or release tag;
- method semantic contract for each endpoint used;
- ayanamsa/node/timezone interpretation;
- deployment timestamp or immutable build ID.

### Path B — pinned self-hosted version

Required archive:

- source commit;
- NuGet package hash;
- DLL SHA-256;
- assembly version;
- public method inventory;
- container image digest or reproducible local runner hash.

`scripts/vedastro_identity_archive.py` now records the NuGet identity and a `required_self_host_evidence` checklist. Missing fields keep truth upgrade blocked.

## Claim boundary

Allowed:

- use VedAstro as external observation;
- report stable conflicts;
- compare raw response hashes and normalized fields;
- use pinned self-hosted evidence if all required identity fields are present.

Forbidden:

- tune production predictions from hosted output with unknown build identity;
- call hosted mismatch arbitration a global truth decision;
- silently prefer VedAstro or local output by majority vote.

## Commercial sync rule

Commercial may receive:

- `VedAstro: observation_only`;
- endpoint status;
- claim boundary text.

Commercial must not receive:

- raw hosted credentials;
- hosted output as truth;
- production tuning permission while `truth_upgrade_gate` is blocked.
