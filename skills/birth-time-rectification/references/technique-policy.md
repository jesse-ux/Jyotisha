# Technique policy

The conversation refactor does not change the scoring algorithm. Keep `rectification-v5-matrix-scoring-1`, the real Python scan of every minute in the inclusive candidate window, the event contribution matrix, Candidate Snapshots, leave-one-event-out (LOEO), leave-one-domain-out (LODO), date sensitivity, neighbor stability, candidate split, Decision Validator, and deterministic fallback. A cross-midnight window continues into the next calendar day; equal endpoints mean one minute and the maximum window is 1,440 minutes.

Only server-reported available layers may be described as used. Missing, blocked, reference-only, and research-only layers are not evidence of a result. Do not import or reproduce the portable ZIP's candidate segmentation, manual `supports/conflicts` scoring, fixed unknown-mode blocks, arbitrary/dynamic external repository loading, or `main_repository_enhanced` mode.

## Public technique availability gate

- **Required:** only the layers registered for active scoreable domains. Education requires `D24 + vimshottari + narayana`; relocation `D4 + vimshottari + narayana`; relationship `D9 + UL + vimshottari + narayana`; career `D10 + A10 + vimshottari + narayana`; finance `D2 + D11 + vimshottari + narayana`; self health pressure `D30 + vimshottari + narayana`. A missing required layer blocks the public range.
- **Optional:** `KP_cusps`, `A7`, `Ashtakavarga`, and `Shadbala`, plus known domain layers that are not required by the active domains. Their absence does not block the public range. In particular, `KP_cusps` is optional.
- **Reference-only:** D60. It must not contribute points, satisfy a gate, appear as executed in the public receipt, or drive a conclusion.
- **Unclassified:** fail closed. An unknown missing layer blocks publication until classified server-side.

## Diagnostic use

- The Reasoner may request at most one allowed read-only diagnostic in a turn.
- Send only compact conclusions needed for opportunity selection, not the full contribution matrix.
- Date sensitivity determines whether finer date precision is worth asking for.
- LOEO, LODO, neighbor stability, and candidate split diagnose fragility; they do not independently authorize public certainty. The public gate requires LOEO and LODO retention of at least `0.8`.
- Sparse, conflicting, or unstable diagnostics require a lower-confidence stop or another genuinely discriminating question.

LOEO/LODO reuse the same Case matrix after subtracting one event or domain. They are not prospective or independent holdout validation. Per-Case independent holdout remains deferred because no sticky train/holdout partition or calibrated acceptance threshold exists; do not claim it is complete.

## VedAstro post-validation

- This read-only check is available only in `v5_agent`, after the local stability and range-eligibility gates pass, and only for the server-selected primary and runner-up. It does not rescore candidates or replace `rectification-v5-matrix-scoring-1`.
- Minute-sensitive snapshots may test whether the pair is distinguishable. SearchEvents is bounded supporting evidence only and must never select or reverse the final candidate.
- Missing, timed-out, exceptional, incomplete, tied, or non-discriminating provider results fail closed for public range disclosure. They do not invalidate or delete the local Snapshot, diagnostics, or Job artifacts.
- VedAstro can never authorize a unique-minute claim or profile write. Public output and receipts must exclude raw provider requests/responses and internal provider or technique traces.

## Technique boundaries

- Dasha and dated evidence can frame comparison only when present in server results.
- D9 and D10 may support relationship and career analysis when available.
- Topic-specific layers such as D4, D24, D2/D11, D7, and D30 remain bounded by server capability.
- D60 is reference-only and must never drive candidate selection or the public conclusion.
- Event provenance is audit lineage only. Source Turn, raw wording, extraction path, and revision lineage must not change contribution points, layer weights, or confidence.
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
