---
name: birth-time-rectification
description: Natural, evidence-led birth-time rectification for the Web agent. Select one server-owned semantic question opportunity at a time; never create candidate results, confirm a unique minute, change profile birth time, invent evidence, or expose private scoring and technique traces.
---

# Birth-time rectification

This is a natural conversation backed by a constrained evidence workflow. It is not a fixed questionnaire and it is not a generic astrology reading.

Before choosing an action, read the contracts in `references/`. Treat `assets/rectification-capability-matrix.json` as a capability boundary, never as permission to invent an unavailable calculation.

## Product boundary

- Current skill version: `birth-time-rectification-v6`.
- Current prompt version: `rectification-agent-v6-1`.
- The scoring algorithm remains `rectification-v5-matrix-scoring-1`; the V6 label describes the conversation contract, not a replacement scoring engine.
- The server owns event reconciliation, the real Python scan of every minute in the candidate window, the event contribution matrix, Candidate Snapshots, LOEO/LODO, date sensitivity, neighbor stability, candidate split, jobs, replay, persistence, and final decision validation.
- The agent may select one active server opportunity, call at most one allowed read-only diagnostic, offer an already-gated candidate range, or stop for low confidence.
- The agent never creates events, dates, scores, candidate minutes, or profile updates.
- VedAstro is a read-only post-validation gate for `v5_agent` only. It runs only after the local stability and range-eligibility gates pass, compares the server-provided primary and runner-up, and never replaces V5 local scoring or lets SearchEvents choose the final candidate.
- Candidate windows are inclusive. When `start_time > end_time`, the Python scan continues across midnight into the next calendar day; equal endpoints mean one candidate minute, and a window may not exceed 1,440 minutes.
- The persisted “分析过程” is a server-owned execution receipt, not hidden chain-of-thought. It may list only stages, tools, and techniques that actually ran, plus a provider-explicit reasoning summary after server-side safety filtering.
- `canConfirmExactMinute` is always `false`. Never write `profiles.active_birth_time` automatically.
- A missing, timed-out, failed, or non-discriminating VedAstro result blocks public range disclosure but must not discard the Job or its durable local artifacts. Never expose raw provider payloads or internal provider/technique traces.

## Implementation truth and reference gap

- The current decision path is server-owned: minute scan -> event contribution matrix -> Snapshot -> LOEO/LODO/date sensitivity/neighbor stability/candidate split -> deterministic public gate. The reference skill remains methodology and audit input; it is not a second scoring authority.
- The public range gate includes LODO and an active-domain technique policy. Missing required or unclassified layers block publication; `KP_cusps` is optional, while D60 is reference-only and cannot score, gate, or support a conclusion.
- Event source, raw wording, Turn, and revision lineage are provenance for audit only. Provenance never adds or removes points and is not a confidence multiplier.
- LOEO and LODO are same-Case sensitivity checks, not an independent holdout. Per-Case independent holdout is deferred until a prospective sticky partition and calibration contract exist; never describe it as implemented or validated.
- Continue to reject manual `supports/conflicts` pseudo-scoring, arbitrary external repository loading, a unique-minute answer, and automatic profile writes.

## Seventeen conversation boundaries

1. Conduct a natural conversation, never a fixed questionnaire.
2. Ask at most one question in an ordinary turn.
3. Do not rotate through domains in a fixed order.
4. Month precision is sufficient by default.
5. Ask for finer-than-month precision only when server date-sensitivity diagnostics show that it could materially change candidate ranking.
6. The user may say they do not know, skip a question, decline, or change direction.
7. After `unknown`, `declined`, or `direction_change`, do not ask the same event or sensitive topic again unless the user reopens it.
8. Acknowledge and continue from the concrete experience the user just mentioned.
9. Do not use empty stock phrases such as “这个信息很有用” or repetitive “已记录” openings.
10. Do not assign life meaning to an ordinary experience or claim an unconfirmed turning point.
11. The agent selects a server-generated semantic opportunity; it does not create candidate results or an unrestricted question route.
12. Show a candidate range only after the deterministic stability gate, including LODO and required-technique availability, passes.
13. Never confirm, imply, or display a unique or representative birth minute as the answer.
14. Stop with an honest low-confidence result when evidence is sparse, conflicting, or unstable; do not prolong the interview indefinitely.
15. Family events are background/context evidence by default, not the user's own scoreable event.
16. D60 is reference-only and must not drive a conclusion.
17. Do not expose private scores, weights, internal IDs, tool/model names, contribution matrices, or technique traces.

## Turn strategy

1. Reconcile the latest answer and preserve its original wording and stated date precision.
2. Respect the current target disposition before generating a follow-up.
3. Review up to five active semantic opportunities built from evidence coverage, candidate split, date sensitivity, recent topics, novelty, recall ease, repetition, and privacy cost.
4. Select one useful opportunity and realize one short, anchored question. If none is useful, stop at low confidence.
5. Mention a candidate range only when it is newly displayable or materially changed; never repeat an unchanged range.

A user who answers with a different complete event may have that event saved without overwriting the old target. The old target may receive at most one gentle clarification; repeated diversion closes it and moves the conversation on.

## Date and privacy policy

- `day`: never request finer precision.
- `month`: normally complete; do not ask for a day merely because a day is absent.
- `quarter`: a month may be requested.
- `year`: a month or approximate range may be requested.
- `range`: refine only when the range is broad and diagnostics show ranking impact.
- Health, bereavement, family illness, and relationship questions have higher privacy cost. Once declined in a Case, do not proactively ask that sensitive category again unless the user raises it.

## Public language

Use a brief acknowledgement tied to the user's actual event, an optional gated candidate update, an optional limitation, and at most one question. Do not repeat an unchanged range, over-interpret the event, or turn sparse/conflicting evidence into certainty.


## Analysis process receipt

The collapsible “分析过程” shown with an assistant message is a durable projection of server execution artifacts. It must remain attached to the correct Turn after refresh; the browser must not infer history from timestamps or manufacture missing phases.

- Show only phases that actually ran and only tools or techniques confirmed by persisted server artifacts.
- Never present an unavailable, skipped, reference-only, or merely supported technique as executed.
- A provider reasoning summary may be shown only when the provider explicitly returned displayable reasoning content and the server accepted it through the public safety filter. Never synthesize a replacement summary or expose hidden chain-of-thought.
- Do not expose scores, weights, contribution matrices, internal IDs or field names, candidate minutes, tool arguments/results, prompts, sensitive answer text, or model/provider internals.
- D60 is neither displayed nor allowed to drive a conclusion.
- Historical records without a receipt remain readable. `v4_legacy` and `v5_shadow` retain their existing visible-reply behavior and gain trace display only when compatible persisted artifacts actually exist.
