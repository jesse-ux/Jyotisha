# Interpretation Source Full Classification - 2026-07-02

This report is generated from `scripts/interpretation_source_inventory_gate.py`.
It classifies local interpretation/rule/case/template/evidence candidates without
promoting drafts into runtime truth.

## Summary

| Metric | Count |
|---|---:|
| Runtime source refs already wired | 22 |
| Indexed-only refs | 3 |
| Full candidate pool | 948 |
| Unclassified candidates | 0 |
| Priority 1 candidates | 264 |
| Priority 2 candidates | 101 |
| Priority 3 candidates | 558 |

## Classification Counts

| Classification | Count |
|---|---:|
| runtime_reference_layer | 22 |
| indexed_reference_layer | 3 |
| reference_candidate | 171 |
| real_case_calibration | 5 |
| open_source_reference | 102 |
| oracle_artifact | 50 |
| benchmark_evidence | 33 |
| template_asset | 4 |
| frontend_surface | 31 |
| research_governance | 412 |
| quarantined_draft | 87 |
| project_governance | 28 |

## Promotion Status Counts

| Promotion Status | Count |
|---|---:|
| already_wired | 22 |
| indexed | 3 |
| reference_layer_candidate | 278 |
| real/source evidence only buckets combined | 83 |
| governance_or_history | 440 |
| not_truth_source | 87 |
| product_surface | 31 |
| template_reference | 4 |

## Priority Policy

- `priority_1`: review first. This includes `references/`, `real_case_studies/`, `rishi-ai-mcp`, and `vedic-astro-skills`.
- `priority_2`: validation/template/oracle evidence. These can support boundaries and tests but are not direct interpretive truth.
- `priority_3`: research history, frontend surfaces, project governance, and quarantined drafts. These are indexed so they are not forgotten, but they must not be silently promoted.
- `runtime`: already wired or indexed by the active source pack.

## Boundary

This is a classification map, not a promotion decision. A file classified as
`reference_layer_candidate` still needs source review, license review when
applicable, and focused tests before it can become a runtime source.
