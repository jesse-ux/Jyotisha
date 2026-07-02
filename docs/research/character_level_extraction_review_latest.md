# Extraction Review Manifest

- status: pass
- scope: extraction-review
- generated_at: 2026-07-02T11:17:16.341748+00:00
- reviewed_files: 66
- runtime_promotions: 0
- stored_text_payload_fields: 0

## Decision Counts

- `asset_or_empty_reference_only`: 17
- `private_reference_only`: 3
- `promote_review_candidate`: 38
- `reference_only`: 8

## Boundary

Review decisions are governance labels only. No extracted source is promoted to runtime truth here.

Promotion still requires human review, source grading, conflict arbitration, and explicit source-pack tests.
