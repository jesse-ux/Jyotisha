# Worktree Fragment Triage - 2026-06-28

## Purpose

This note records the current dirty-worktree fragments after the high-value bridge passes. It prevents future agents from repeatedly rediscovering the same files and mistaking scratch output for source truth.

## Promoted In This Pass

- Shadbala absolute oracle comparison:
  - `<repo>/scripts/shadbala_oracle_comparison.py`
  - `<repo>/docs/research/shadbala_absolute_oracle_comparison_audit_2026_06_28.md`
- VedAstro range scan allowlist and signal metadata:
  - `<repo>/scripts/vedastro_service_adapter.py`
  - `<repo>/docs/research/vedastro_range_scan_allowlist_audit_2026_06_28.md`
- Marriage benchmark summary bridge:
  - `<repo>/scripts/marriage_benchmark_summary.py`
  - `<repo>/docs/research/marriage_benchmark_summary_bridge_audit_2026_06_28.md`

## Remaining Fragments

### Generated or Scratch Output

Do not promote without a specific new use case:

- `<repo>/full_chart_data.json`
- `<repo>/test_dasha.json`
- `<repo>/test_output.json`
- `<repo>/scratch_extract.py`
- `<repo>/scratch_mcp_eval.py`

### Duplicate Benchmark Output

- `<repo>/tests/verify-results-v6.1.json`

The canonical tracked source is:

- `<repo>/tests/test-data/verify-results-v6.1.json`

The untracked copy differs mainly by list ordering inside target arrays and does not need promotion as a second source of truth.

### Generated Report Candidate

- `<repo>/tests/印度占星实战案例综合验证报告-v6.1-2026-05-03.md`

Much of its durable content is already represented by:

- `<repo>/references/verified-patterns-marriage-timing-v6.md`
- `<repo>/scripts/marriage_benchmark_summary.py`

Only promote this report later if a stable human-facing archive is needed.

### Weak Test Candidates

- `<repo>/tests/test_dasha_raman_truth.py`
  - Current state: `pytest.xfail` placeholder with mocked computation.
  - Disposition: useful boundary values were promoted into `<repo>/references/oracle/dasha_shadbala_oracle_cases.json` as `template_bv_raman_vimshottari_boundary_series`.
  - Follow-up: collect source artifact metadata before promoting beyond `template_only`.
- `<repo>/tests/test_yoga_benchmark_cases.py`
  - Disposition: promoted into a real benchmark with concrete `rule_id` expectations and metadata contract checks.
  - See `<repo>/docs/research/yoga_benchmark_case_promotion_audit_2026_06_28.md`.

### Superseded or Needs Review

- `<repo>/scripts/oracle_functional_benefics.py`
  - Superseded in strict evidence by the functional benefic/malefic layer in `mcp_server.py`.
  - Could be promoted later only if rewritten as a JSON CLI around the canonical helper.
- `<repo>/scripts/patch_api_tz.py`
- `<repo>/scripts/patch_engine_tz.py`
- `<repo>/scripts/sync_to_workbuddy.sh`
  - Review manually before promotion. Do not batch-commit as-is.

### Benign Generated Timestamp

- `<repo>/references/oracle/artifacts/pyjhora_oracle_artifact_manifest.json`

Current diff only changes `generated_at`. Do not commit timestamp-only churn unless the artifact inventory materially changes.
