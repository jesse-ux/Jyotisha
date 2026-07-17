# VedAstro Live Replay Conflict 2026-07-17

## Status

`blocked`: a fresh official VedAstro full snapshot for the public Steve Jobs
same-chart case does not reproduce the previously recorded D1 longitude packet.
This report records an external-oracle conflict. It does not authorize prediction
claims, production tuning, or a three-engine closure claim.

## Reproducible Public Request

- Case: `steve_jobs_public_aa` / `steve_jobs_public_1955_lahiri`
- Birth time: `19:15 24/02/1955 -08:00`
- Location: `37.7749, -122.4194`
- Ayanamsa / node mode: `lahiri` / `mean`
- Fresh local raw artifact: `scratch/local/vedastro_adapter/official_full_snapshot-1ff276e8fdee-ab172556e932.json`
- Fresh official raw response SHA-256: `ab172556e9327f55ce5a14d2a2da91c7736690c5181ba59627d0acbf0d1b0ef8`
- Runner output: `scratch/local/three_engine_parity_vedastro_live/three_engine_parity_replay.json`
- Independent repeat raw response SHA-256: `64c784ddfce22b83f2ba4a666983c1ca3a01f54c6f4d49dd1070167dbf850d54`
- Repeat runner output: `scratch/local/three_engine_parity_vedastro_retry/three_engine_parity_replay.json`

## Fresh Result

| metric | value |
|---|---:|
| normalized D1 rows | 15 |
| matches | 9 |
| mismatches | 5 |
| blocked rows | 0 |

Mismatched fields: `Sun.longitude`, `Moon.longitude`, `Mars.longitude`,
`Mercury.longitude`, `Venus.longitude`.

The independent repeat used the same visible request body and produced the same
five normalized mismatch values. The raw response hash differs, but the
normalized external discrepancy is stable for this endpoint replay.

## Conflict Arbitration

The prior commercial manifest referenced a research-local scratch artifact with
the same visible birth-time request but a different official response hash. Two
fresh official responses converge on the same five normalized discrepancies.
The mismatch must remain visible until the VedAstro endpoint/version/method
contract explains the drift. Do not replace the old packet with a pass result
or tune local calculations to match either response.

## Required Next Evidence

1. Capture official API version and method identifiers alongside the raw packet.
2. Replay the same request after a bounded delay and compare response hashes.
3. Publish a redacted, versioned public packet only after the response is stable.
4. Require a fresh normalized 15-row comparison before changing
   `three_engine_parity_replay_manifest.json` from its current blocked boundary.
