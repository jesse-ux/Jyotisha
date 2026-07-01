# 2026-06 Local Drafts Disposition

Date: 2026-07-01

Purpose: freeze the governance boundary for `docs/research/local_drafts/2026-06` without deleting or moving the drafts. The draft directory is evidence and recovery memory, not runtime truth. Do not move or delete files in this pass.

Source-of-truth rule:

- Main repo truth stays in `SKILL.md`, `AGENTS.md`, `references/`, `scripts/`, `tests/`, and canonical `docs/research/*.md`.
- `.workbuddy` is a historical distribution mirror and recovery reference only. It must not reverse-sync over this repo, and runtime code must not import from it.
- A `promote` row means the draft should be converted into a canonical research note, benchmark artifact, test, or source change before it drives implementation.
- A `reference-only` row means it can be cited as background after re-anchoring to current code and licenses.
- An `archive` row means it should stay out of current implementation flow unless a future audit explicitly reopens it.

## Disposition Table

| Disposition | Draft | Reason |
|---|---|---|
| reference-only | antigravity_round31_api_completion_top50_2026_06_26.md | Older API exposure wishlist; re-check against current `jyotish_api_server.py` before reuse. |
| promote | antigravity_round31_ayanamsa_ephemeris_timezone_risk_matrix_2026_06_26.md | Core accuracy boundary for ayanamsa, ephemeris, timezone and node-mode evidence. |
| reference-only | antigravity_round31_cli_completion_top50_2026_06_26.md | Useful CLI wishlist, but many items are superseded by later tests and active plans. |
| reference-only | antigravity_round31_cloud_sync_whitelist_final_draft_2026_06_26.md | Distribution-sync background only; current rule is no reverse contamination from `.workbuddy`. |
| archive | antigravity_round31_codex_round32_top180_2026_06_26.md | Broad execution board superseded by later narrower closure plans. |
| promote | antigravity_round31_copy_allowed_assets_top80_2026_06_26.md | License-safe reuse candidates need canonical whitelist linkage before code migration. |
| promote | antigravity_round31_external_oracle_closure_top60_2026_06_26.md | External oracle closure remains a high-rigor blocker and should feed oracle queues. |
| promote | antigravity_round31_extra_astronomical_edge_cases_polar_regions_2026_06_26.md | Polar and astronomical edge cases affect correctness and confidence boundaries. |
| reference-only | antigravity_round31_extra_internationalization_i18n_readiness_2026_06_26.md | Product-localization idea; not a current strict accuracy front. |
| reference-only | antigravity_round31_extra_offline_fallback_mode_2026_06_26.md | Frontend resilience idea; keep outside current engine-truth work. |
| reference-only | antigravity_round31_extra_performance_profiling_memory_leaks_2026_06_26.md | Performance background; only promote after API payload profiling is reopened. |
| archive | antigravity_round31_final_execution_board_2026_06_26.md | Round board superseded by current active fronts. |
| reference-only | antigravity_round31_frontend_completion_top50_2026_06_26.md | UI exposure backlog, not current runtime truth. |
| promote | antigravity_round31_jhora_pyjhora_capture_manual_review_2026_06_26.md | Human oracle capture standards belong with benchmark and operator docs. |
| promote | antigravity_round31_license_quarantine_blacklist_top60_2026_06_26.md | License quarantine rules are project safety boundaries and should stay canonical. |
| promote | antigravity_round31_local_accuracy_shortest_path_top50_2026_06_26.md | Local accuracy verification path supports regression confidence and user trust. |
| reference-only | antigravity_round31_local_user_experience_top60_2026_06_26.md | UX backlog; not a main-chain source of truth. |
| promote | antigravity_round31_single_source_of_truth_enforcement_2026_06_26.md | Single-source governance supports the current mirror-contamination fix. |
| promote | antigravity_round31_true_missing_traditional_techniques_top30_2026_06_26.md | Traditional technique gap list should inform registry and roadmap truth. |
| promote | antigravity_round31_whole_machine_fragment_reuse_fourth_pass_2026_06_26.md | Whole-machine reuse findings are high value, but must be re-anchored before integration. |
| reference-only | antigravity_round32_api_direct_coding_top40_2026_06_26.md | Concrete API tasks, but must be reconciled with current endpoint map first. |
| reference-only | antigravity_round32_cli_direct_coding_top40_2026_06_26.md | Concrete CLI tasks, but no longer authoritative without current test review. |
| archive | antigravity_round32_codex_round33_top200_2026_06_26.md | Broad execution board superseded by current closure lanes. |
| promote | antigravity_round32_copy_allowed_assets_top100_2026_06_26.md | License-safe assets list should merge with canonical reuse whitelist. |
| reference-only | antigravity_round32_extra_accuracy_verification_blocks_2026_06_26.md | Trust-center idea; promote only if product verification UI is reopened. |
| reference-only | antigravity_round32_extra_i18n_translation_2026_06_26.md | Localization backlog, not current strict workflow. |
| reference-only | antigravity_round32_extra_offline_fallback_2026_06_26.md | Offline/PWA idea; reference only until frontend resilience is prioritized. |
| reference-only | antigravity_round32_extra_payload_performance_2026_06_26.md | Performance backlog; useful when API payload slimming resumes. |
| archive | antigravity_round32_final_execution_board_2026_06_26.md | Superseded round board. |
| reference-only | antigravity_round32_frontend_direct_coding_top40_2026_06_26.md | UI backlog; not canonical runtime map. |
| promote | antigravity_round32_jhora_pyjhora_fast_capture_pipeline_2026_06_26.md | Capture pipeline can reduce oracle bottlenecks and should feed operator docs. |
| promote | antigravity_round32_license_blacklist_recheck_2026_06_26.md | GPL/AGPL isolation remains a hard boundary. |
| promote | antigravity_round32_local_accuracy_shortest_chain_final_2026_06_26.md | Accuracy shortest chain should connect to benchmark and preflight gates. |
| reference-only | antigravity_round32_local_ux_direct_top30_2026_06_26.md | UX backlog only. |
| promote | antigravity_round32_oracle_sample_push_matrix_2026_06_26.md | Oracle sample matrix belongs in benchmark planning. |
| reference-only | antigravity_round32_sync_script_blueprint_2026_06_26.md | Sync script idea; keep constrained by no reverse `.workbuddy` authority. |
| promote | antigravity_round32_timezone_dst_polar_direct_tasks_2026_06_26.md | Timezone, DST and polar handling affect chart correctness. |
| promote | antigravity_round32_true_missing_techniques_rerank_top20_2026_06_26.md | Technique gap rerank should feed registry and roadmap. |
| promote | antigravity_round32_whole_machine_fragment_reuse_fifth_pass_2026_06_26.md | Fragment reuse findings are useful after license/source re-anchoring. |
| promote | antigravity_round36_asc_degree_yogi_tight_orb_wealth_pack_2026_06_26.md | Wealth-specific Yogi/tight-orb material supports strict finance adjudication. |
| promote | antigravity_round36_bhrigu_pada_all_event_expansion_pack_2026_06_26.md | Event expansion material is relevant to historical backtest and timing routes. |
| promote | antigravity_round36_global_first_honesty_board_2026_06_26.md | Honesty boundary belongs near oracle and benchmark governance. |
| reference-only | antigravity_round36_pakshi_swara_boundary_pack_2026_06_26.md | Advanced traditional technique background; not current route-critical. |
| reference-only | antigravity_round36_rtn_anomalous_d9_deepening_pack_2026_06_26.md | Niche D9 deepening background; promote only with current evidence. |
| promote | antigravity_round36_tajika_sahams_external_closure_pack_2026_06_26.md | Tajika/Saham external closure is an active benchmark frontier. |
| reference-only | antigravity_round36_tithi_lord_freeze_gap_pack_2026_06_26.md | Technique detail backlog; not current main-chain blocker. |
| reference-only | antigravity_round37_article_template_industrialization_board_2026_06_26.md | Interpretation template backlog; useful after truth arbitration. |
| archive | antigravity_round37_codex_round38_top100_2026_06_26.md | Execution board superseded by later focused documents. |
| promote | antigravity_round37_dasha_external_oracle_shortest_closure_board_2026_06_26.md | Dasha external closure is a high-rigor requirement. |
| promote | antigravity_round37_public_benchmark_moat_board_2026_06_26.md | Public benchmark strategy should inform benchmark dashboard governance. |
| promote | antigravity_round37_shadbala_absolute_value_frontier_board_2026_06_26.md | Shadbala absolute values remain a precision frontier. |
| promote | antigravity_round37_tajika_sahams_annual_closure_board_2026_06_26.md | Annual chart closure aligns with current Tajika oracle work. |
| reference-only | antigravity_round38_advanced_sensitive_points_top20_2026_06_26.md | Advanced sensitive points backlog; not current strict route source. |
| reference-only | antigravity_round38_article_detail_template_batch2_2026_06_26.md | Template backlog; keep behind truth arbitration. |
| archive | antigravity_round38_codex_round39_top150_2026_06_26.md | Execution board superseded by current active fronts. |
| promote | antigravity_round38_dasha_external_oracle_packet_factory_2026_06_26.md | Dasha oracle packet factory should feed operator packet docs/tests. |
| reference-only | antigravity_round38_mrityu_bhaga_authority_table_hunt_2026_06_26.md | Authority-table research, but not active route-critical. |
| promote | antigravity_round38_open_source_copy_whitelist_sensitive_points_2026_06_26.md | License-safe sensitive-point whitelist should be reconciled before reuse. |
| promote | antigravity_round38_public_benchmark_board_v2_2026_06_26.md | Benchmark dashboard v2 should be promoted if public benchmark work resumes. |
| promote | antigravity_round38_shadbala_absolute_value_capture_matrix_2026_06_26.md | Shadbala absolute capture matrix belongs with oracle closure planning. |
| promote | antigravity_round38_skill_global_rank_gap_after_round38_2026_06_26.md | Global gap assessment informs honest capability claims. |
| promote | antigravity_round38_whole_machine_fragment_reuse_sixth_pass_2026_06_26.md | Fragment reuse shortlist needs canonical anchoring. |
| promote | antigravity_round39_yogi_wealth_bridge_audit_2026_06_28.md | Directly relevant to current wealth strict adjudication. |
| promote | antigravity_round40_article_technique_truth_arbitration_2026_06_27.md | Truth arbitration prevents noisy article-derived code migration. |
| archive | antigravity_round40_codex_round41_skill_top60_2026_06_27.md | Round-specific action board, not canonical truth. |
| promote | antigravity_round40_dasha_second_wave_closure_pack_2026_06_27.md | Dasha second-wave closure supports high-rigor timing validation. |
| promote | antigravity_round40_shadbala_absolute_authority_ladder_2026_06_27.md | Shadbala authority ladder belongs with precision/oracle governance. |
| promote | antigravity_round40_tajika_annual_second_wave_board_2026_06_27.md | Tajika second-wave board supports annual oracle closure. |
| promote | antigravity_round40_whole_machine_fragment_reuse_shortlist_2026_06_27.md | Top 20 fragment shortlist should be re-anchored to current code/tests. |
| archive | antigravity_sidecar_work_order_round33_2026_06_26.md | Sidecar work order; historical coordination only. |
| archive | antigravity_sidecar_work_order_round34_2026_06_26.md | Sidecar work order; historical coordination only. |
| archive | antigravity_sidecar_work_order_round35_2026_06_26.md | Sidecar work order; historical coordination only. |
| archive | antigravity_sidecar_work_order_round36_2026_06_26.md | Sidecar work order; historical coordination only. |
| archive | antigravity_sidecar_work_order_round37_2026_06_26.md | Sidecar work order; historical coordination only. |
| archive | antigravity_sidecar_work_order_round40_2026_06_27.md | Sidecar work order; historical coordination only. |
| promote | article_technique_coverage_matrix_2026_06_26.md | Article-to-technique coverage matrix should remain a canonical truth-arbitration input. |
| reference-only | chayue_screenshot_coverage_matrix_2026_06_26.md | Source-specific screenshot coverage; useful as evidence only. |
| reference-only | cloud_sync_minimum_whitelist_for_skill_truth_2026_06_26.md | Sync governance background; no reverse authority over main repo. |
| promote | current_skill_core_gap_rerank_2026_06_26.md | Current skill gap rerank should feed active roadmap and registry work. |
| promote | dasha_accuracy_closure_status_2026_06_26.md | Dasha closure status is a high-rigor timing boundary. |
| promote | dasha_code_only_priority_rerank_2026_06_26.md | Code-only Dasha prioritization can guide scoped local improvements. |
| promote | five_hard_fronts_master_board_2026_06_26.md | Five-front board is the best compact strategic index for precision gaps. |
| archive | git_execution_card_skill_truth_only_2026_06_26.md | One-off git execution card; no ongoing truth role. |
| promote | global_open_source_positioning_of_skill_2026_06_26.md | Honest positioning is required for claims and benchmark framing. |
| promote | high_granularity_technique_deepening_backlog_2026_06_26.md | Technique deepening backlog should be reconciled with the registry. |
| promote | jhora_capture_task_v2.md | Human oracle capture task should connect to benchmark packets. |
| reference-only | recovered_old_skill_reuse_audit_2026_06_26.md | Recovery audit; reuse only after current-code and license recheck. |
| promote | reuse_license_whitelist_for_skill_2026_06_26.md | Reuse license whitelist should be canonical before any migration. |
| promote | skill_fragment_map_and_source_of_truth_2026_06_26.md | Source-of-truth map supports mirror and fragment discipline. |
| promote | skill_single_source_of_truth_disposition_2026_06_26.md | Single-source disposition remains a governance anchor. |
| promote | skill_truth_conflict_matrix_2026_06_26.md | Conflict matrix should inform future source-truth decisions. |
| promote | three_fronts_skill_depth_audit_2026_06_26.md | Three-front depth audit is compact and still relevant to skill depth. |
| reference-only | zhanxingyindu1_screenshot_coverage_matrix_2026_06_26.md | Source-specific screenshot coverage; useful as evidence only. |

## Immediate Next Use

When a future task needs one of these drafts, first copy the claim into a canonical target and verify it against current code/tests. Never import code or truth from `.workbuddy` or local drafts directly into the runtime chain.
