# Worktree Fragment Triage - 2026-06-28

## Purpose

This note records the current dirty-worktree fragments after the high-value bridge passes. It prevents future agents from repeatedly rediscovering the same files and mistaking scratch output for source truth.

## Promoted In This Pass

- Shadbala absolute oracle comparison:
  - `/Users/wuyongnaren/Documents/印度占星/scripts/shadbala_oracle_comparison.py`
  - `/Users/wuyongnaren/Documents/印度占星/docs/research/shadbala_absolute_oracle_comparison_audit_2026_06_28.md`
- VedAstro range scan allowlist and signal metadata:
  - `/Users/wuyongnaren/Documents/印度占星/scripts/vedastro_service_adapter.py`
  - `/Users/wuyongnaren/Documents/印度占星/docs/research/vedastro_range_scan_allowlist_audit_2026_06_28.md`
- Marriage benchmark summary bridge:
  - `/Users/wuyongnaren/Documents/印度占星/scripts/marriage_benchmark_summary.py`
  - `/Users/wuyongnaren/Documents/印度占星/docs/research/marriage_benchmark_summary_bridge_audit_2026_06_28.md`

## Remaining Fragments

### Generated or Scratch Output

Do not promote without a specific new use case:

- `/Users/wuyongnaren/Documents/印度占星/full_chart_data.json`
- `/Users/wuyongnaren/Documents/印度占星/test_dasha.json`
- `/Users/wuyongnaren/Documents/印度占星/test_output.json`
- `/Users/wuyongnaren/Documents/印度占星/scratch_extract.py`
- `/Users/wuyongnaren/Documents/印度占星/scratch_mcp_eval.py`

### Duplicate Benchmark Output

- `/Users/wuyongnaren/Documents/印度占星/tests/verify-results-v6.1.json`

The canonical tracked source is:

- `/Users/wuyongnaren/Documents/印度占星/tests/test-data/verify-results-v6.1.json`

The untracked copy differs mainly by list ordering inside target arrays and does not need promotion as a second source of truth.

### Generated Report Candidate

- `/Users/wuyongnaren/Documents/印度占星/tests/印度占星实战案例综合验证报告-v6.1-2026-05-03.md`

Much of its durable content is already represented by:

- `/Users/wuyongnaren/Documents/印度占星/references/verified-patterns-marriage-timing-v6.md`
- `/Users/wuyongnaren/Documents/印度占星/scripts/marriage_benchmark_summary.py`

Only promote this report later if a stable human-facing archive is needed.

### Weak Test Candidates

- `/Users/wuyongnaren/Documents/印度占星/tests/test_dasha_raman_truth.py`
  - Current state: `pytest.xfail` placeholder with mocked computation.
  - Disposition: useful boundary values were promoted into `/Users/wuyongnaren/Documents/印度占星/references/oracle/dasha_shadbala_oracle_cases.json` as `template_bv_raman_vimshottari_boundary_series`.
  - Follow-up: collect source artifact metadata before promoting beyond `template_only`.
- `/Users/wuyongnaren/Documents/印度占星/tests/test_yoga_benchmark_cases.py`
  - Current state: smoke-style test ending in `assert True`.
  - Better path: replace with concrete yoga names and expected detections before promotion.

### Superseded or Needs Review

- `/Users/wuyongnaren/Documents/印度占星/scripts/oracle_functional_benefics.py`
  - Superseded in strict evidence by the functional benefic/malefic layer in `mcp_server.py`.
  - Could be promoted later only if rewritten as a JSON CLI around the canonical helper.
- `/Users/wuyongnaren/Documents/印度占星/scripts/patch_api_tz.py`
- `/Users/wuyongnaren/Documents/印度占星/scripts/patch_engine_tz.py`
- `/Users/wuyongnaren/Documents/印度占星/scripts/sync_to_workbuddy.sh`
  - Review manually before promotion. Do not batch-commit as-is.

### Benign Generated Timestamp

- `/Users/wuyongnaren/Documents/印度占星/references/oracle/artifacts/pyjhora_oracle_artifact_manifest.json`

Current diff only changes `generated_at`. Do not commit timestamp-only churn unless the artifact inventory materially changes.
