# User-reported birth-time flow issues — 2026-07-20

This ledger records the five reported product failures and the evidence needed
to close them. It contains no copied authentication header, cookie, token,
email, user UUID, or real birth record. The original plan described this file as
an existing modification target; it did not exist in this checkout, so Task 12
created it.

`verified-local` means deterministic contract tests and the equivalent local
PostgreSQL 14 workflow pass. It is deliberately not `closed`: closure also
requires an authenticated synthetic production smoke whose health Git SHA is
the tested deployment SHA.

| Issue | Reported failure | Current status | Local evidence | Production closure artifact |
| --- | --- | --- | --- | --- |
| ISSUE-BT-001 | A chat appeared impossible to delete, or a late response could recreate it. | verified-local | `20260720000000_chat_delete_and_dynamic_candidate_confirmation.sql`; `frontend/tests/chat-session-delete-contract.test.ts`; the PG14 full-flow test deletes a real RLS-owned chat as `authenticated` and proves the account case remains. | Authenticated synthetic delete plus account-case reload, tied to `/api/health` deployment SHA. |
| ISSUE-BT-002 | A new chat could not establish a fresh rectification interaction and unfinished progress was coupled to chat state. | verified-local | `20260720010000_conversational_rectification_schema.sql`; account-level resume in `frontend/tests/conversational-rectification-e2e.test.ts` across two route clients; Task 9 current-chat consent tests. | Authenticated new-device/new-chat resume smoke tied to the deployed SHA. |
| ISSUE-BT-003 | Confirming a candidate such as `17:15` surfaced `The string did not match the expected pattern`. | verified-local | Atomic v3 confirmation in `20260720030000_conversational_rectification_transitions.sql`; client retry/fallback and mismatched-then-exact confirmation in `frontend/tests/conversational-rectification-e2e.test.ts`; the PG14 full-flow test rejects `05:20`, confirms exact `05:21`, and proves the old time survives until commit. | Authenticated production exact-candidate confirmation with old-time preservation, plus transient deployment-error probe. |
| ISSUE-BT-004 | Choosing `都不符合` surfaced the same raw English pattern error. | verified-local | The actual orchestrator treats `都不符合` as a normal direction change; Task 12 E2E advances the durable turn and preserves the single fee; client maps terminal 502/non-JSON failures to stable Chinese copy. | Authenticated production `都不符合` action followed by reload/resume, tied to the deployed SHA. |
| ISSUE-BT-005 | Initialization used generic broad-year choices and lost the rich card/chat rectification analysis. | verified-local | Task 9 onboarding soft gate; v3 narrative grounding rejects broad-year questionnaires; Task 12 asserts candidate boundary, D1/D9/D10 layers, three domain rationales, free text, and year/month event request; PG14 proves future background persists without scoring and the legacy suite imports old unfinished work once with `migration_waived`. | Authenticated synthetic first-turn snapshot and one legacy import smoke tied to the deployed SHA. |

## Initial production diagnosis (preserved)

The original issue record captured these causes before implementation:

- Chat deletion lacked both an authenticated `DELETE` grant and an owner-only
  RLS policy.
- `startNewChat()` created only a chat session; the birth profile and
  rectification case were account-scoped, so a new chat could not start an
  explicit re-rectification while preserving the active chart.
- `dynamic-choice-v2` emitted `request_candidate_confirmation`, but the client
  sent the legacy `confirm_guided_candidate` mutation, which rejected dynamic
  cases and left them in `confirming` without applying the candidate.
- The reported `都不符合` failure coincided with a deployment replacement in
  which Caddy returned HTTP 502 while Docker could not resolve the temporarily
  unavailable `web` service.
- WebKit can represent a non-JSON parse failure as a `DOMException` named
  `SyntaxError`; the old transport recognized JavaScript `SyntaxError` only and
  could expose `The string did not match the expected pattern.` instead of
  stable Chinese product copy.

The original closure checklist required owner-only deletion, explicit
account-level re-rectification, atomic idempotent candidate confirmation,
deployment availability or bounded retry behavior, stable localized WebKit
errors, and authenticated end-to-end coverage for `都不符合`, confirmation,
re-rectification, and deletion. The table above maps each requirement to the
implemented local evidence and the remaining production proof.

## Release decision

All five issues remain `verified-local` until the production closure artifacts
above are attached. A public 200 response, an unverified browser session, or a
local in-memory test cannot change them to `closed`. The deployment sequence and
non-destructive rollback are defined in `deploy/README.md`. The executable
creation policy keeps rollout `smoke_only` for one unlogged synthetic account
until the smoke SHA matches the exact deployed revision; ordinary users cannot
incur a new rectification charge during that canary window.
