# Advanced Technique Adjudicator ROI Queue - 2026-06-28

## Audit Basis

The capability registry validates 89 techniques. A stricter static pass over
advanced Vedic/Jyotish techniques found 76 high-value advanced techniques, of
which roughly 22 are directly consumed by the current MCP strict workflows or
their evidence contracts. Around 54 remain useful but under-used by the
adjudicators.

`covered` means the project can compute or expose the technique. It does not
mean the technique is already weighted in relationship, finance, career, or
event adjudication.

## First ROI Queue

1. `A10 / AmK / Karakamsha` into career adjudication.
   - Status: implemented in this pass.
   - Reason: highest value for career timing and status manifestation.
2. `Argala / Virodhargala` into career and relationship conflict handling.
   - Reason: distinguishes support from obstruction.
3. `Ashtakavarga PAV / Sodhita / Kakshya` into finance and transit timing.
   - Reason: already computed but not deeply weighted.
4. `Shadbala six components` into finance/career/relationship confidence caps.
   - Reason: total strength exists; component-level use is still shallow.
5. `Yogini / Ashtottari / Kalachakra` as secondary dasha convergence.
   - Reason: already available in full-reading but not adjudicator-weighted.
6. `D7 / D12 / D24 / D30 / D60` domain-specific varga gates.
   - Reason: needed for child, family, education, crisis, and ultra-sensitive
     rectification contexts.
7. `Tajika / Sahams` annual event adjudication.
   - Reason: annual closure has begun but is not yet a general verdict layer.
8. `KP ruling planets / Prashna workflow` for specific yes/no event questions.
   - Reason: high value but requires stricter question-time input boundaries.

## Implemented This Pass

Career strict workflow now requires and scores:

- `varga_full.D10_Dasamsa`
- `special_lagnas.A10_Karma_Pada`
- `jaimini.karakas.Amatyakaraka`
- `jaimini.karakamsha`
- `dasha.current_dasha`
- `narayana_dasha.current_dasha`
- `dasa_convergence.domain_activations.career_status`

It emits:

- `dominant_label = "career_status"` only when hard gates are present and score
  reaches the moderated threshold.
- `secondary_context` values: `a10_active`, `amk_active`,
  `karakamsha_context`, and optional `external_activation_support`.

## Verification

- `python3 -m pytest tests/test_mcp_strict_workflow_career.py tests/test_mcp_strict_workflow_relationship.py tests/test_mcp_strict_workflow_finance.py tests/test_vedastro_service_adapter_executor.py -q`
- Result: `37 passed`

## Boundary

This is not a full career prediction engine. The new workflow only converts
already-computed A10/AmK/Karakamsha assets into auditable strict evidence. It
does not claim external oracle closure for career event timing.
