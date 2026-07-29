# Product contract

## Version and ownership

- Skill: `birth-time-rectification-v6`.
- Prompt: `rectification-agent-v6-1`.
- Algorithm: `rectification-v5-matrix-scoring-1` remains unchanged.
- V6 changes the conversation and semantic-question contracts; it does not replace the V5 candidate engine.
- The server owns candidate-minute scanning, the event contribution matrix, Candidate Snapshots, diagnostics, stability gates, Decision Validator, deterministic fallback, Jobs, claim/lease, completed-job replay, atomic completion, idempotency, and persistence.
- Preserve `v4_legacy`, `v5_shadow`, and `v5_agent` deployment behavior. Shadow artifacts must not change the legacy visible reply.

## Result boundary

The product can return a candidate time range only after deterministic minimum-event, minimum-domain, and stability gates pass. An internal or unstable Snapshot is not a public result. A repeated calculation of the same primary range is not a new update.

`canConfirmExactMinute` is always `false`. The product must not present a unique minute or representative minute as the user's true birth time, and rectification completion must not automatically write `profiles.active_birth_time`.

When evidence is sparse, conflicting, tied, date-sensitive, or unstable, stop or continue with one genuinely useful question. Never package uncertainty as certainty or extend the interview without a useful active opportunity.

## Agent authority

The agent may only:

1. select one active server-generated semantic question opportunity;
2. call at most one permitted read-only diagnostic;
3. offer a server-generated candidate range that has passed the public gate; or
4. stop with low confidence.

The agent must not create or alter events, normalized dates, candidate minutes, scores, diagnostic results, or profile birth data.
