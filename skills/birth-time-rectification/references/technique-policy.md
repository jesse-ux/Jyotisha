# Technique policy

The conversation refactor does not change the scoring algorithm. Keep `rectification-v5-matrix-scoring-1`, Python candidate-minute scanning, the event contribution matrix, Candidate Snapshots, leave-one-event-out, leave-one-domain-out, date sensitivity, neighbor stability, candidate split, Decision Validator, and deterministic fallback.

Only server-reported available layers may be described as used. Missing, blocked, reference-only, and research-only layers are not evidence of a result. Do not import or reproduce the portable ZIP's candidate segmentation, manual `supports/conflicts` scoring, fixed unknown-mode blocks, dynamic repository loading, or `main_repository_enhanced` mode.

## Diagnostic use

- The Reasoner may request at most one allowed read-only diagnostic in a turn.
- Send only compact conclusions needed for opportunity selection, not the full contribution matrix.
- Date sensitivity determines whether finer date precision is worth asking for.
- Leave-one-event/domain-out, neighbor stability, and candidate split diagnose fragility; they do not independently authorize public certainty.
- Sparse, conflicting, or unstable diagnostics require a lower-confidence stop or another genuinely discriminating question.

## Technique boundaries

- Dasha and dated evidence can frame comparison only when present in server results.
- D9 and D10 may support relationship and career analysis when available.
- Topic-specific layers such as D4, D24, D2/D11, D7, and D30 remain bounded by server capability.
- D60 is reference-only and must never drive candidate selection or the public conclusion.
- Never expose private scores, weights, contribution values, internal technique traces, or tool/model names in the user-facing message.
- No technique result can override `canConfirmExactMinute === false` or authorize an automatic profile birth-time write.


## Public execution receipt

The analysis receipt reports observed execution, not the complete capability catalog. A technique or diagnostic may be named only when persisted server artifacts prove it ran in that Turn.

- Candidate-minute scanning and stability diagnostics are shown only on turns that executed them.
- A Reasoner diagnostic is shown as an Agent read only when its persisted tool trace records the call; precomputed diagnostics are not Agent tool calls.
- Technique labels are derived through a server allowlist from actual contribution/technique metadata. Never expose rule IDs, raw layers, scores, weights, contribution values, matrices, arguments, or candidate minutes.
- Unsupported, unavailable, skipped, blocked, reference-only, and research-only layers are omitted rather than shown as missing work.
- D60 is omitted from the receipt and must not drive candidate selection, stability claims, or public conclusions.
- Provider-explicit reasoning content is not technique evidence. It may appear only as a separately labeled, server-filtered summary and never as hidden chain-of-thought.
