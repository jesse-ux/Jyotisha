# Failure policy

## Conversation failures

- Invalid Reasoner output, an unavailable model, or exhausted diagnostic budget uses the deterministic server policy.
- Invalid Renderer output uses the selected opportunity's validated `fallbackPrompt`.
- A failed or unavailable model-assisted event extraction leaves deterministic extraction and pending evidence intact; it must not fabricate an event or date.
- `unknown`, `declined`, and `direction_change` are valid conversation outcomes, not parsing failures and not life events.
- After a refusal or direction change, close the target and do not repeat it.

## Evidence failures

Stop with low confidence when evidence is too sparse, conflicting, tied, unstable, privacy-costly, or unlikely to add information. Do not turn an internal Snapshot into a public range before its gate passes. Do not keep asking merely to fill a domain checklist.

A month-dated event is not a failure. Refine it only when date-sensitivity diagnostics show that finer precision could change candidate ranking.

## System failures

Preserve the existing Job and persistence guarantees: claim/lease, idempotency, completed-job replay, and atomic completion. A renderer or extraction failure must not cause partial artifact writes, duplicate completion, profile mutation, or a different replay result.

Never log raw sensitive answers to ordinary telemetry. Persist user text only in the approved Turn/evidence stores required by the product contract.
