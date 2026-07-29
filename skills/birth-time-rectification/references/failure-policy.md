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


## Analysis receipt failures

- Missing phase history, tool traces, technique evidence, or provider reasoning is represented by omission, never by reconstruction or invented text.
- A provider reasoning payload that fails source checks or the server safety filter is discarded. Do not fall back to hidden reasoning, a second-model summary, or raw provider metadata.
- If a Job fails before durable artifacts exist, show only a safe public failure state; do not expose internal error codes or partial model output.
- Legacy records without analysis receipts must continue to load. `v4_legacy` and `v5_shadow` visible replies must not change merely to populate the receipt.
- Receipt persistence and Turn association must be replay-safe and owner-scoped. Refresh, completed-job replay, or retry must not duplicate, reorder, or attach a receipt to another Turn.
