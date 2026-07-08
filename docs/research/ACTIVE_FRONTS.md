# Active Fronts

This file is the small index for the current engineering fronts that still drive code changes.

## Shortest-Path Closure Order (2026-06-29)

To avoid scope drift, current work stays inside these four closure lanes only:

1. Relationship adjudicator closure
2. Vimsopaka + functional-role closure
3. Oracle closure batch
4. VedAstro strict ingestion

Reference plan:
- `<repo>/docs/superpowers/plans/2026-06-29-shortest-path-closure-plan.md`

Do not open new product surfaces before at least one of these four lanes is closed.

## Fragment Discipline

- Before touching strict workflow or adjudicator logic, check:
  - `<repo>/docs/research/high_value_fragment_source_map_2026_06_28.md`
  - `<repo>/docs/research/worktree_fragment_triage_2026_06_28.md`
  - `<repo>/docs/research/yoga_benchmark_case_promotion_audit_2026_06_28.md`
  - `<repo>/docs/research/promote_first_repo_truth_pack_2026_07_01.md`
  - `<repo>/docs/research/promote_second_repo_truth_pack_2026_07_01.md`
  - `<repo>/docs/research/promote_third_repo_truth_pack_2026_07_01.md`
  - `<repo>/docs/research/promote_fourth_repo_truth_pack_2026_07_01.md`
- Treat repo truth as authoritative.
- Treat `docs/research/local_drafts`, Gemini brain notes, Codex attachments, and WorkBuddy copies as candidate sources only.

## Relationship Adjudication

- `<repo>/docs/research/marriage_adjudicator_first_pass_audit_2026_06_27.md`
- `<repo>/docs/research/marriage_benchmark_summary_bridge_audit_2026_06_28.md`
- `<repo>/docs/research/isolated_asset_bridge_audit_2026_06_28.md`
- `<repo>/references/event_judgment_marriage.md`
- `<repo>/docs/superpowers/specs/2026-06-28-jaimini-marriage-bridge-v1-design.md`
- `<repo>/scripts/marriage_benchmark_summary.py`

## Career Adjudication

- `<repo>/references/event_judgment_career.md`
- `<repo>/tests/test_mcp_strict_workflow_career.py`
- `<repo>/docs/research/life_event_graph_v1_audit_2026_06_28.md`
- `<repo>/docs/research/functional_benefic_malefic_strict_layer_audit_2026_06_28.md`

## Wealth Adjudication

- `<repo>/docs/research/wealth_adjudicator_first_pass_audit_2026_06_27.md`
- `<repo>/docs/research/wealth_adjudicator_second_pass_audit_2026_06_27.md`
- `<repo>/docs/research/wealth_adjudicator_third_pass_audit_2026_06_27.md`
- `<repo>/docs/research/wealth_adjudicator_fourth_pass_audit_2026_06_28.md`
- `<repo>/docs/research/wealth_adjudicator_fifth_pass_audit_2026_06_28.md`
- `<repo>/docs/research/wealth_adjudicator_sixth_pass_audit_2026_06_28.md`
- `<repo>/docs/research/wealth_adjudicator_sixth_pass_avayogi_boundary_2026_06_28.md`
- `<repo>/docs/research/wealth_adjudicator_seventh_pass_ashtakavarga_bridge_2026_06_28.md`
- `<repo>/references/event_judgment_wealth.md`
- `<repo>/references/yogi-asc-tight-orb-wealth-freeze-guide.md`

## Oracle Closure

- `<repo>/docs/research/oracle_benchmark_inventory_latest.md`
- `<repo>/docs/research/oracle_benchmark_inventory_latest.json`
- `<repo>/docs/research/oracle_closure_master_dashboard_latest.md`
- `<repo>/docs/research/public_benchmark_dashboard_latest.md`
- `<repo>/docs/research/shadbala_absolute_oracle_comparison_audit_2026_06_28.md`
- `<repo>/docs/research/promote_first_repo_truth_pack_2026_07_01.md`
- `<repo>/docs/research/promote_second_repo_truth_pack_2026_07_01.md`
- `<repo>/docs/research/promote_third_repo_truth_pack_2026_07_01.md`
- `<repo>/docs/research/promote_fourth_repo_truth_pack_2026_07_01.md`
- `<repo>/docs/research/raman_dasha_boundary_series_oracle_seed_2026_06_28.md`
- `<repo>/docs/research/tajika_annual_closure_status_latest.md`
- `<repo>/docs/research/tajika_annual_benchmark_dashboard_latest.md`
- `<repo>/scripts/shadbala_oracle_comparison.py`
- `<repo>/references/oracle/`
- Before changing oracle-dependent adjudicator or benchmark claims, run:
  - `python3 scripts/oracle_benchmark_inventory.py --format json`

## VedAstro Adapter MVP

- `<repo>/docs/research/vedastro_parity_matrix_latest.md`
- `<repo>/docs/research/vedastro_parity_matrix_latest.json`
- `<repo>/docs/research/vedastro_fast_path_checklist_latest.md`
- `<repo>/docs/research/vedastro_fast_path_checklist_latest.json`
- `<repo>/docs/research/life_event_graph_v1_audit_2026_06_28.md`
- `<repo>/docs/research/vedastro_range_scan_allowlist_audit_2026_06_28.md`
- `<repo>/scripts/vedastro_python_bridge.py`
- `<repo>/scripts/vedastro_official_mcp_bridge.py`
- `<repo>/scripts/vedastro_method_catalog_sync.py`
- `<repo>/scripts/vedastro_fast_path_checklist.py`
- `<repo>/scripts/vedastro_service_adapter.py`
- follow only after the Jaimini marriage bridge v1 regression loop is closed
- Use the parity matrix before adding or claiming VedAstro-equivalent capability.
- Use the fast-path checklist when deciding whether a VedAstro-facing feature should go through official MCP, official Python bridge, REST adapter, or remain local-native.

## Dignity / Role Guardrails

- `<repo>/docs/superpowers/specs/2026-06-28-dignity-guardrail-v1-design.md`
- `<repo>/docs/research/dignity_guardrail_v1_boundary_audit_2026_06_28.md`
- `<repo>/docs/research/divisional_dignity_context_repair_audit_2026_06_28.md`
- `<repo>/docs/research/functional_benefic_malefic_strict_layer_audit_2026_06_28.md`
- D1-only dignity guardrail is landed.
- Divisional dignity context repair for D9/DK/Vimsopaka Navamsa is also landed.
- Still open:
  - Vimsopaka semantic mapping for `NEECHA_BHANGA / GREAT_FRIEND / GREAT_ENEMY`
  - functional role now enters strict evidence; follow-up is Technique Audit Table rendering.
