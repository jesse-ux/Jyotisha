# 印度占星产品化进度日志

## 2026-06-30

- 完成 VedAstro 官方事件层的“日窗口优先”第一轮落地：`scripts/vedastro_service_adapter.py` 现会从 allowlisted `evidence_ledger` 派生 `daily_windows` 与 `top_daily_window`，不再只停留在原始事件行。
- `scripts/vedastro_evidence_orchestrator.py` 已透传：
  - `daily_windows_by_domain`
  - `top_daily_window_by_domain`
- `mcp_server.py` 的 strict workflow `present_evidence.external_activation` 已可直接消费：
  - `daily_windows`
  - `top_daily_window`
- `life_event_graph_v1` 已新增 `official_day_window` 节点，前端/问答后续不必重解析原始事件就能看见官方日窗口。
- `scripts/jyotish_engine.py` 的 full-reading overview 汇总层已补齐：
  - `daily_windows`
  - `top_daily_window`
  - `daily_windows_by_domain`
  - `top_daily_window_by_domain`
- 新增/更新的 focused verification：
  - `python3 -m pytest tests/test_vedastro_range_scan_replay.py::test_range_scan_builds_ranked_daily_windows_from_same_day_events -q`
  - `python3 -m pytest tests/test_vedastro_evidence_orchestrator.py::test_vedastro_orchestrator_surfaces_daily_windows_by_domain -q`
  - `python3 -m pytest tests/test_mcp_strict_workflow_relationship.py::test_relationship_external_activation_exposes_top_daily_window -q`
  - `python3 -m pytest tests/test_life_event_graph_v1.py::test_life_event_graph_surfaces_ranked_official_day_window_nodes -q`
  - `python3 -m pytest tests/test_cli_smoke.py::test_full_reading_preserves_official_daily_window_fields_in_range_scan_result -q`
  - 组合回归：以上 5 个测试同跑通过
- 真实边界：
  - 这轮完成的是“官方事件 -> 日窗口派生 -> strict workflow/graph/full-reading透传”。
  - 还没完成的是把 day-window 再继续升级成“高质量事业/婚恋/财富日级裁决器”；目前窗口质量仍依赖 `SearchEvents` 实际返回与 allowlist/tag/alias 覆盖质量。

- 完成 guided topic -> AI chat 上下文链路补强：`jyotish-app/main.js` 点击 guided topic 时会把整条 topic 作为 `guided_topic_context` 传给 `openAIChatWithPrompt()`，`jyotish-app/ai-chat.js` 会把这层上下文继续拼进 `chart_context`，并在后端 `/api/chat` 请求体中透传 `guided_topic_context`。
- 这意味着 guided topic 后续追问不再只带自然语言问题，还会继续携带：
  - `strict_audit_gate.functional_benefic_malefic`
  - `strict_audit_gate.relevant_vargas`
  - `strict_audit_gate.vimshottari_narayana_crosscheck`
  - `strict_audit_gate.source_priority_boundary`
- 新增/更新的 focused verification：
  - `python3 -m pytest tests/test_frontend_productization.py::test_guided_topic_questions_reuse_ai_chat_entry -q`
  - `python3 -m pytest tests/test_frontend_productization.py::test_complete_reading_surfaces_guided_topic_discovery tests/test_frontend_productization.py::test_guided_topic_questions_reuse_ai_chat_entry -q`
- 真实边界：
  - 这轮完成的是 guided topic 点击后的上下文透传，不是服务端 `/api/chat` 自己再基于 `guided_topic_context` 做专门的二次路由。

- 完成 `guided_topics` 逐条结论压入 compact audit gate：`scripts/guided_topic_discovery.py` 现会从现有 strict contract 读取 `technique_audit_summary`，并把它作为 `strict_audit_gate` 挂到每一条 guided topic 上。
- 这层 `strict_audit_gate` 目前已覆盖：
  - `functional_benefic_malefic`
  - `relevant_vargas`
  - `vimshottari_narayana_crosscheck`
  - `source_priority_boundary`
- 前端 `jyotish-app/main.js` 的 guided topic 卡片现已消费 `strict_audit_gate`，会在“继续深入”卡片上显示：
  - functional gate
  - varga gate
  - dual dasha gate
- 新增/更新的 focused verification：
  - `python3 -m pytest tests/test_cli_smoke.py::test_full_reading_generates_guided_topics_from_real_evidence -q`
  - `python3 -m pytest tests/test_frontend_productization.py::test_complete_reading_surfaces_guided_topic_discovery -q`
- 真实边界：
  - 这轮是把 compact audit gate 压进 guided topics 逐条对象与前端卡片。
  - 还没做的是把同层 gate 再继续压进 guided topic 触发的后续问答 payload，让每次点击追问时也自动携带这层 compact boundary。

- 完成 `Technique Audit Table -> strict adjudication` 设计文档落库：`docs/superpowers/specs/2026-06-30-technique-audit-strict-adjudication-design.md`，明确现成审计表不再只是平行证据，而是默认事业/婚恋/财富结论的强制引用门槛。
- 完成对应实现计划落库：`docs/superpowers/plans/2026-06-30-technique-audit-strict-adjudication.md`，约束为复用现有 strict workflow、prompt pack、API summary 和前端消费层，不新增第二套审计系统。
- `mcp_server.py` 已新增 compact strict audit gate：
  - `_route_varga_gate_keys`
  - `_build_technique_audit_summary`
  - `strict["technique_audit_summary"]`
  - `multi_reference_reading_summary["audit_gate_frame"]`
- compact strict audit gate 现强制覆盖 4 类默认裁决依据：
  - `Functional Benefic/Malefic`
  - `D1 + 对应分盘门槛`
  - `Vimshottari + Narayana`
  - `official / local / fallback / blocked / conflicts`
- `scripts/jyotish_engine.py` 已把 `technique_audit_summary` 透传进 compact strict contract，并把以下字段直接抬到 `ai_prompt_pack.evidence_snapshot` 顶层，减少 skill / Codex / 网页端消费路径复杂度：
  - `strict_workflow_primary_route`
  - `strict_workflow_routes_available`
  - `strict_workflow_contracts`
  - `official_primary_evidence`
  - `local_supplemental_evidence`
  - `fallback_used`
  - `blocked_items`
  - `conflicts`
- `scripts/jyotish_api_server.py::_high_rigor_vedastro_official_summary()` 现已透传 `technique_audit_summary`，高严谨摘要与 consultation 工作流不再只给 top-reader skeleton，也会同步给出 compact audit gate。
- 前端 `jyotish-app/main.js` 与 `jyotish-app/ai-chat.js` 已消费 `technique_audit_summary`：
  - Prompt Pack 合同卡会显示 functional gate / varga gate / dual dasha gate
  - AI Chat `【Top Reader Contract】` 上下文会显式写出 `technique_audit_summary` 的关键门槛状态
- 新增/更新的红绿测试：
  - `tests/test_mcp_strict_workflow_career.py::test_career_strict_contract_exposes_compact_technique_audit_summary`
  - `tests/test_mcp_strict_workflow_relationship.py::test_relationship_multi_reference_summary_carries_audit_gate_frame`
  - `tests/test_mcp_strict_workflow_finance.py::test_finance_strict_contract_compact_audit_marks_dual_dasha_gate`
  - `tests/test_cli_smoke.py::test_full_reading_prompt_pack_carries_compact_technique_audit_summary`
  - `tests/test_api_server_security.py::test_high_rigor_vedastro_official_summary_exposes_top_reader_contract_from_full_snapshot`
  - `tests/test_api_server_security.py::test_consultation_workflow_surfaces_top_reader_contract_in_official_summary`
  - `tests/test_frontend_productization.py::test_frontend_consumes_top_reader_contract_in_prompt_pack_and_ai_chat`
- 已确认通过的 focused verification：
  - `python3 -m pytest tests/test_mcp_strict_workflow_career.py tests/test_mcp_strict_workflow_relationship.py tests/test_mcp_strict_workflow_finance.py -k "compact_technique_audit_summary or audit_gate_frame or dual_dasha_gate" -q`
  - `python3 -m pytest tests/test_cli_smoke.py -k "compact_technique_audit_summary" -q`
  - `python3 -m pytest tests/test_api_server_security.py::test_high_rigor_vedastro_official_summary_exposes_top_reader_contract_from_full_snapshot tests/test_api_server_security.py::test_consultation_workflow_surfaces_top_reader_contract_in_official_summary tests/test_frontend_productization.py::test_frontend_consumes_top_reader_contract_in_prompt_pack_and_ai_chat -q`
- 真实边界：
  - 这轮完成的是“现成审计表正式并入默认 strict adjudication 主裁决”。
  - 还没完成的是把这份 compact audit gate 进一步压进 guided topic 级逐条结论对象，让每条主题建议也自带同层门槛摘要。

- 完成 `chart async + unified stage contract` 设计文档落库：`docs/superpowers/specs/2026-06-30-chart-async-unified-stage-contract-design.md`，明确普通 `/api/chart` 也可选走轻量 `job_id + poll`，以及 `full-reading` 在现有阶段耗时之上补一层统一 stage contract。
- 完成对应实现计划落库：`docs/superpowers/plans/2026-06-30-chart-async-unified-stage-contract.md`，约束为复用现有 high-rigor 文件队列、不新增 Redis/Celery、不改变同步默认行为。
- `scripts/jyotish_engine.py` 已新增 `_build_unified_stage_contract(stage_timings)`，并把以下字段压入 `full-reading.summary`：
  - `stage_contract_version`
  - `stage_groups`
  - `cache_recommendations`
  - `async_recommendations`
- `scripts/jyotish_api_server.py` 已抽出共享异步作业层：
  - `_async_job_dir`
  - `_async_job_path`
  - `_load_async_job_record`
  - `_write_async_job_record`
  - `ChartAPIHandler._enqueue_async_job`
- `scripts/jyotish_api_server.py` 已为普通排盘主链补上可选异步出口：
  - `POST /api/chart` 支持 `async=true` / `enqueue=true`
  - 新增 `/api/chart/jobs/{job_id}` poll
  - 同步 `_compute_chart_sync` 仍保持原行为，完成态异步结果与同步 chart payload 对齐
- 为兼容既有 monkeypatch 测试与主链，high-rigor async wrapper 保持原接口：
  - `_enqueue_high_rigor_job`
  - `_get_high_rigor_job`
  - `_load_high_rigor_job_record`
  - `_write_high_rigor_job_record`
- 新增/更新的红绿测试：
  - `tests/test_cli_smoke.py::test_full_reading_summary_exposes_unified_stage_groups`
  - `tests/test_api_server_security.py::test_chart_async_submit_returns_job_id`
  - `tests/test_api_server_security.py::test_chart_job_poll_endpoint_returns_cached_job_payload`
  - `tests/test_api_server_security.py::test_chart_async_job_executes_in_background`
- 已确认通过的 focused verification：
  - `python3 -m pytest tests/test_cli_smoke.py::test_full_reading_summary_exposes_unified_stage_groups -q`
  - `python3 -m pytest tests/test_api_server_security.py -k "chart_async_submit_returns_job_id or chart_job_poll_endpoint_returns_cached_job_payload or chart_async_job_executes_in_background" -q`
  - `python3 -m pytest tests/test_api_server_security.py -k "high_rigor_async_submit_returns_job_id or high_rigor_job_poll_endpoint_returns_cached_job_payload or high_rigor_async_job_executes_in_background" -q`
  - `python3 -m pytest tests/test_api_server_security.py -k "chart_async or high_rigor_async or chart_job_poll_endpoint_returns_cached_job_payload or runtime_cache" -q`
- 真实边界：
  - 这轮完成的是普通 chart / full-reading 的统一异步出口和阶段契约压实。
  - 还没完成的是把这层继续完整前推到前端极简交互与更大一圈慢回归基线。

- 完成 `VedAstro official -> local supplemental -> local fallback` 设计文档落库：`docs/superpowers/specs/2026-06-30-vedastro-official-hard-override-design.md`，明确婚恋/事业/财富三条默认工作流的官方优先、冲突暴露、`blocked` 和 `confidence_cap` 规则。
- 完成对应实现计划落库：`docs/superpowers/plans/2026-06-30-vedastro-official-hard-override.md`，按 TDD 拆成 strict contract、orchestrator metadata、API/report 出口和验证四段。
- `mcp_server.py` 已为 `relationship / career / finance` 三条 strict workflow 增加共享 contract：
  - `official_primary_evidence`
  - `local_supplemental_evidence`
  - `fallback_used`
  - `blocked_items`
  - `conflicts`
- `mcp_server.py` 新增共享 helper，避免三条主题各自偷偷拼 contract：
  - `_build_official_primary_evidence`
  - `_build_local_supplemental_evidence`
  - `_build_fallback_and_blocked`
  - `_build_conflicts`
- `scripts/historical_event_backtest.py` 已透传 strict contract 的 `blocked_items` 与 `conflicts`，历史回测链不再只看到 `source_priority_mode/confidence_cap`。
- `scripts/vedastro_evidence_orchestrator.py` 已把 `official_section_statuses` 与 `theme_requirements` 推入 `source_metadata`，为后续官方硬覆盖裁决提供统一 metadata。
- `scripts/jyotish_api_server.py` 的 `high_rigor_workflow_plan_only` 已改为返回 `return_official_primary_supplemental_fallback_conflict_contract`，并在 plan-only 输出中显式声明这套 contract。
- `scripts/jyotish_api_server.py::_high_rigor_vedastro_official_summary` 已透传：
  - `official_primary_evidence`
  - `local_supplemental_evidence`
  - `fallback_used`
  - `blocked_items`
  - `conflicts`
- `scripts/jyotish_engine.py::_build_vedastro_official_full_snapshot_payload` 已开始把 relationship strict contract 折叠进 `ai_prompt_pack.evidence_snapshot.vedastro_official_full_snapshot`，让 prompt/网页/AI 上下文看到官方主证据、补充、回退和冲突边界，而不只看到快照状态。
- 新增/更新的红绿测试：
  - `tests/test_mcp_strict_workflow_relationship.py`
  - `tests/test_mcp_strict_workflow_career.py`
  - `tests/test_mcp_strict_workflow_finance.py`
  - `tests/test_historical_event_backtest.py`
  - `tests/test_vedastro_evidence_orchestrator.py`
  - `tests/test_api_server_security.py`
  - `tests/test_cli_smoke.py`
- 已确认通过的 focused verification：
  - `python3 -m pytest tests/test_mcp_strict_workflow_relationship.py tests/test_mcp_strict_workflow_career.py tests/test_mcp_strict_workflow_finance.py tests/test_historical_event_backtest.py -k "strict_contract or conflicts_and_blocked_items" -q`
  - `python3 -m pytest tests/test_vedastro_evidence_orchestrator.py -k official_section_statuses -q`
  - `python3 -m pytest tests/test_api_server_security.py -k "hard_override_contract or vedastro_official_summary_passes_through_contract_fields" -q`
- 真实边界：
  - 这轮已把“官方硬覆盖 contract”压实到 strict workflow、historical backtest、orchestrator metadata 和高严谨 API summary。
  - 还未完成的收尾是把同一 contract 更完整地消费到 full-reading / prompt pack / 前端展示层，并跑完更大一圈的慢回归验证。

## 2026-06-22

- 恢复上下文：项目根目录此前没有 `task_plan.md`、`findings.md`、`progress.md`。
- 读取了 `planning-with-files-zh` 技能说明，按复杂任务要求建立磁盘工作记忆。
- 检查了 `docs/research/product_gap_matrix_2026_06_22.md`，当前最高优先级为 richer Panchanga festival rules 和 search-by-condition。
- 网络扫描 GitHub：确认 VedAstro、VedAstro.Python、kunjara/jyotish、panchanga_api、jyotidarshan 等仍是 Panchanga/Muhurta 同类对标对象。
- 完成 Panchanga richer rules：`scripts/muhurta.py` 增加保守 vrata/festival-candidate 标签和 `condition_tags`。
- 完成前端条件检索：`jyotish-app/main.js` 增加 `PANCHANGA_CONDITIONS`、`panchanga-condition`、行过滤、条件徽章、CSV/ICS 条件标签。
- 完成样式与测试：`jyotish-app/style.css` 增加 `.panchanga-condition-chip`；`tests/test_muhurta.py`、`tests/test_api_server_security.py`、`tests/test_frontend_productization.py` 增加覆盖。
- 验证：`python3 -m pytest tests/test_muhurta.py tests/test_api_server_security.py tests/test_frontend_productization.py -q` 通过。
- 验证：`npm run build` 通过；`python3 scripts/audit_fragments.py --strict` 通过，65 registry / 37 commands / 32 API endpoints / 42 frontend files，0 problems。
- 完成多人/家庭案例工作区 MVP：`jyotish-app/main.js` 增加 `CASE_GROUP_PRESETS`、`CASE_RELATION_PRESETS`、元数据归一化、统一 chart/pair/prashna 列表、group/relation 筛选、星盘打开、三类记录批量导出/删除。
- 完成样式与测试：`jyotish-app/style.css` 增加 `.case-meta-line`；`tests/test_frontend_productization.py` 增加案例分组/关系 token。
- 验证：`python3 -m pytest tests/test_frontend_productization.py -q` 通过；`npm run build` 通过。
- 网络扫描合盘/匹配开源：`ashtakoot kundli matching` 与 `jyotish matchmaking python` 无高价值直接结果；`vedic astrology compatibility matching` 命中 VedAstro MCP、dashaflow、Cosmic Harmony Match、MyRashifal 等，其中可复用内核仍以本地 `dashaflow` MIT 为准。
- 完成关系报告模板：`jyotish-app/main.js` 增加 `buildRelationshipReportTemplate`、`renderRelationshipReport`，保存配对记录、复盘、当前工作流与 HTML 导出都携带 `relationshipReport`/`relationship_report`。
- 完成 bi-wheel/composite-style 比较视图：新增双人轴线、行星 overlay 宫位、星座关系 tone、Sun/Moon/Venus/Mars midpoint；完整合盘深度区会渲染 `renderBiWheelComparisonView`。
- 完成样式与测试：`jyotish-app/style.css` 增加 `.relationship-report-*`、`.biwheel-*`、`.composite-style-strip`；`tests/test_frontend_productization.py` 增加关系报告和比较视图 token。
- 验证：`python3 -m pytest tests/test_frontend_productization.py -q` 通过；`npm run build` 通过，仅保留既有 Vite chunk size warning。
- 完成 `spouse_status_yoga.py` 关系折叠：`scripts/jyotish_api_server.py` 的 `/api/relationship` 返回 `spouse_status_yoga`；`jyotish-app/main.js` 增加 `buildSynastrySpouseStatusContext`、`renderSpouseStatusComparison`、保存复盘归一化和关系报告证据；`jyotish-app/export.js` 在 HTML 报告中输出 spouse-status 表。
- 完成样式与测试：`jyotish-app/style.css` 增加 `.spouse-status-*`；`tests/test_api_server_security.py` 增加 relationship fragment 测试；`tests/test_frontend_productization.py` 增加 spouse-status token。
- 验证：`python3 -m pytest tests/test_api_server_security.py tests/test_frontend_productization.py -q` 通过；`npm run build` 通过，仅保留既有 Vite chunk size warning。
- 完成关系报告打印 polish：`jyotish-app/export.js` 的合盘 HTML 报告升级为 `relationship-deliverable`，包含结论 hero、证据卡、bi-wheel 轴线、overlay 表、midpoint、spouse-status、行动列表和边界说明，并增加 print break-inside 规则。
- 完成测试：`tests/test_frontend_productization.py` 增加 relationship deliverable/export token。
- 验证：`python3 -m pytest tests/test_frontend_productization.py -q` 通过；`npm run build` 通过，仅保留既有 Vite chunk size warning。
- 完成可编辑关系元数据：`jyotish-app/main.js` 的统一案例工作区增加 `workspace-edit-case`，支持编辑 chart/pair/prashna 标题、分组、关系类型和标签，并通过 `applyWorkspaceCaseMetadata` 归一化后写回原本地库。
- 完成测试：`tests/test_frontend_productization.py` 增加 metadata editing token。
- 验证：`python3 -m pytest tests/test_frontend_productization.py -q` 通过；`npm run build` 通过，仅保留既有 Vite chunk size warning。

## 2026-06-23

- 本地/网络报告管线复核：外部 GitHub 命中的 Vedic report/PDF 项目大多是无许可证仓库、API SDK、产品壳或 notebook；决定复用本地 `vedic-astro-skills` 来源的 `scripts/report_builder.py`。
- 完成后端报告 artifact/PDF 管线：`scripts/jyotish_api_server.py` 新增 `/api/report_artifact`，限制 HTML 体积，阻断 script/iframe/object/embed/on* 事件属性和 `javascript:` URL，写入 `/private/tmp/jyotish-reports`，并调用 `report_builder._html_to_pdf` 生成 PDF。
- 完成安全降级：Playwright/Chromium 不可用时 API 返回后端生成 HTML 工件、`html_base64` 和 fallback 状态，不让导出流程空失败。
- 完成前端 PDF 导出：`jyotish-app/api-bridge.js` 暴露 `generateReportArtifact`；`jyotish-app/export.js` 新增 `exportPDFReport` 和 `downloadBase64File`；`jyotish-app/index.html` 导出菜单新增 PDF；`jyotish-app/main.js` 懒加载导出分支支持 `data-format="pdf"`。
- 完成测试与审计：`python3 -m pytest tests/test_api_server_security.py tests/test_frontend_productization.py -q` 通过；`python3 scripts/audit_fragments.py --strict` 通过，65 registry / 37 commands / 33 API endpoints / 42 frontend files，0 problems；`npm run build` 通过。
- 完成关系时机/UL-DK 折叠：前端完整合盘上下文新增 `ulDkTiming`，聚合 7星制/8星制 DK、UL、当前 Dasha 与 7宫主/关系自然征象触发；当前合盘、保存配对回放、关系报告模板都能展示“UL/DK 与关系时机”证据卡。
- 完成后端关系时机补强：`/api/relationship` 新增 `relationship_timing`，复用 `darakaraka_reader.py` 与 `jaimini.py`，并返回 `darakaraka_reader.py`/`jaimini.py` fragment source；HTML/PDF 合盘报告新增 `uldk-print-grid`。
- 完成导出体验 polish：导出菜单新增 `aria-live` 状态区，导出期间禁用按钮/菜单项，PDF 回退以可见状态反馈提示，避免重复点击和“点了没反应”。
- 完成构建体积优化：`export.js` 改为动态导入，`vite.config.js` 将 reference/audit chunks 拆分；生产构建主 JS 保持在约 356K。
- 验证：`python3 -m pytest tests/test_frontend_productization.py tests/test_api_server_security.py -q` 通过；`npm run build` 通过；`git diff --check` 通过。
- 完成 Panchanga 搜索增强：条件筛选从单选升级为多选组合，支持 `has_vrata`、`festival_candidate`、`spiritual_practice`、`auspicious_activity`、`avoid_new_start`、`good_choghadiya` 的 AND 组合筛选，并在结果上方展示条件说明；CSV/ICS 继续使用筛选后的日期。
- 完成 Panchanga search/details 补强：后端返回 `search_summary` 和逐日 `festival_details`；前端新增“满足全部/满足任一”模式、节日说明卡和 location-aware 坐标/时区摘要。
- 验证：`python3 -m pytest tests/test_frontend_productization.py tests/test_api_server_security.py tests/test_muhurta.py -q` 通过；`npm run build` 通过；`git diff --check` 通过。
- 额外验证：`python3 scripts/audit_fragments.py --strict` 通过。
- 完成计算设置选择器：参数/日历中心新增 Calculation Settings 面板，支持保存 ayanamsa、node、house、sunrise、geocoder 策略到 localStorage；排盘请求会携带策略字段，星盘对象、provenance、JSON/HTML 导出都会记录这些设置。
- 约束说明：当前核心排盘仍以 Lahiri / Mean Node / Whole Sign 为主路径，Raman/KP/True node 等先作为策略记录与后续统一引擎切换入口，避免 UI 假装已改变底层黄经。
- 验证：`python3 -m pytest tests/test_frontend_productization.py tests/test_api_server_security.py tests/test_muhurta.py -q` 通过；`npm run build` 通过；`git diff --check` 通过。
- 完成规则/技法检索目录与 API Explorer：`scripts/jyotish_api_server.py` 新增 `/api/technique_catalog` 和白名单 `/api/technique_example`；`jyotish-app/api-bridge.js`/`public/api-bridge.js` 暴露 `getTechniqueCatalog`、`runTechniqueExample`；`jyotish-app/skill-map.js` 的目录卡片可携带 endpoint，用当前星盘生成 payload 并试算 API，保留 workbench fallback。
- 完成样式与测试：`jyotish-app/style.css` 补 Explorer call/sample 样式；`tests/test_api_server_security.py` 验证 catalog/runnable examples；`tests/test_frontend_productization.py` 验证 bridge、目录、payload builder、endpoint/action 映射。
- 验证：`python3 -m pytest tests/test_api_server_security.py tests/test_frontend_productization.py tests/test_muhurta.py -q` 通过；`npm run build` 通过；`python3 scripts/audit_fragments.py --strict` 通过，65 registry / 37 commands / 35 API endpoints / 42 frontend files，0 problems。
- 当前下一最高优先级：规则变体/流派 toggles 与候选碎片归档。
- 完成规则变体/流派 toggles 可见化：Calculation Settings 新增 Yoga、Jaimini Karaka、KP significator、Ashtakavarga、Shadbala、Dasha reference 六类 Rule Variants；保存后进入排盘 payload、星盘对象 provenance、JSON/HTML/PDF 导出。
- 约束说明：Rule Variants 当前作为解释口径和导出审计记录；非当前选项标注为 staged，后续逐项接入实时算法切换，避免 UI 假装已经改变底层判断。
- 验证：`python3 -m pytest tests/test_frontend_productization.py tests/test_api_server_security.py tests/test_muhurta.py -q` 通过；`npm run build` 通过；`git diff --check` 通过；`python3 scripts/audit_fragments.py --strict` 通过，候选碎片从 8 个降至 6 个。
- 当前下一最高优先级：继续分流 `dasha_analyzer.py`、`reading_orchestrator.py`、`report_orchestrator.py`、`orchestrator_bridge.py`、`hermes_bridge.py`、`mevg_automation.py`。
- 完成 Yoga/Shadbala 规则碎片真实接入：`/api/yogas` 复用 `curse_yoga_detector.py` 返回 `curse_yogas`、`curse_count`、风险等级与规则口径；`/api/shadbala` 复用 `shadbala_advanced.py` 返回 `advanced_layer`、Kala VMDH、Yuddha Bala、Sputa Drishti 与规则口径。
- 完成前端 Explorer 渲染：`jyotish-app/skill-map.js` 新增 Shadbala/Yoga 专属结果卡，显示规则来源、凶星合相风险、Kala/Yuddha/Sputa 摘要和下一步边界提示。
- 修复碎片警告：移除 `shadbala_advanced.py` 中未使用且会触发 SwissEph 属性警告的日出调用，保持轻量 Hora 近似与主 Shadbala 一致。
- 验证：`python3 -m pytest tests/test_api_server_security.py tests/test_frontend_productization.py tests/test_muhurta.py -q` 通过；`npm run build` 通过；`python3 scripts/audit_fragments.py --strict` 通过，0 problems，候选碎片保持 6 个。
- 当前下一最高优先级：把 `dasha_analyzer.py` 决定为 API/报告 Dasha 叙事接入或归档；随后处理 report/reading orchestrator 与 bridge/automation 类碎片。
- 完成 Dasha 候选碎片接入：`/api/dasha` 在 Vimshottari 模式下新增 `vimshottari_analysis`，复用 `dasha_analyzer.py` 的真实 Mahadasha 起点、当前 Antardasha 计算，并结合 `dasha_calculator_enhanced.py` 输出五级层级；主 `periods` 合同保持不变。
- 完成 Dasha 前端可见化：Skill workbench 和主界面“多 Dasha 系统”详情都会显示当前 MD/AD、五级层级、Nakshatra/Pada、关键词与 fragment source。
- 验证：`python3 -m pytest tests/test_api_server_security.py tests/test_frontend_productization.py tests/test_muhurta.py -q` 通过；`npm run build` 通过；`python3 scripts/audit_fragments.py --strict` 通过，候选碎片从 6 个降至 4 个。
- 当前下一最高优先级：处理 `reading_orchestrator.py`、`orchestrator_bridge.py`、`hermes_bridge.py`、`mevg_automation.py` 的产品归属。
- 完成主题化报告编排器接入：新增 `/api/thematic_report`，复用 `report_orchestrator.py` 生成五主题 summary/narrative/evidence/conflict/timing/recommendations，并把 `reading_orchestrator.py`、`orchestrator_bridge.py` 作为 registry 输出路径纳入真实引用链。
- 完成前端承载：`api-bridge.js`/`public/api-bridge.js` 暴露 `computeThematicReport`，Skill workbench 新增“主题报告”动作，Technique Directory/API Explorer 可试算 `/api/thematic_report`，结果以主题卡展示强度、时间锚点、证据和建议。
- 验证：`python3 -m pytest tests/test_frontend_productization.py -q` 通过；`python3 scripts/audit_fragments.py --strict` 通过，66 registry / 36 API endpoints / 42 frontend files，0 problems，候选碎片从 4 个降至 2 个。
- 当前下一最高优先级：处理剩余 `hermes_bridge.py` 与 `mevg_automation.py`；两者偏外部学习/自动化门控，需做非破坏性产品归属或工具化决策。
- 完成主题报告/编排碎片归档：`/api/thematic_report` 返回 `fragment_sources` 与 `workflow_orchestration`，声明 `report_orchestrator.py`、`reading_orchestrator.py`、`orchestrator_bridge.py` 的分工；Skill workbench 主题报告结果会展示这些来源。
- 完成 MEVG 自动化接入：`/api/case_validation` 返回 `mevg_gate`，只读 `mevg_automation.py` 的门控协议/状态文件，不运行子进程、不写状态；无 `tests/mevg_state.json` 时明确返回 `NOT_INITIALIZED`。
- 完成 Hermes 归档决策：`hermes_bridge.py` 属于外部个人 agent/WorkBuddy 学习桥，依赖 `hermes_memory_core.py` 且默认写 `~/.workbuddy`，不进入印度占星网页/app 默认产品面，已加入 `scripts/audit_fragments.py` 的忽略清单。
- 当前下一最高优先级：跑全量回归、build、碎片审计，确认候选碎片清零。
- 完成回归确认：`python3 -m pytest tests/test_frontend_productization.py tests/test_api_server_security.py tests/test_muhurta.py -q` 通过；`npm run build` 通过；`git diff --check` 通过；`python3 scripts/audit_fragments.py --strict` 通过，候选碎片清零。
- 当前下一最高优先级：从“碎片清理”转向真实用户端质量，优先把 `/api/thematic_report` 从样例 evidence 升级为消费真实 full-reading 模块证据。
- 完成主题报告真实证据链：`/api/thematic_report` 在没有自定义 evidence、但提供 birth/chart payload 时进入 `derived_chart_evidence` 模式，best-effort 调用 chart、dasha、yogas、shadbala、ashtakavarga、relationship、career、Jaimini 模块，生成 marriage/career/wealth/health/spirituality 五主题证据。
- 完成前端证据透明度：Skill workbench 主题报告结果显示 `evidence_source`、`module_status`、warning 数和 real/sample fallback 状态，让用户能区分真实计算报告与示例报告。
- 验证：`python3 -m pytest tests/test_api_server_security.py::test_thematic_report_derives_evidence_from_birth_payload tests/test_api_server_security.py::test_thematic_report_declares_orchestrator_fragments tests/test_frontend_productization.py::test_skill_workbench_exposes_all_expected_advanced_actions -q` 通过；`npm run build` 通过。
- 当前下一最高优先级：补 Technique Directory/API Explorer 的方法文档、可复制 cURL/OpenAPI 示例，并继续检查同品类产品 polish 缺口。
- 完成方法文档/API 示例：`/api/technique_catalog` 新增 `api_docs` 与每行 `method_docs`，白名单 endpoint 自动生成 cURL、最小 OpenAPI operation、方法 notes；主题报告等多 endpoint 技法会按 id/name/domain 优先绑定最相关 API。
- 完成前端 API 文档展示：Technique Directory 卡片显示方法摘要、边界和 API doc key；Explorer 样例结果显示 `cURL / OpenAPI` 折叠区，支持复制本地 API 调用片段。
- 验证：`python3 -m pytest tests/test_frontend_productization.py::test_skill_workbench_exposes_all_expected_advanced_actions tests/test_frontend_productization.py::test_frontend_backend_contracts_with_api_handler -q` 通过；`npm run build` 通过。
- 当前下一最高优先级：执行全量回归/审计后，转向 P2 同品类产品 polish：PWA/桌面包装审计、隐私信任中心、术语模式与可替换星历底座。
- 完成 PWA/信任中心 MVP：新增 `manifest.webmanifest`、`pwa-icon.svg`、`sw.js`，HTML 关联 manifest/theme color，主入口注册 service worker、监听 install prompt，并在参数/日历页展示 PWA 状态。
- 完成本地数据 Trust Center：参数/日历页显示 Local-first 数据说明、本地星盘/配对/问事数量、API/AI 边界；提供“安装为应用”“导出本地资料”“清空本地资料”按钮，清空动作保留 `window.confirm` 二次确认。
- 验证：`python3 -m pytest tests/test_frontend_productization.py::test_provenance_panchanga_workspace_panel_is_productized tests/test_frontend_productization.py::test_mobile_layout_keeps_dense_sections_single_column -q` 通过；`npm run build` 通过；相关 `git diff --check` 通过。
- 当前下一最高优先级：全量回归/审计后，推进术语模式和星历底座可替换性说明。
- 完成术语模式产品化：Trust Center 新增入门/专业/梵文优先三档；tooltip 会按当前模式切换标题、名称对照和说明深度；provenance、Trust Center 本地导出、JSON/HTML 报告都会记录当前术语偏好。
- 验证：`python3 -m pytest tests/test_frontend_productization.py::test_provenance_panchanga_workspace_panel_is_productized tests/test_frontend_productization.py::test_mobile_layout_keeps_dense_sections_single_column -q` 通过；相关 `git diff --check` 通过。
- 当前下一最高优先级：补桌面包装说明/spike，并继续星历底座可替换性分析。
- 完成主题报告 full-reading 证据链升级：`/api/thematic_report` 在出生数据路径下优先调用 `cmd_full_reading`，读取 full-reading modules，并把 marriage_counting、Vivah Saham、Dasa convergence、Dhana Yoga、validation、D30、D20/Jaimini 等真实模块折叠进五主题证据。
- 修复主题报告兼容性 Bug：full-reading 的 Dasha timeline 中 `antardasha` 可能是对象，已在 `_normalize_thematic_dasha_timeline` 中统一提取 lord/name 并归一化年份，避免 `report_orchestrator.TimingAnchorBuilder` 拼接时报 TypeError。
- 完成前端证据透明度增强：Skill workbench 主题报告结果显示 `full-reading:<module_count> modules` 与 `full_reading_modules` 来源，普通用户可区分 full-reading 实算证据和 sample fallback。
- 验证：`python3 -m pytest tests/test_frontend_productization.py tests/test_api_server_security.py tests/test_muhurta.py -q` 通过；`npm run build` 通过；`python3 scripts/audit_fragments.py --strict` 通过，66 registry / 36 API endpoints / 43 frontend files / candidate_count 0；`git diff --check` 通过。
- 当前下一最高优先级：术语模式与星历底座抽象，先检查现有 glossary/i18n/calculation settings 是否已有半接入碎片，再补用户端切换入口与导出/provenance 记录。
- 完成术语模式与星历底座 MVP：Calculation Settings 增加 `ephemerisBackend` 与 `terminologyMode`，兼容旧 `jyotish_terminology_mode`；tooltip 支持 balanced/beginner/professional 三种解释层，Trust Center、provenance、HTML/JSON 导出都会记录当前模式与星历底座。
- 产品边界：`xalen-ephemeris` 先作为 Apache-2.0 可行性记录，不改变当前 Swiss Ephemeris 主路径；避免 UI 暗示已替换核心黄经。
- 验证：`python3 -m pytest tests/test_frontend_productization.py tests/test_api_server_security.py tests/test_muhurta.py -q` 通过；`npm run build` 通过；`python3 scripts/audit_fragments.py --strict` 通过；`git diff --check` 通过。
- 当前下一最高优先级：桌面包装说明与运行健康检查入口，让普通用户能判断本地 API/PWA/导出能力是否可用。
- 完成普通用户运行健康检查入口：`api-bridge.js`/`public/api-bridge.js` 暴露 `getAPIHealth()`；Trust Center 新增 Runtime Health 面板和“运行健康检查”按钮，串联 `/api/health`、`/api/capability_audit`、PWA 状态、Pake/Tauri 桌面路线与 preflight 命令。
- 修复普通用户可用性 Bug：此前 Trust Center 只展示静态 API 说明，用户无法判断本地 Python API 是否在线；现在失败时给出 `npm run web` / `python3 scripts/jyotish_api_server.py` / `python3 scripts/desktop_packaging_preflight.py` 的具体恢复路径。
- 验证：`python3 -m pytest tests/test_frontend_productization.py::test_api_bridge_exports_productized_backend_actions tests/test_frontend_productization.py::test_provenance_panchanga_workspace_panel_is_productized tests/test_frontend_productization.py::test_mobile_layout_keeps_dense_sections_single_column tests/test_frontend_productization.py::test_desktop_packaging_spike_is_documented_and_checkable -q` 通过；`npm run build` 通过。
- 当前下一最高优先级：跑全量回归/碎片审计后，继续首次使用引导与普通用户空状态路径。
- 会话恢复检查：`session-catchup.py` 提示前一窗口存在未同步上下文；已按建议读取 `task_plan.md`、`progress.md`、`findings.md` 并查看 `git diff --stat`，继续在原计划文件内同步状态。
- 完成首屏首次使用引导：`jyotish-app/index.html` 新增 `first-use-panel`，提供“运行健康检查”“填入示例盘”“识别已有星盘”三条入口；`main.js` 新增 `DEMO_BIRTH`、`setupFirstUsePanel`、`fillDemoBirth`、`runFirstUseHealthCheck`、`focusFirstUseImport`，并把本地星盘库空状态改成可行动提示。
- 完成首屏样式与移动端守门：`style.css` 新增 first-use 操作区样式，并把 `.first-use-grid` 纳入现有 768px 单列响应式守门。
- 测试先行：先新增 `test_first_use_onboarding_is_actionable` 并确认红灯失败于缺失 `first-use-panel`；实现后继续复跑到产品矩阵同步阶段。
- 当前下一最高优先级：完成首屏测试转绿后，运行构建/preflight/diff 检查，再用真实浏览器做桌面/移动首次运行冒烟。
- 浏览器冒烟发现并修复首跑 Banner Bug：Python API 返回的 `ascendant` 不含 `lord`、`Moon` 不含 `nakshatra/nakshatra_pada`，前端原本直拼字段会显示 `undefined`；新增 `getAscendantLord`、`normalizePlanetRecord`、`formatMoonNakshatra`，从星座推导上升主星，缺星宿时隐藏该行。
- 新增回归守门：`test_chart_banner_avoids_undefined_api_fields` 先红灯捕捉 Banner 直拼问题，修复后转绿。
- 真实浏览器验证：使用系统 Google Chrome + Codex bundled Playwright 访问 `http://127.0.0.1:5173/`，完成首屏健康检查、示例盘填入、生成星盘、移动端 390px 单列检查；输出确认 `hasUndefined=false`、`chartVisible=true`、`consoleErrors=[]`。
- 当前下一最高优先级：跑全量前端测试、build、desktop preflight、diff check，并关闭本地 API/Vite 会话。
- 完成首次使用入口接线复核：输入页已有“运行健康检查 / 填入示例盘 / 识别已有星盘”三入口；修正首次使用健康检查读取 `/api/capability_audit` 的字段口径，使用 `registry.technique_count` 与 `surfaces.api_endpoint_count`，避免显示模糊的“技法目录已返回”。
- 验证：`python3 -m pytest tests/test_frontend_productization.py tests/test_api_server_security.py tests/test_muhurta.py -q` 通过；`npm run build` 通过；`python3 scripts/audit_fragments.py --strict` 通过，candidate_count 0；`git diff --check` 通过；`python3 tests/run_frontend_runtime_smoke.py --start-if-needed` 通过，66 registry / 66 excellent UX / 66 productized。
- 浏览器交互守门：Playwright Python 包存在，但 Chromium 二进制下载多次超时/断连，已停止卡住的安装进程；当前以 runtime smoke + curl 首页/manifest/api-bridge + packaging preflight 作为可执行首跑验证。
- 完成高级技法错误恢复提示：Skill Workbench/API Explorer 的 `renderWorkbenchError` 现在提示先到 Trust Center 运行健康检查，并给出 `npm run web` / `python3 scripts/jyotish_api_server.py` 的恢复动作。
- 当前下一最高优先级：继续导出/报告失败恢复和 AI/API key 安全提示，降低普通用户在 PDF、AI 聊天和外部凭证配置上的误操作。
- 官方文档核对：OpenAI API authentication 文档明确 API key 是 secret，不应暴露在浏览器/app 客户端代码里，应从服务端环境变量或密钥管理服务读取；据此修正 AI 聊天配置提示。
- 完成 AI/API key 安全提示：`ai-chat.js` 新增 `buildAISetupGuidance`，未登录与本地默认回复都提示通过服务端 `/api/chat` 或后端代理连接模型，并说明 `OPENAI_API_KEY` 放在服务端环境变量；移除“浏览器控制台 localStorage 配置 endpoint”的旧提示。
- 完成导出失败恢复：`main.js` 新增 `getPDFExportRecoveryMessage` / `getGenericExportRecoveryMessage`，PDF fallback 明确“已改为导出 HTML 报告”，并指向 Trust Center 健康检查与 `python3 scripts/jyotish_api_server.py` 恢复路径；导出异常不再弹窗打断。
- 新增测试：`test_ai_chat_guides_server_side_secret_handling` 先红灯后转绿，并守住 `buildAISetupGuidance` 只定义一次；`test_export_failure_recovery_guides_health_check` 先红灯后转绿。
- 当前下一最高优先级：跑完整前端产品化测试、API 安全测试、runtime smoke、build、preflight、audit fragments 与 diff check，然后继续 ephemeris abstraction feasibility。
- 验证完成：`python3 -B -m pytest tests/test_frontend_productization.py tests/test_api_server_security.py tests/test_muhurta.py -q` 通过；`python3 tests/run_frontend_runtime_smoke.py --start-if-needed` 通过；`npm run build` 通过；`python3 scripts/desktop_packaging_preflight.py` 通过；`python3 scripts/audit_fragments.py --strict` 通过，problem_count/warning_count/candidate_count 均为 0；相关 `git diff --check` 通过。
- 当前下一最高优先级：进入 ephemeris abstraction feasibility，先扫描本地 `xalen`/VedAstro/PyJHora/SwissEph 记录与现有 calculation settings，再决定做探针脚本还是 API contract。
- 完成 AI 安全提示修复：`ai-chat.js` 不再在默认回复中引导用户通过浏览器控制台/localStorage 配置 AI endpoint；新增 `buildAISetupGuidance()`，明确 `OPENAI_API_KEY` 必须放在服务端环境变量，并通过服务端 `/api/chat` 或后端代理使用。
- 完成导出失败恢复提示：`main.js` 新增 `buildExportRecoveryMessage()`；PDF 失败时在 `export-status` 中提示先运行 Trust Center 健康检查、启动本地 API，或先导出 HTML 再浏览器打印 PDF，不再用 alert 打断。
- 验证：`python3 -m pytest tests/test_frontend_productization.py::test_ai_chat_guides_server_side_secret_handling tests/test_frontend_productization.py::test_provenance_panchanga_workspace_panel_is_productized -q` 通过；`npm run build` 通过；`git diff --check` 通过。
- 当前下一最高优先级：跑全量回归/碎片审计后，继续检查 `api-bridge.js` 中旧版 `YINDUZHANXING_AI_KEY` 浏览器密钥路径是否应降级为 legacy warning 或移除。
- 完成浏览器 AI key 路径降级：`api-bridge.js`/`public/api-bridge.js` 不再读取 `YINDUZHANXING_AI_KEY`、不再暴露 `apiKey`、不再向旧 relay 发送 Bearer token；`aiReading/aiFullReading/aiQuickInsight` 保留函数名但返回 `AI_BROWSER_KEY_DISABLED` 安全指引，AI 对话统一走登录后的服务端 `/api/chat` 或后端代理。
- 修复过境对比旧 key 传播：`renderTransitCompareTab` 请求本地 `/api/transit` 时不再从 `window.JyotishAPI.apiKey` 拼 `Authorization` header。
- 文档同步：README 历史说明改为当前浏览器构建禁用模型 API key 直连，避免普通用户继续按旧方式配置。
- 验证：`python3 -m pytest tests/test_frontend_productization.py::test_api_bridge_exports_productized_backend_actions tests/test_frontend_productization.py::test_ai_chat_guides_server_side_secret_handling -q` 通过；`npm run build` 通过。
- 当前下一最高优先级：执行全量回归/碎片审计后，继续检查登录/订阅/API 调用失败是否有用户端恢复提示。
- Ephemeris TDD 红灯：新增 `test_ephemeris_abstraction_feasibility_is_probeable` 后先运行 `python3 -B -m pytest tests/test_frontend_productization.py::test_ephemeris_abstraction_feasibility_is_probeable -q`，按预期失败于缺少 `scripts/ephemeris_backend_probe.py`。
- 完成星历后端可行性探针：新增 `scripts/ephemeris_backend_probe.py`，只读检查 `swisseph_python`、`swisseph_wasm`、`xalen_ephemeris`、`vedastro`、`pyjhora_benchmark` 的可用性、`license_posture` 与 `replacement_readiness`，输出 JSON。
- 完成星历可行性文档：新增 `docs/research/ephemeris_abstraction_feasibility_2026_06_23.md`，同步 `docs/research/product_gap_matrix_2026_06_22.md`、`task_plan.md`、`findings.md`。
- 当前下一最高优先级：跑探针/测试/build/preflight/audit 回归后，继续进入星历 backend adapter contract 与 longitude parity matrix。
- Ephemeris contract TDD 红灯：新增 `test_ephemeris_adapter_contract_and_parity_matrix_are_defined` 后先运行，按预期失败于缺少 `scripts/ephemeris_adapter_contract.py`。
- 完成星历 adapter contract：新增 `scripts/ephemeris_adapter_contract.py`，复用现有 `compute_chart_data` 生成 `swisseph_python` baseline，定义 `EphemerisAdapterContract`、`PARITY_CASES`、`sun_moon_asc_nodes` 和 `acceptance_thresholds`。
- 完成 parity matrix 文档：新增 `docs/research/ephemeris_adapter_contract_2026_06_23.md`，明确 Sun/Moon/Asc/Rahu/Ketu 的 `longitude_delta_arcsec` 验收阈值与 xalen/VedAstro/PyJHora 的接入边界。
- 当前下一最高优先级：跑 contract 脚本、测试、build、preflight、fragment audit、diff check，然后继续候选 adapter spike 或 AI/export 交互 smoke。
- 完成 runtime smoke 补强：`tests/run_frontend_runtime_smoke.py` 现在 POST `/api/report_artifact` 并验证 HTML fallback artifact，同时读取 `/api-bridge.js` 确认 `AI_BROWSER_KEY_DISABLED`、`server_side_only` 和无前端 Bearer key 泄漏。
- 完成候选星历 adapter spike：新增 `scripts/ephemeris_candidate_adapter_spike.py` 与 `docs/research/ephemeris_candidate_adapter_spike_2026_06_23.md`，将 `swisseph_wasm_candidate` 和 `xalen_ephemeris_candidate` 都挡在 `license_gate` / `parity_gate_required` / `runtime_setting_exposure` 之后。
- 当前下一最高优先级：跑候选 spike 与全量回归；随后继续检查登录/订阅/API 调用失败恢复提示。
- 调试修复：`scripts/ephemeris_adapter_contract.py` 首跑暴露 `PARITY_CASES` 的 `id/label` 被混传进 dataclass，已修正为只传计算输入字段，保留 `id/label` 用于矩阵行。
- 验证完成：`python3 scripts/ephemeris_backend_probe.py` 通过，确认 SwissEph Python/WASM 可用、xalen 未本地接入、VedAstro/PyJHora 为基准；`python3 scripts/ephemeris_adapter_contract.py` 通过并生成 3 组 baseline parity rows。
- 回归完成：`python3 -B -m pytest tests/test_frontend_productization.py tests/test_api_server_security.py tests/test_muhurta.py -q` 通过；`npm run build` 通过；`python3 scripts/desktop_packaging_preflight.py` 通过；`python3 scripts/audit_fragments.py --strict` 通过，problem/warning/candidate 均为 0；相关 `git diff --check` 通过。
- 当前下一最高优先级：检查候选星历 adapter 的本地可执行性；若没有 xalen 本地二进制/源码，则先做 SwissEph WASM parity smoke 或转向 AI/export 实际交互 smoke。
- 候选 adapter spike 复核：本地有 Rust/Cargo，但没有 xalen 源码或二进制；SwissEph WASM 资产存在，`@swisseph/browser` package license 为 `AGPL-3.0`，`swisseph-wasm` package license 为 `GPL-3.0-or-later`。
- 完成许可证门禁结构化：`scripts/ephemeris_candidate_adapter_spike.py` 新增 `package_license` 输出和 distribution gate，避免把 GPL/AGPL WASM fallback 误当作低风险生产替换后端。
- 当前下一最高优先级：跑候选 gate 测试和全量回归后，转向 AI/export runtime smoke 或 xalen 隔离获取/构建 spike。
- 验证完成：`python3 scripts/ephemeris_candidate_adapter_spike.py` 输出 `package_license`，`test_ephemeris_candidate_adapter_spike_is_gated` 通过；全量 `tests/test_frontend_productization.py tests/test_api_server_security.py tests/test_muhurta.py` 通过；`npm run build`、`desktop_packaging_preflight.py`、`audit_fragments.py --strict`、相关 `git diff --check` 均通过。
- 当前下一最高优先级：从星历 gate 转向真实用户运行路径，优先检查 AI/export runtime smoke 是否覆盖点击失败恢复、服务端密钥提示和 PDF/HTML fallback。
- 真实浏览器 AI 交互验证：打开 `http://127.0.0.1:5173/`，示例盘生成后打开 AI 面板，输入“请概述这个星盘”并按 Enter；面板在 1280x720 视口内，回复明确提示 `/api/chat`、服务端环境变量 `OPENAI_API_KEY`、不要把 key 放浏览器，且无 `jyotish_ai_endpoint` 或浏览器控制台配置文案。
- 修复 AI 安全残留：删除 `ai-chat.js` 旧版 `localStorage.getItem('jyotish_ai_endpoint')` 自定义 endpoint fetch 路径；`test_ai_chat_guides_server_side_secret_handling` 现在禁止 `jyotish_ai_endpoint` 和 `Custom endpoint failed`。
- Runtime smoke 补强：`tests/run_frontend_runtime_smoke.py` 现在同时检查 `api-bridge.js` 和 `ai-chat.js`，确认 AI 浏览器 key 禁用、聊天配置指向服务端 `/api/chat` 和 `OPENAI_API_KEY`。
- 当前下一最高优先级：跑 runtime smoke、全量回归、build、审计和 diff check；然后继续导出点击路径是否需要更强可见状态守门。
- 完成登录/订阅/API 恢复提示：`auth.js` 新增 `buildAuthRecoveryMessage`、`showAuthError` 与安全响应解析，登录/注册/Apple/token 校验失败时会提示 Trust Center、`npm run web`、`python3 scripts/jyotish_api_server.py`；`subscription.js` 新增 `buildSubscriptionRecoveryMessage`、`showSubscriptionNotice`，IAP/恢复购买/收据验证失败不再只弹 alert，并对消息做 HTML 转义。
- 验证完成：`test_auth_and_subscription_failures_have_recovery_guidance` 通过；全量 `tests/test_frontend_productization.py tests/test_api_server_security.py tests/test_muhurta.py` 通过；`tests/run_frontend_runtime_smoke.py --start-if-needed` 通过；`npm run build` 通过；`ephemeris_backend_probe.py`、`ephemeris_adapter_contract.py`、`ephemeris_candidate_adapter_spike.py`、`desktop_packaging_preflight.py`、`audit_fragments.py --strict` 和 `git diff --check` 均通过。
- 当前下一最高优先级：继续检查主排盘、关系工作流、Skill Workbench 的 API 调用失败恢复是否同样完整。
- 完成 API bridge 与主排盘失败恢复：`api-bridge.js`/`public/api-bridge.js` 安全解析非 JSON 响应，主排盘表单新增 `chart-compute-status` 可见状态，失败时提示 Trust Center、`npm run web`、`python3 scripts/jyotish_api_server.py`，不再用 alert 打断。
- 完成 AI chat API 失败恢复：`ai-chat.js` 对 `/api/chat` 使用安全响应解析；服务端 AI 不可用时提示服务端环境变量 `OPENAI_API_KEY`、Trust Center 与本地 API 启动路径，同时保留本地解释 fallback。
- 完成 Transit/互动 API 失败恢复：`renderTransitCompareTab` 不再直接 `resp.json()`，非 JSON/HTTP 错误会显示可行动恢复提示；Transit 主渲染、关系合盘、Prashna、校正时间应用统一走 `buildInteractiveAPIRecoveryMessage`/`renderInlineAPIError`，避免裸错误和旧版启动命令散落。
- 当前下一最高优先级：跑完整回归、runtime smoke、build、星历/打包/碎片审计与 diff check；若通过，进入真实浏览器点击级 smoke，覆盖生成星盘、AI chat、导出、Transit/合盘/问事失败态。
- 真实浏览器点击级 smoke 发现并修复首盘渲染残留：示例盘生成后页面仍有 `☽ undefined Pundefined` 与 Raman 详情 `(undefined)`；已改为 `buildChartSummary` 复用 `formatMoonNakshatra`，`analysis-renderers.js` 新增 `sanitizeRamanDetail` 将缺失星座显示为“缺星座”。
- 验证完成：`python3 -m pytest tests/test_frontend_productization.py tests/test_api_server_security.py tests/test_muhurta.py -q` 通过；浏览器复验示例盘后 `hasUndefined=false`、`hasNaN=false`、控制台无 error；`npm run build` 通过；`python3 tests/run_frontend_runtime_smoke.py --start-if-needed` 通过；`python3 scripts/audit_fragments.py --strict` 与 `git diff --check` 通过。
- 当前下一最高优先级：把真实浏览器点击级 smoke 固化为可重复脚本，继续覆盖 AI chat、导出、Transit/合盘/问事失败态。
- 完成真实浏览器点击级 smoke 固化：新增 `tests/run_frontend_click_smoke.py`，动态启动本地 API/Vite，向页面注入 `YINDUZHANXING_API_BASE`，使用系统 Chrome 真实点击示例盘生成、AI chat、HTML 导出、Transit、合盘、问事，并输出 JSON 结果。
- 点击级 smoke 发现并修复 HTML 导出真 Bug：`computeNakshatraAdvanced` 中对象简写误写 `sub_lord,`，运行时抛 `sub_lord is not defined`，导致 HTML 报告导出失败；已修为 `sub_lord: subLord`，并在产品化测试中禁止回归。
- 验证完成：`tests/run_frontend_click_smoke.py` 通过，HTML 导出状态为“HTML 报告已开始下载，可直接打开或打印”；`python3 -B -m pytest tests/test_frontend_productization.py tests/test_api_server_security.py tests/test_muhurta.py -q` 通过；`npm run build`、`desktop_packaging_preflight.py`、`audit_fragments.py --strict`、`run_frontend_runtime_smoke.py --start-if-needed`、三条 ephemeris 脚本和 `git diff --check` 均通过。
- 当前下一最高优先级：把真实浏览器守门扩展到移动端/离线/PWA 安装与无 API 失败路径，避免只验证在线桌面 happy path。
- 完成移动端/离线/PWA 点击守门扩展：`tests/run_frontend_click_smoke.py` 支持 `--mode core|mobile|offline|all`；`mobile` 跑 390x844 真机视口，`offline` 故意指向未监听 API 端口，验证健康检查恢复提示、浏览器 fallback 排盘和 manifest/serviceWorker。
- 真实移动端修复：mobile smoke 发现 AI FAB 在 390px 视口被星盘/行星表截获，并发现页面横向溢出 528px；已把移动 FAB 改为左侧安全区定位、AI panel 改为 `100vw` 左侧滑入，并给 chart/table 容器补 `minmax(0,1fr)`/`min-width:0`/`max-width:100%`。
- 完成 Pake/Tauri 非破坏性本机探测：`scripts/desktop_packaging_preflight.py` 新增 `toolchain_probe`，只读探测 node/npm/rustc/cargo/xcodebuild/pake/tauri；本机 node/npm/rust/cargo 可用，pake/tauri CLI 未安装，xcodebuild 只有 CommandLineTools 因此 `macos_signing_notarization=false`。
- 验证完成：`python3 tests/run_frontend_click_smoke.py --mode all` 通过；`python3 -B -m pytest tests/test_frontend_productization.py -q` 通过；`npm run build` 通过；`python3 scripts/desktop_packaging_preflight.py` 输出 `toolchain_probe.non_destructive=true`；相关 `git diff --check` 通过。
- 当前下一最高优先级：继续检查 PDF fallback 的真实点击路径、PWA 离线 shell 二次加载、以及移动端长页面关键标签切换。
- 完成 PDF fallback 真实点击守门：`run_pdf_fallback_smoke` 会生成示例盘后 monkeypatch `window.JyotishAPI.generateReportArtifact` 返回 HTML fallback，真实点击“导出 PDF 报告”，验证用户看到“PDF 渲染器不可用 / 已改为导出 HTML 报告 / Trust Center / npm run web / python3 scripts/jyotish_api_server.py”。
- 完成 PWA 离线 shell 二次加载守门：`run_offline_shell_reload_smoke` 等待 service worker 控制后切换 `context.set_offline(True)` 并 reload，确认 `first-use-panel` 仍可加载，离线 JS module 请求的 `ERR_FAILED` 被归入 `offline_shell_expected_console_errors`，不污染真正 console error。
- 完成移动端长标签切换守门：`run_mobile_tab_smoke` 在 390x844 视口依次点击 Complete、Vargas、Synastry、Prashna、Transit Compare，确认对应 panel active、无 `undefined/NaN`、无非豁免横向溢出。
- 验证完成：`python3 tests/run_frontend_click_smoke.py --mode all` 通过，输出 `pdf_fallback_checked=true`、`offline_shell_reload_checked=true`、`mobile_tab_switch_checked=true`；`python3 -B -m pytest tests/test_frontend_productization.py -q` 通过；`npm run build` 通过；相关 `git diff --check` 通过。
- 当前下一最高优先级：检查报告/导出后端 artifact 的用户可见完整性，包括 HTML/PDF artifact 状态、失败恢复、下载命名和普通用户可理解提示。
- 完成移动/离线/PWA 点击守门：`tests/run_frontend_click_smoke.py` 新增 `--mode online|offline|all`；在线模式补移动首屏和 `manifest.webmanifest`/`serviceWorker` 检查；离线模式只启动前端，用未监听 API 端口验证 `first-use-health` 与排盘 fallback 恢复提示。
- 完成质量门接入：`scripts/run_quality_gate.py` 默认运行 `tests/run_frontend_click_smoke.py --mode all`，并提供 `--skip-frontend-click` 给无浏览器环境跳过。
- 验证完成：`python3 tests/run_frontend_click_smoke.py --mode all` 通过，在线/离线 console_errors 均为空，离线连接拒绝被归类为 `expected_offline_console_errors`；`python3 -B -m pytest tests/test_frontend_productization.py tests/test_api_server_security.py tests/test_muhurta.py -q` 通过；`npm run build`、`run_frontend_runtime_smoke.py --start-if-needed`、`desktop_packaging_preflight.py`、`audit_fragments.py --strict`、`git diff --check` 均通过。
- 当前下一最高优先级：继续补普通用户“桌面应用/安装后首次打开”路线说明与验证，让 PWA/Pake/Tauri 路径从文档提示进一步变成可执行检查。
- 完成桌面首启路线可执行化：`scripts/desktop_packaging_preflight.py` 新增 `first_launch_checks`，输出 PWA installed shell、Pake first launch、Tauri sidecar readiness 三条可执行检查；README 与 `docs/research/desktop_packaging_spike_2026_06_23.md` 增加 `tests/run_frontend_click_smoke.py --mode all` 和“安装后首次打开”步骤。
- 调试修正：首轮 click smoke 抓到 390px 移动视口 `scrollWidth=528`；诊断确认来源是 `.section-tabs` 合法横向滚动项，而非页面主体溢出。已将 smoke 的溢出检测改为排除 `.section-tabs` 等明确滚动容器，继续抓其他非预期溢出。
- 验证完成：`python3 tests/run_frontend_click_smoke.py --mode all` 通过；`python3 -B -m pytest tests/test_frontend_productization.py tests/test_api_server_security.py tests/test_muhurta.py -q` 通过；`npm run build`、`run_frontend_runtime_smoke.py --start-if-needed`、`desktop_packaging_preflight.py`、`audit_fragments.py --strict`、`git diff --check` 均通过。
- 当前下一最高优先级：做 Pake/Tauri 本机可用性探测脚本，只检测 CLI、Rust/Node、签名/sidecar 前置条件，不生成真实包，避免破坏性打包。
- 完成 PDF fallback / PWA 离线 shell / 移动长标签守门：`tests/run_frontend_click_smoke.py --mode all` 覆盖 PDF 渲染器不可用时 HTML fallback 提示、移动端 Complete/Vargas/Synastry/Prashna/Transit Compare 标签切换、service worker 真离线二次加载。
- 修复 PWA 离线 shell 噪声：`jyotish-app/public/sw.js` 现在只在 `request.mode === 'navigate'` 时 fallback 到 `/index.html`，避免 JS module 离线请求拿到 HTML 并触发 MIME 错误；断网资源错误会被 smoke 归类为 expected，真正异常仍留在 `console_errors`。
- 当前下一最高优先级：跑完整回归链后，继续检查报告/导出后端 artifact 的用户可见完整性。
- 完成报告/导出 artifact 契约收口：`/api/report_artifact` 现在对 HTML、PDF 成功、PDF fallback 都返回 `artifact_status`、`primary_artifact`、`download_filename`、`download_mime`、`fallback_reason`、`user_message`、`next_action`，并在 `delivery` 中提供同构字段。
- 完成前端 artifact 下载与提示收口：`exportPDFReport` 优先使用后端 `download_filename`/`download_mime`，保留 `downloaded_filename` 作为实际浏览器下载记录；`formatReportArtifactStatus` 优先使用后端 `user_message`，PDF fallback 继续显示 HTML 降级、文件名与打印 PDF 路径。
- 验证完成：新增 report artifact PDF fallback 单元测试先红灯后转绿；`tests/run_frontend_runtime_smoke.py --start-if-needed` 输出 `artifact_status=html_ready` 与 `download_filename`；`python3 -B -m pytest tests/test_frontend_productization.py tests/test_api_server_security.py -q` 通过；`npm run build` 在 `jyotish-app/` 通过；相关 `git diff --check` 通过。
- 当前下一最高优先级：补真实浏览器导入/案例库工作流守门，覆盖文本/PDF 星盘导入入口、识别失败恢复、保存案例、重新打开和导出案例库，继续排查移动端导出菜单与 Trust Center 长内容。
- 完成导入/案例库真实浏览器守门补强：`tests/run_frontend_click_smoke.py --mode workspace` 先用不完整出生资料验证“仍需手动补充：出生时间、出生地经纬度、时区”，再用完整 Delhi 文本资料验证识别质量分、自动填表、生成星盘、保存本地星盘、重新打开、保存到案例库、导出已选和导出全库。
- 验证完成：`python3 tests/run_frontend_click_smoke.py --mode workspace --keep-logs` 通过，下载 `jyotish-selected-cases-2026-06-23.json` 与 `jyotish-case-library-2026-06-23.json`，console_errors 为空。
- 当前下一最高优先级：排查移动端导出菜单与 Trust Center 长内容，确认 390px 视口下菜单不遮挡、长面板无横向溢出、健康检查/本地数据/安装说明在移动端可读可操作。
- 完成导入/案例库真实点击守门：`tests/run_frontend_click_smoke.py` 新增 `run_import_workspace_smoke` 和 `--mode workspace`，真实输入出生资料文本，确认识别质量 100、填表、生成星盘、保存本地星盘、返回输入页重开保存星盘、进入参数/日历工作区保存当前盘、导出已选案例和整库。
- 验证完成：`python3 tests/run_frontend_click_smoke.py --mode workspace` 通过；`python3 tests/run_frontend_click_smoke.py --mode all` 通过并包含 `import_workspace_checked=true`、`jyotish-selected-cases-*.json`、`jyotish-case-library-*.json`；`python3 -B -m pytest tests/test_frontend_productization.py tests/test_api_server_security.py -q` 通过；`python3 tests/run_frontend_runtime_smoke.py --start-if-needed` 通过；`npm run build` 在 `jyotish-app/` 通过；相关 `git diff --check` 通过。
- 当前下一最高优先级：排查移动端导出菜单与 Trust Center 长内容，确认 390px 视口下菜单不遮挡、长面板无横向溢出、健康检查/本地数据/安装说明在移动端可读可操作。
- 完成移动端导出菜单与 Trust Center 长内容守门：`tests/run_frontend_click_smoke.py --mode mobile-trust` 在 390px 视口检查导出菜单五项、JSON 下载、Trust Center 健康检查、本地资料导出、关键按钮文案和长面板横向溢出。
- 修复移动端问题：Trust Center 健康检查成功后 `renderAll()` 会重渲染面板，原先状态被 PWA 默认说明覆盖；新增 `getTrustCenterStatusMessage` 保留健康检查结果。工作区案例块在移动端会因内部 360px 宽度加 padding 越界，已给 case workspace 相关块补 `min-width:0`、移动单列和 `max-width:100%`。
- 完成点击 smoke 超时/质量门接入：`tests/run_frontend_click_smoke.py --timeout 1` 验证超时路径输出 `process_snapshot` 与日志尾部，PID 清理后 `ps` 无残留；`scripts/run_quality_gate.py` 新增 `--frontend-click-timeout` 并传给点击 smoke 默认 `--timeout 240`。
- 验证完成：`python3 tests/run_frontend_click_smoke.py --mode all` 通过；`python3 tests/run_frontend_click_smoke.py --mode mobile-trust --timeout 120` 通过；`python3 -B -m pytest tests/test_frontend_productization.py tests/test_api_server_security.py -q` 通过；`python3 tests/run_frontend_runtime_smoke.py --start-if-needed` 通过；`npm run build` 在 `jyotish-app/` 通过；相关 `git diff --check` 通过。
- 当前下一最高优先级：给 PDF/文本星盘导入的文件上传分支补真实浏览器守门，覆盖 PDF 文本抽取失败恢复、文本文件上传解析、导入后字段质量提示与移动端文件选择入口。
- 完成 PDF/文本文件上传导入守门：`tests/run_frontend_click_smoke.py --mode import-files` 真实上传 `.txt` 出生资料，验证识别质量 100、字段填入到 1988-11-09 06:45 Mumbai/UTC+5:30；monkeypatch PDF import API 抛错后上传 `.pdf`，验证“PDF文本抽取失败”和“可复制PDF文字后粘贴到文本框”恢复文案；移动 390px 视口确认“上传文件”入口可见且触控高度达标。
- 修复移动端文件入口：`.chart-import-actions button, .chart-import-file` 的 `min-height` 从 38px 提升到 44px，满足移动端基本触控目标。
- 稳定全量点击 smoke：workspace 案例库导出改为 `page.expect_download()` 明确等待 `jyotish-selected-cases-*.json` 与 `jyotish-case-library-*.json`，避免长链路中下载事件偶发未捕获。
- 验证完成：`python3 tests/run_frontend_click_smoke.py --mode import-files --timeout 120` 通过；`python3 tests/run_frontend_click_smoke.py --mode all --timeout 240` 通过并包含 `import_files`；`python3 -B -m pytest tests/test_frontend_productization.py tests/test_api_server_security.py -q` 通过；`python3 tests/run_frontend_runtime_smoke.py --start-if-needed` 通过；`npm run build` 在 `jyotish-app/` 通过；相关 `git diff --check` 通过。
- 当前下一最高优先级：把普通用户安装/启动文档与质量门输出统一，减少“npm run web / python API / PWA 安装”多入口带来的认知负担。
- 完成普通用户启动路径统一：README 新增“普通用户启动路径”，将网页启动、本地 API、Trust Center 健康检查、PWA 边界和完整自检命令压成一条路径；`scripts/run_quality_gate.py` 的失败摘要也输出同一套网页/API/Trust Center 步骤。
- 验证完成：`test_desktop_packaging_spike_is_documented_and_checkable` 先红灯后转绿；`python3 -B -m pytest tests/test_frontend_productization.py tests/test_api_server_security.py -q` 通过；`python3 tests/run_frontend_runtime_smoke.py --start-if-needed` 通过；`npm run build` 在 `jyotish-app/` 通过；相关 `git diff --check` 通过。
- 当前下一最高优先级：继续检查 README/应用内 Trust Center/失败恢复文案的术语一致性，把“npm run web / npm run dev / python API / PWA”统一成普通用户可理解的一组标签。
- 完成术语一致性收口：`main.js`、`api-bridge.js`、`public/api-bridge.js`、`ai-chat.js`、`i18n.js`、`skill-map.js` 的普通用户可见恢复提示统一为“按 README 的普通用户启动路径启动网页服务和本地 API 服务”，Trust Center 成功状态统一为“本地 API 服务、能力目录和 PWA 安装壳”。
- 边界约束：README 与 `scripts/run_quality_gate.py` 继续保留可复制命令；应用界面不再散落 `npm run web`、`npm run dev`、完整 `python3 scripts/jyotish_api_server.py --host ...` 这类开发者命令。
- 验证完成：术语聚焦 pytest 8 项通过；`python3 -B -m pytest tests/test_frontend_productization.py tests/test_api_server_security.py -q` 通过；`python3 tests/run_frontend_click_smoke.py --mode mobile-trust --timeout 120` 通过；`python3 tests/run_frontend_runtime_smoke.py --start-if-needed` 通过；`npm run build` 在 `jyotish-app/` 通过；`git diff --check` 通过。
- 当前下一最高优先级：梳理质量门分层与运行成本，把快速开发守门、完整浏览器守门、发布前守门拆得更清楚，避免遗漏真实用户路径也避免每步都跑超长链路。
- 启动整机与 Git 云端地毯式遗漏审计：当前仓库 remote 为 `git@github.com:732642856/yinduzhanxing.git`，分支 `codex/release-hygiene-ci`；初步只读枚举发现整机存在 `.workbuddy/skills/jyotish-vedic-astrology`、`Projects/星轨资料恢复/*/jyotish-vedic-astrology`、`engines-repo/jyotish`、`WorkBuddy/*/jyotish-fragments`、多个历史审计/验证报告、PDF/Docx 资料库和多个 star-track/占星相关 git 仓库。
- 审计边界：只读索引与摘要，不删除、不移动、不上传整机资料；密钥/凭证类文件只记录路径和命中类别，不读取内容；远端仓库以当前认证/公开可访问 refs 为准，若被凭证阻断则记录阻断点。
- 远端探测进展：`git ls-remote` 走 SSH 被 22 端口超时阻断；改用 HTTPS 成功列出 `main`、`codex/release-hygiene-ci` 和 v6.0.47-v6.0.52 tags。GitHub REST API 匿名请求被 rate limit，后续以 HTTPS git 协议和 `/tmp` mirror 为主。
- 安全发现：多个历史仓库 remote URL 内嵌 GitHub token；后续报告只记录“存在嵌入 token 的 remote”与路径类别，不复述 token 字符串。
- 旧审计报告提取到的候选遗漏：Navatara/Tara Bala、Kantaka Shani、Pushkar Navamsa、Ishta/Kashta Phala、Ashtakavarga PAV/Prashtara/Kakshya/Yoga Pinda、Bhava Bala、Sripathi/Placidus、Vimshottari 多起算点、36 Sahams、Tajika 强度体系、完整 Prashna/KP Horary、Muhurta 求解器、精微分盘 D24/D30/D60 深度模板。
- 完成云端 mirror 第一轮：`/tmp/yinduzhanxing-cloud` 来自 GitHub HTTPS mirror，HEAD 为 `11bdee3ba1f480aff38440ad58cfbb81bfa5567d`，文件数 720，tree `d3a89944bb1c319120f61f66a88c879d0fa28375`。本地工作区文件数 1525，其中大量是 build/cache/node_modules/dist 与未提交产品化改动。
- 完成遗漏映射文档：新增 `docs/research/whole_machine_git_audit_2026_06_23.md`，记录整机资料源、远端 refs、历史报告共识、当前 registry/API/frontend 覆盖矩阵和下一优先级。
- 第一轮结论：旧报告的 30 类缺口已有一批被 v6.9 后续补上（Kantaka Shani、Pushkara、Kakshya、Bhava Bala、Trisphuta、部分 Sahams/Prashna/Muhurta），真正仍缺第一类产品化闭环的是 Ashtakavarga Prashtara/Yoga Pinda、Sripathi/Placidus 用户可控切换、KP Horary、Tajika Harsha/Panchavargiya、Muhurta date-range solver、Sayanadi/Shayanadi 与精微分盘深度模板。
- 当前下一最高优先级：从 Ashtakavarga Prashtara / Yoga Pinda 开始实现，因为它在历史报告中反复出现，且当前只有 BAV/SAV 总分和参考代码，没有专业工具应有的来源贡献表与 Pinda 层。
- 完成 Ashtakavarga Prashtara / Yoga Pinda 产品闭环：`scripts/ashtakavarga.py` 保留并验证 `calc_prastara_av` 的 7×12×8 PAV 矩阵，新增 `calc_yoga_pinda` 一等契约；`/api/ashtakavarga` 返回 `yoga_pinda_summary` 和 `rule_variants.selected += yoga_pinda`；Skill workbench 显示 `Ashtakavarga / PAV / Sodhita / Yoga Pinda`、Yoga Pinda 卡片与校验标签。
- 完成 Ashtakavarga 守门：`tests/test_ashtakavarga_invariants.py` 不再依赖本机缺失的 Hypothesis，改为确定性 invariant；新增 PAV 回推 BAV、Yoga Pinda 与 legacy Shodhya Pinda 兼容断言；产品化测试要求 API 返回 `pav.matrix_shape` 与 `yoga_pinda_summary`。
- 验证完成：`python3 -m pytest -q tests/test_ashtakavarga_invariants.py` 4 项通过；`python3 -m pytest -q tests/test_frontend_productization.py -k "technique_catalog or ashtakavarga or api_runtime"` 通过；`python3 -m json.tool references/technique_registry.json` 与 `git diff --check` 通过。
- 当前下一最高优先级：推进 Sripathi/Placidus 房宫算法用户可控切换与 parity 守门，因为历史审计多次指出它仍停留在 staged policy/局部代码层，尚未形成用户可验证的房宫算法切换闭环。
- 完成移动端导出菜单与 Trust Center 长内容守门：`tests/run_frontend_click_smoke.py --mode mobile-trust --keep-logs` 在 390x844 移动视口下验证导出菜单 JSON/HTML/PDF/SVG/PNG 不溢出，JSON 星盘下载成功，Trust Center 健康检查通过，本地资料 JSON 导出成功，长面板无横向溢出且无 console error。
- 验证输出：`mobile_trust_export_checked=true`，下载 `jyotish-chart-1990-01-01.json` 与 `jyotish-local-data-2026-06-23.json`，`health_status=健康检查通过：本地 API、能力目录和 PWA 状态已记录。`
- 当前下一最高优先级：给真实浏览器点击级 smoke 增加命令级超时/残留进程诊断，避免 `--mode all` 或局部模式异常时留下 API/Vite/Chromium 后台进程。
- 完成真实浏览器 smoke 超时与残留诊断：`tests/run_frontend_click_smoke.py` 新增 `--timeout`、`run_with_timeout`、`ClickSmokeTimeoutError`、`process_snapshot` 与 `force_stop_process`，超时失败会输出 API/Vite pid、running 状态和日志尾部，并在 finally 强制清理子进程。
- TDD 验证：先让 `test_click_smoke_covers_core_interactive_workflows` 要求 `--timeout/run_with_timeout/process_snapshot/force_stop_process` 后红灯，再实现；`python3 tests/run_frontend_click_smoke.py --mode mobile-trust --timeout 1 --keep-logs` 按预期失败并输出 process_snapshot，随后 ps 未发现残留 API/Vite 进程。
- 正常路径复验：`python3 tests/run_frontend_click_smoke.py --mode mobile-trust --timeout 120 --keep-logs` 通过，移动 Trust/export 仍返回 `mobile_trust_export_checked=true`。
- 当前下一最高优先级：跑完整回归链与碎片审计，然后继续推进普通用户长链路质量门的剩余缺口。
- 完成普通用户长链路质量门摘要：`scripts/run_quality_gate.py` 新增 `format_failure_summary`、stdout/stderr 尾部、cwd、JSON reason/process_snapshot 提取；真实失败时会提示聚焦命令、`--keep-logs` 与 Trust Center/API 恢复路径。
- 修复质量门真实 Bug：`npm run build` 原先在仓库根目录执行导致找不到 `package.json`，已新增 `APP = ROOT / "jyotish-app"` 并让前端 build 在 `cwd=APP` 执行。
- 修复 click smoke 真实 Bug：`run_import_file_smoke` 已等待 PDF 失败恢复文案但没有赋值 `pdf_import_recovery`，导致 `--mode all` NameError；已保存该文案并通过 `--mode import-files` 和 `--mode all` 验证。
- 验证完成：`python3 tests/run_frontend_click_smoke.py --mode import-files --timeout 120 --keep-logs` 通过；`python3 scripts/run_quality_gate.py --skip-slow --skip-yoga-logic --frontend-click-timeout 240` 通过，覆盖 compile、JSON、capability/fragment audit、BPHS invariants、185 个 pytest、前端 build、runtime smoke、全量 click smoke。
- 当前下一最高优先级：把普通用户安装/启动文档与质量门输出统一，减少“npm run web / python API / PWA 安装”多入口带来的认知负担。
- 完成普通用户启动路径与术语统一：README、质量门失败摘要、AI/API/auth/subscription/Skill Workbench/Trust Center/离线恢复提示统一使用“普通用户启动路径 / 网页服务 / 本地 API 服务 / PWA 安装壳 / Trust Center”；用户面旧称 `npm run web`、`PWA shell`、`PWA 壳`、`Local API` 已从应用与 README/质量门中移除。
- 修复离线恢复提示：offline click smoke 发现首用健康检查失败文案缺少“普通用户启动路径”，已补回并验证 `offline_recovery_guidance_visible=true`。
- 验证完成：`python3 -B -m pytest tests/test_frontend_productization.py -q` 通过；`npm run build` 通过；`python3 tests/run_frontend_runtime_smoke.py --start-if-needed` 通过；`python3 tests/run_frontend_click_smoke.py --mode mobile-trust --timeout 120 --keep-logs` 通过；`python3 tests/run_frontend_click_smoke.py --mode offline --timeout 120 --keep-logs` 通过。
- 当前下一最高优先级：梳理质量门分层与运行成本，把快速开发守门、完整浏览器守门、发布前守门拆得更清楚，避免遗漏真实用户路径也避免每步都跑超长链路。
- 完成质量门分层：`scripts/run_quality_gate.py` 新增 `QUALITY_GATE_PROFILES` 与 `--profile quick|browser|release`；quick 适合普通代码/文案修改，browser 覆盖 runtime 与真实浏览器路径，release 恢复慢速 golden cases 与 Yoga 逻辑报告；`--frontend-click-mode` 可局部复验 `mobile-trust/import-files/all` 等浏览器路径。
- 文档与守门同步：README 新增“质量门分层”，`tests/test_frontend_productization.py` 增加静态契约，防止 profile、README 命令或关键浏览器模式后续漂移。
- 验证完成：先让 `test_quality_gate_declares_fast_browser_release_profiles` 红灯确认缺口，再实现转绿；`python3 scripts/run_quality_gate.py --profile quick` 通过；`python3 scripts/run_quality_gate.py --profile browser --frontend-click-mode mobile-trust --frontend-click-timeout 120` 通过，覆盖 187 个核心 pytest、前端 build、runtime smoke 与 mobile-trust click smoke；`python3 -B -m pytest tests/test_frontend_productization.py -q` 与 `git diff --check` 通过。
- 当前下一最高优先级：推进 Sripathi/Placidus 房宫算法用户可控切换与 parity 守门，先确认现有 `bhava_chalit`/UI/API 是否只是显示 staged policy，再补用户可验证闭环。
- 完成 Sripathi/Placidus 用户可控切换：`jyotish-app/skill-map.js` 的 Bhava Chalit 工作台读取 `calculationSettings.houseSystem`，请求带上出生时间地点 payload，不再硬编码 `sripati`；结果渲染宫位制、可选系统、第一宫边界和行星 Rashi→Bhava 迁移摘要。
- 完成 Bhava Chalit API parity 契约：`/api/bhava_chalit` 返回 `requested_house_system`、`selected_house_system`、`available_house_systems`、`calculation_note` 与 `fallback_reason`；Placidus/Koch 使用 swisseph JD + lat/lon/tz，缺依赖或参数时降级 Sripati 并解释原因。
- TDD 验证：新增测试先红灯抓到 Placidus 缺 JD/location 参数、前端硬编码 Sripati；实现后 `test_bhava_chalit_endpoint_exposes_user_selected_house_systems`、`test_bhava_chalit_uses_user_selected_house_system` 转绿。
- 验证完成：`python3 -B -m pytest tests/test_api_server_security.py tests/test_frontend_productization.py tests/test_bhava_chalit.py -q` 通过；`npm run build` 通过；`python3 -m py_compile scripts/jyotish_api_server.py scripts/bhava_chalit.py` 通过；`python3 scripts/run_quality_gate.py --profile quick` 通过，覆盖 189 个核心 pytest、前端 build 与 runtime smoke；`git diff --check` 通过。
- 当前下一最高优先级：推进 KP Horary 产品化闭环，先复核 `scripts/prashna.py`、VedicAstro horary 参考与当前 KP 快读，确认是否缺 ruling planets/sub-lord/house significator 的普通用户可验证输出。
- 完成 KP Horary 结构化证据闭环：`scripts/prashna.py` 新增 `build_kp_horary_evidence`，复用本地 KP sub-lord 与 significator 规则，返回 question houses、ruling planets、cuspal sub-lord、house significators 与 judgement matrix；`/api/prashna` 支持可选 `horary_number` 1-249 并返回 `kp_horary`。
- 完成普通用户端承载：Prashna 面板渲染 “KP Horary：Ruling Planets / Sub Lord / Significators” 证据块；问事 workflow、案例保存和导出都保留 `kp_horary`，避免只保存 YES/NO 结论。
- TDD 验证：新增 API 测试先红灯抓到 `kp_horary` 缺失；新增前端产品化 token 先红灯抓到 `renderKPHoraryEvidence/ruling_planets/house_significators` 缺失；实现后聚焦测试转绿。
- 验证完成：`python3 -B -m pytest tests/test_kp_system.py tests/test_api_server_security.py tests/test_frontend_productization.py -q` 通过；`npm run build` 通过；`python3 -m py_compile scripts/prashna.py scripts/kp_system.py scripts/jyotish_api_server.py` 通过；`python3 scripts/run_quality_gate.py --profile quick` 通过，覆盖 189 个核心 pytest、前端 build 与 runtime smoke；`git diff --check` 通过。
- 当前下一最高优先级：推进 Tajika Harsha/Panchavargiya Bala 产品化闭环，先检查 `scripts/tajika.py`、`scripts/varshaphala.py`、`/api/annual` 和 Skill Workbench 的年运强度层缺口。
- 完成 Tajika Harsha/Panchavargiya Bala 产品化闭环：`scripts/tajika.py` 新增 `calc_tajika_strength_layers`，输出 Harsha Bala、Panchavargiya 五分盘强度、综合排序、最强/最弱行星和下一步提示；`scripts/solar_return.py` 与 `scripts/varshaphala.py` 年报路径均追加 `tajika_strength`，避免 API/旧入口能力碎片。
- 完成普通用户端承载：`jyotish-app/skill-map.js` 的 Varshaphala / Tajika 结果新增“年度强度/年度风险”卡片和 Harsha Bala / Panchavargiya Bala 证据展开，不再只显示 Tajika Yoga 数量与 JSON。
- TDD 验证：新增算法、年度 API、前端产品化三条红灯测试，确认缺口后实现并转绿；`tests/test_tajika.py`、年度 API 聚焦测试、前端聚焦测试均通过。
- 验证完成：`python3 -B -m pytest tests/test_tajika.py tests/test_api_server_security.py::test_annual_endpoint_returns_varshaphala_report tests/test_frontend_productization.py::test_annual_workbench_renders_tajika_strength_layers -q` 通过；`python3 -m py_compile scripts/tajika.py scripts/solar_return.py scripts/varshaphala.py scripts/jyotish_api_server.py` 通过；`npm run build` 通过；相关 `git diff --check` 通过。
- 当前下一最高优先级：推进 Muhurta date-range solver，把当前单日评分升级为可按活动、日期范围与约束搜索的普通用户择日工作流。
- 完成 Muhurta date-range solver 产品化闭环：`scripts/muhurta.py` 新增 `muhurta_range_search`，复用 `panchanga_range_report` 的日历、Rahu Kala/Yamaganda/Gulika、Choghadiya、Hora 与活动评分，输出 `best_windows`、`rejected_dates`、`constraints` 和 `next_action`。
- 完成 `/api/muhurta` 范围入口：传入 `start_date/end_date/activity/limit/lat/lon/tz` 时返回 `range_search`，同时保留原单日 `report` 兼容旧调用，并继续限制 63 天以内。
- 完成普通用户端承载：`jyotish-app/skill-map.js` 的 Muhurta 结果新增“范围择日 · 择日候选”展开区，显示候选日期、评分、活动结论、推荐 Choghadiya/Hora 窗口、Panchanga 证据和过滤原因。
- TDD 验证：新增核心 solver、API、前端产品化三条红灯测试，确认缺口后实现并转绿；修复候选全合格时 `rejected_dates` 为空导致用户缺少过滤解释的问题。
- 验证完成：`python3 -B -m pytest tests/test_muhurta.py tests/test_api_server_security.py::test_muhurta_endpoint_returns_activity_checks tests/test_api_server_security.py::test_muhurta_endpoint_returns_date_range_solver tests/test_api_server_security.py::test_panchanga_range_endpoint_returns_calendar_rows tests/test_api_server_security.py::test_panchanga_range_endpoint_uses_location_when_available tests/test_frontend_productization.py::test_muhurta_workbench_renders_date_range_solver -q` 通过；`python3 -m py_compile scripts/muhurta.py scripts/jyotish_api_server.py` 通过；`npm run build` 通过；相关 `git diff --check` 通过。
- 当前下一最高优先级：推进 Sayanadi/Shayanadi Avastha 与 D24/D30/D60 深度模板产品化，把已有计算碎片变成 API/前端可验证的解释层。
- 完成 Sayanadi/Shayanadi Avastha 与 D24/D30/D60 深度模板产品化：新增 `scripts/deep_varga_avastha.py`，聚合 `avastha_calculator.py`、`divisional_charts_extended.py`、`trimshamsa_d30.py`，输出 `avastha_summary`、`deep_varga_templates`、D24/D30/D60 关键行星卡、risk_flags 与 next_action。
- 完成 API 承载：新增 `/api/deep_varga_avastha` 与 `_compute_deep_varga_avastha`，Technique Explorer dispatch、方法说明和示例 payload 均接入，避免该能力只停留在本地碎片。
- 完成普通用户端承载：`jyotish-app/skill-map.js` 新增 `deepVargaAvastha` 工作台按钮和 `renderDeepVargaAvasthaResult`，展示 Sayanadi/Shayanadi 主导状态、弱状态行星、D24/D30/D60 模板、risk_flags 与下一步边界。
- TDD 验证：新增 `tests/test_deep_varga_avastha.py`、API 测试、前端产品化测试，先红灯确认模块/API/action 缺失，后实现转绿。
- 验证完成：`python3 -B -m pytest tests/test_deep_varga_avastha.py tests/test_api_server_security.py::test_deep_varga_avastha_endpoint_returns_templates tests/test_api_server_security.py::test_divisional_yoga_endpoint_returns_varga_yoga_summary tests/test_frontend_productization.py::test_deep_varga_avastha_workbench_renders_templates tests/test_frontend_productization.py::test_skill_workbench_exposes_all_expected_advanced_actions -q` 通过；`python3 -m py_compile scripts/deep_varga_avastha.py scripts/jyotish_api_server.py scripts/avastha_calculator.py scripts/divisional_charts_extended.py scripts/trimshamsa_d30.py` 通过；`npm run build` 通过；相关 `git diff --check` 通过。
- 当前下一最高优先级：二轮整机/Git/开源对标审计与全球排名更新，复核第一类缺口是否已闭环，并重新生成下一批优先级。
- 完成二轮整机/Git/开源对标审计与全球排名更新：`python3 scripts/audit_fragments.py --strict` 显示 registry 68 技法、37 API、frontend 43 文件、候选碎片 0、hard problems 0、warnings 0；`docs/research/whole_machine_git_audit_2026_06_23.md` 已追加 2026-06-24 二轮结论与全球排名口径。
- 修复二轮审计发现的产品目录缺口：`deep_varga_avastha` 已有 API 与 Skill Workbench，但未进入 registry/catalog/audit command map；新增注册表条目、audit 映射、后端产品化/UX/目录推断，并增加测试要求 `/api/deep_varga_avastha` 出现在能力审计、Technique Explorer filter、sample payload 与 runnable example。
- TDD 验证：新增断言后先红灯（`KeyError: deep_varga_avastha` 与 catalog 缺 `/api/deep_varga_avastha`），修复后 `python3 -B -m pytest tests/test_api_server_security.py::test_capability_audit_scans_registry_and_local_sources tests/test_api_server_security.py::test_technique_catalog_exposes_runnable_api_examples -q` 通过；`python3 -m json.tool references/technique_registry.json`、`python3 -m py_compile scripts/jyotish_api_server.py scripts/audit_fragments.py scripts/deep_varga_avastha.py`、`python3 scripts/audit_fragments.py --strict` 通过。
- 当前下一最高优先级：发布/仓库卫生与 release 质量门收口，优先确认未跟踪产品文件不会在 GitHub/普通用户安装路径中遗漏，再跑完整 browser/release profile。
- 完成发布/仓库卫生第一步：`scripts/run_quality_gate.py` 新增 `RELEASE_CRITICAL_UNTRACKED_PATHS`、`release_hygiene_check` 与 release profile 的 `check_release_hygiene`；先用聚焦测试红灯确认缺口，再实现守门。
- 真实风险复现：新增 release hygiene 后在当前工作区按预期失败，列出 28 个关键产品文件仍未跟踪；随后将这些文件纳入 Git 暂存，`release_hygiene_check` 复跑通过，`audit_fragments.py --strict` 当前 `workspace_residue.untracked_count=0`。
- 旧测试调整：`test_fragment_audit_blocks_registry_surface_drift` 不再强制要求一定存在 untracked 文件，改为检查字段存在和列表结构，适配发布卫生目标。
- 验证完成：`python3 -B -m pytest tests/test_api_server_security.py::test_fragment_audit_blocks_registry_surface_drift tests/test_frontend_productization.py::test_release_quality_gate_tracks_untracked_product_files -q` 通过；`python3 scripts/run_quality_gate.py --profile quick` 通过，覆盖 195 个核心 pytest、npm build 与 runtime smoke，runtime smoke 显示 registry/productized/UX 均为 68。
- 当前下一最高优先级：跑完整 browser/release profile，并检查云端分支同步状态，确认普通用户从 GitHub 拉取不会丢失网页/API/PWA/高级工作台关键文件。
- 完成完整 browser/release profile：`python3 scripts/run_quality_gate.py --profile browser --frontend-click-timeout 240` 与 `python3 scripts/run_quality_gate.py --profile release --frontend-click-timeout 240` 均通过；release 覆盖 release hygiene、195+核心 pytest、runtime smoke、真实浏览器 all smoke、golden cases 与 Yoga 逻辑校验。
- 修复 release profile 暴露的 Yoga 逻辑校验 Bug：`scripts/validate_logic_v2.py` 现在用 `extract_skill_rule_ids` 安全跳过算法级无 `rule_id` Yoga，并默认使用当前仓库路径，不再在 import 时把 `~/.workbuddy/.../scripts` 插入 `sys.path` 污染后续 `import prashna`。
- 验证细节：新增 `test_yoga_logic_validation_tolerates_algorithmic_yogas_without_rule_id` 与 `test_yoga_logic_validation_import_does_not_shadow_project_modules` 先红灯后转绿；`validate_logic_v2.py` 输出 Precision 96.48%、Recall 93.99%、F1 95.22%，并写入当前仓库 `references/validation_logic_report.json`。
- 云端同步完成：本地改动已提交为 `83cc859 Productize jyotish app release surface` 并推送到远端 `codex/release-hygiene-ci`；GitHub API 确认现有 PR #6 处于 open，head 已更新到 `83cc859`。
- 修复 PR CI 云端稳定性风险：`.github/workflows/ci.yml` 将质量门命令从默认 browser profile 改为 `python scripts/run_quality_gate.py --profile quick --skip-yoga-logic`，避免 GitHub Actions 在未安装 Playwright/真实浏览器依赖时误跑 browser click smoke；完整 browser/release profile 仍作为发布前本地/手动守门。
- 验证完成：`python3 -B -m pytest tests/test_frontend_productization.py::test_quality_gate_declares_fast_browser_release_profiles tests/test_frontend_productization.py::test_release_quality_gate_tracks_untracked_product_files -q` 通过；`.github/workflows/*.yml` 均可被 PyYAML 解析。
- GitHub Actions 复查发现 PR #6 head `062dc86` 的 `validate` 与 `test` 均失败：`validate` 失败点为 Ruff lint，`test` 失败点为全量 `python -m pytest -q`；Actions 日志下载需要仓库 admin 权限，改为本地补齐 dev 依赖后复现。
- 修复 CI 阻断：`tests/conftest.py` 统一保证当前仓库 `scripts` 在 `sys.path[0]`，并在每个测试前清理从 `~/.workbuddy/skills/jyotish-vedic-astrology/scripts` 载入的同名模块，避免历史测试收集期污染 `prashna`；`tests/test_ashtakavarga_invariants.py` 给需要先改 `sys.path` 的脚本导入加 Ruff E402 标注。
- 验证完成：`python3 -m ruff check scripts/run_quality_gate.py tests/test_varga_bphs.py tests/test_ashtakavarga_invariants.py tests/test_cli_smoke.py tests/test_yoga_rules_integrity.py` 通过；`python3 -m pytest -q` 全量通过；`python3 scripts/run_quality_gate.py --profile quick --skip-yoga-logic` 通过，核心质量门 198 个 pytest、npm build 与 runtime smoke 通过。
- 继续复查 PR #6 Actions：Ruff 已转绿，但 `quick quality gate` 与 `pytest suite` 仍失败；在 `/tmp/yinduzhanxing-ci-repro` 干净 clone 复现，根因为 `test_fragment_audit_blocks_registry_surface_drift` 假设 `.git/lost-found` 一定存在，以及 `test_kp_system.py` 依赖未纳入 Git 的 `VedicAstro/vedicastro/data/KP_SL_Divisions.csv`。
- 修复 clean checkout 测试依赖：碎片审计测试改为检查 lost-found 字段结构而非要求本机残留数量；KP 外部 oracle CSV 缺失时明确 `pytest.skip`，保留内建 360° wrap 测试。
- 发布包链路进展：`python3 -m build --no-isolation --wheel --sdist` 成功生成 wheel/sdist；`python3 -m twine check dist/*` 通过；全新 venv 安装 wheel 后 `jyotish-engine --help` 可用。
- PR merge ref 复现：在 `/tmp/yinduzhanxing-pr6-merge` 拉取 `refs/pull/6/merge` 得到 `b614b03`；未安装前端依赖时可复现 `vite: command not found`，执行 `npm ci --prefix jyotish-app` 后 `python3 -m pytest tests/test_frontend_productization.py::test_local_frontend_and_api_runtime_smoke -q` 通过，`python3 scripts/run_quality_gate.py --profile quick --skip-yoga-logic` 通过，说明当前可复现路径不再指向产品代码行为缺陷。
- 完成 release-only workflow：新增 `.github/workflows/release-quality-gate.yml`，支持 `workflow_dispatch` 与关键路径 PR 触发，安装 Python/Node/Playwright Chromium 后运行 `python scripts/run_quality_gate.py --profile release --frontend-click-timeout 240`；`.github/workflows/ci.yml` 与 `.github/workflows/test.yml` 增加 Python/Node/npm/Vite 诊断，便于云端失败时定位依赖安装差异。
- TDD/验证完成：新增 `test_github_release_quality_gate_runs_browser_release_profile` 静态契约；`python3 -B -m pytest tests/test_frontend_productization.py::test_github_release_quality_gate_runs_browser_release_profile tests/test_frontend_productization.py::test_quality_gate_declares_fast_browser_release_profiles -q` 通过；`.github/workflows/*.yml` PyYAML 解析通过；`git diff --check` 通过；`python3 scripts/run_quality_gate.py --profile quick --skip-yoga-logic` 通过，核心质量门 199 个 pytest、npm build 与 runtime smoke 通过。
- 云端复查：PR #6 head `5399c6f` 的 `validate`、`test`、`release-quality-gate` 均失败；step metadata 显示依赖安装和 Vite 环境诊断已成功，失败仍发生在 pytest/quality gate 内部。GitHub annotations 仍只显示 exit code，日志/API 受权限限制；本机 Docker daemon 未运行，暂不能用 Linux 容器复现。
- 增补 CI 失败诊断：`.github/workflows/test.yml` 的 pytest 改为 `-vv --maxfail=1 --junitxml=artifacts/pytest.xml` 并上传 `pytest-diagnostics`；`ci.yml` 与 `release-quality-gate.yml` 将 quality gate stdout tee 到 artifact 并上传，下一轮云端失败可直接定位首个 Linux runner 差异。
- 云端 CI 收口完成：推送 `925e73e` 后，GitHub PR #6 最新 head 的 `validate`、`test`、`release-quality-gate` 三条检查均为 success；release-only browser/release 守门已在云端可运行。
- 完成准确率透明度页面：Trust Center 新增 Validation Transparency，直接展示 `references/validation_logic_report.json` 当前 Yoga 对照口径：60 charts、82 comparable rules、Precision 96.48%、Recall 93.99%、F1 95.22%、unmapped_pyjhora 718，并明确这些是 Yoga 规则对照指标，不是个人事件预测准确率。
- TDD/验证完成：先让 `test_trust_center_exposes_validation_transparency` 红灯确认缺口，再实现转绿；修复移动端 selector 回归后，`python3 -B -m pytest tests/test_frontend_productization.py::test_first_use_onboarding_is_actionable tests/test_frontend_productization.py::test_mobile_layout_keeps_dense_sections_single_column tests/test_frontend_productization.py::test_trust_center_exposes_validation_transparency -q` 通过；`npm run build --prefix jyotish-app` 通过；`python3 scripts/run_quality_gate.py --profile quick --skip-yoga-logic` 通过，覆盖 201 个核心 pytest、npm build 与 runtime smoke。
- 完成普通用户交付形态矩阵：新增 `scripts/deployment_preflight.py`，输出 local-dev、docker-compose、static-demo-pwa、desktop-shell 四条 delivery_matrix，明确公开演示环境只能完整展示静态壳、完整高级技法需要本地 API 服务；README 增加“普通用户交付形态”表格；Dockerfile build 阶段运行 deployment preflight。
- 交付矩阵纳入质量门：`scripts/run_quality_gate.py` 编译并执行 `scripts/deployment_preflight.py`，release hygiene 追踪该新文件，避免部署/公开演示路径漂移。
- 完成公开静态 demo/PWA 能力边界：首屏 `static-demo-boundary` 和 Trust Center `renderStaticDemoBoundary()` 明确 Browser fallback 与 Local API required 能力；README 增加 `static_demo_boundary_visible` 发布要求，`deployment_preflight.py` 会检查首屏与 Trust Center 是否保留该边界。
- TDD/验证完成：`test_user_delivery_matrix_is_documented_and_checkable` 先红灯确认缺 `deployment_preflight.py`，实现后转绿；`python3 scripts/deployment_preflight.py` 输出 `valid: true`；`python3 scripts/run_quality_gate.py --profile quick --skip-yoga-logic` 通过，覆盖 202 个核心 pytest、npm build 与 runtime smoke。
- 完成 Dasha/Shadbala 外部 oracle 边界第一步：新增 `references/oracle/dasha_shadbala_oracle_cases.json` 和 `scripts/oracle_boundary_audit.py`，把用户 PDF 的 Vimshottari 起点差异、Moon 偏移量、Shadbala 当前六分量 totals 与“缺分量级外部目标”的状态合并成可重复 JSON 审计。
- TDD 验证：`tests/test_oracle_boundary_audit.py` 先因 `scripts/oracle_boundary_audit.py` 缺失红灯，再实现转绿；报告明确 `production_tuning_recommended=false`，防止单样本调参或全局 Shadbala scaling。
- 完成 VedAstro 黄经 oracle 接入：`references/oracle/dasha_shadbala_oracle_cases.json` 新增 `longitude_cases`，记录 Antigravity/VedAstro SDK 对用户盘的 9 项 sidereal longitude；`scripts/oracle_boundary_audit.py` 输出每项角秒差、最大差和阈值状态。当前最大差为 Moon `26.2254` 角秒，全部低于 120 角秒阈值，说明 D1/D9 基础落点对齐，但不构成 Dasha/Shadbala 调参依据。
- 完成 Multi-Ayanamsa 与 AI Native Prompt Pack 第一层：`compute_chart_data(..., ayanamsa_name=...)` 和 `full-reading --ayanamsa` 均可验证切换，并在输出中记录 `ayanamsa_name/display/value`；`full-reading.ai_prompt_pack` 输出证据快照、RAG 检索文档和“不得单象下结论”的约束型提示词。
- 修正 Antigravity 并行改动的 oracle 语义风险：本地生成的 Shadbala `component_targets` 保留为结构样本，但审计报告标记为 `component_targets_sample_only` / `sample_only_not_external_oracle`，不能用于对外宣称 JHora/PyJHora 已校准。
- 完成 Antigravity AI 副手工作单：新增 `docs/research/antigravity_sidecar_work_order_2026_06_25.md`，安排其执行外部 oracle 样本采集、网页/app Multi-Ayanamsa 与 Prompt Pack 审计、skill 同步审计和浏览器用户流验证；同时写明禁止读取密钥、禁止破坏性命令、禁止把本地输出标成外部 oracle。
- 完成 standalone ayanamsa 全局状态修复：新增 `scripts/ayanamsa_utils.py`，Transit、Solar Return、Muhurta、cmd_muhurta 和 Yoga 准确率脚本都在 `FLG_SIDEREAL` 计算前显式设置 ayanamsa；红灯测试复现 Raman 全局污染约 `1.446°` 后转绿。
- 验证完成：`python3 -m pytest tests/test_standalone_ayanamsa_defaults.py tests/test_transit_trigger.py tests/test_transit_complete.py tests/test_muhurta.py tests/test_ayanamsa_switching.py tests/test_cli_smoke.py::test_full_reading_reports_ayanamsa_metadata_and_ai_prompt_pack tests/test_oracle_boundary_audit.py -q` 通过；`python3 -m py_compile scripts/ayanamsa_utils.py scripts/jyotish_engine.py scripts/transit_trigger.py scripts/solar_return.py scripts/muhurta.py scripts/cmd_muhurta.py scripts/cmd_solar_return.py scripts/jyotish_api_server.py scripts/validate_yoga_accuracy.py` 通过。
- 完成前端 Multi-Ayanamsa 与 AI Prompt Pack 承载：网页/app 的 birth payload 保留 `second` 并显式传 `ayanamsa`；`/api/chart` 返回 `birth.ayanamsa_name/display/node_mode` 与轻量 `ai_prompt_pack`；完整解盘页新增 `AI Prompt Pack` 面板，AI Chat 优先把 `prompt_zh/evidence_snapshot/retrieval_plan` 作为上下文。
- 完成产品头像轻量接入：用户提供头像已压缩为 512px 资源 `jyotish-app/public/brand-avatar.png` 与 `dist/brand-avatar.png`，页头显示尺寸降到 28px，manifest 增加 PNG 图标但保留原 SVG maskable 图标。
- 完成 Antigravity Round 2 副手任务单：新增 `docs/research/antigravity_sidecar_work_order_round2_2026_06_25.md`，安排全球产品差距、开源 oracle 可行性、前端黑盒复验和 Skill/App 同步审计，继续限定为只读/报告型副手。
- 完成 Antigravity Round 3 副手任务单：新增 `docs/research/antigravity_sidecar_work_order_round3_2026_06_25.md`，要求副手复验 Codex 已修的 Multi-Ayanamsa、秒级出生时间、`ai_prompt_pack`、AI Chat 上下文、产品头像和普通用户成品路径；输出限定为 `docs/research/*round3*2026_06_25.md`。
- 完成 Antigravity Round 4 副手任务单：新增 `docs/research/antigravity_sidecar_work_order_round4_2026_06_25.md`，要求副手围绕正式 oracle `template_cases` 做外部来源分层、5 个模板逐项填充路线、审计脚本黑盒复验和准确率透明度下一步建议。
- 完成 Dasha/Shadbala 外部真值采集队列第一层：新增 `scripts/oracle_collection_queue.py` 与 `tests/test_oracle_collection_queue.py`，把 5 个 `template_cases` 生成可执行采集任务，输出 `external_oracle_collection_queue`、preferred sources、collection steps、promotion criteria，并保持 `ready_for_calibration: 0` / `production_tuning_allowed: false`。
- 采集队列已接入质量门与文档：`scripts/run_quality_gate.py` release oracle 审计后会运行 `ORACLE_COLLECTION_QUEUE_CMD`，README 增加 markdown/json 命令与当前边界说明，`tests/test_frontend_productization.py::test_dasha_reference_audit_is_documented_and_gated` 防止该入口漂移。
- 完成 Antigravity Round 5 副手任务单：新增 `docs/research/antigravity_sidecar_work_order_round5_2026_06_25.md`，要求副手黑盒复验采集队列、README/质量门接入、外部来源采集动作和用户解释文案，只允许产出 `docs/research/*round5*2026_06_25.md` 报告。
- 完成采集队列 evidence packet：`scripts/oracle_collection_queue.py` 的每个任务现在包含 `evidence_packet.capture_id`、required metadata、target placeholders 与 integrity checks，明确 `must_not_come_from_local_engine`、`requires_external_artifact` 和 Shadbala 不得全局 scaling。
- 完成 evidence packet 文档/质量门同步：README 增加 `evidence_packet.capture_id`、`tool_name`、`source_artifact` 和本地输出不得作为外部 artifact 的说明；`run_quality_gate.py` 增加 `ORACLE_COLLECTION_QUEUE_EXPECTED_FIELDS`，测试锁定字段存在。
- 完成 Antigravity Round 6 副手任务单：新增 `docs/research/antigravity_sidecar_work_order_round6_2026_06_25.md`，要求副手黑盒复验证据包、人工采集模板、README/质量门同步和准确率透明度话术。
- 完成外部 evidence validator 第一层：新增 `scripts/oracle_evidence_validator.py` 与 `tests/test_oracle_evidence_validator.py`，校验证据包必须具备外部 artifact、完整 metadata、已填 target placeholders 和 `external_verified` 状态；本仓库/本地引擎输出会被拒绝，当前 5 个 draft packet 均保持 `valid_packets: 0`、`production_tuning_allowed: false`。
- 修复 Round 5 暴露的质量门覆盖缺口：`CORE_PYTEST_TARGETS` 现在直接包含 `tests/test_oracle_collection_queue.py` 和 `tests/test_oracle_evidence_validator.py`，quick profile 不再只靠静态产品化测试间接覆盖 oracle 队列。
- 完成 Antigravity Round 7 副手任务单：新增 `docs/research/antigravity_sidecar_work_order_round7_2026_06_25.md`，要求副手复核 evidence validator、quick/release 质量门接入、external_verified 晋级清单和用户准确率话术。
- 修复 external_verified 晋级路径：`scripts/oracle_collection_queue.py` 现在保留 oracle JSON 中已填的 `evidence_packet.status/metadata` 和目标值，新增 `target_fields`，避免外部证据包被重新降级为 `draft`；`scripts/oracle_evidence_validator.py` 改为用 `target_fields` 校验已填目标，兼容旧 draft 队列。
- 完成 Antigravity Round 8 副手任务单：新增 `docs/research/antigravity_sidecar_work_order_round8_2026_06_25.md`，要求副手黑盒复验 external_verified 晋级链路，并输出相对 VedAstro/PyJHora/JHora 的全球差距矩阵。
- 完成 GitHub 远端真实 HEAD 复核：`git ls-remote ssh://git@ssh.github.com:443/732642856/yinduzhanxing.git` 显示远端 `codex/release-hygiene-ci` 为 `912867f2ec35ce13f757fb0362da6bced9edf404`，与本地主分支 HEAD 一致；本地 `origin/... [gone]` 是 22 端口 fetch 失败后的跟踪引用异常，已用 `git update-ref` 按远端真实 HEAD 修复。
- 完成地毯式本机碎片扫描第一轮：高相关路径约 297 条，主要分布在当前主仓、`.workbuddy/skills/jyotish-vedic-astrology` 旧 skill 副本、`.gemini/antigravity-ide` scratch、Downloads PDF/压缩包、Desktop 私人报告、WorkBuddy 历史碎片、Projects 恢复目录、Documents/Codex 历史审计与 `Documents/星轨talk/engines-repo/jyotish`。
- 同项目 Git 副本扫描结论：除当前主仓外，发现 `.workbuddy/skills/jyotish-vedic-astrology` 指向同一远端但停在 `main@4ff6248`，仅 `references/validation_logic_report.json` 有排序类本地修改；该副本作为历史 skill/基线来源，不直接覆盖当前主仓。
- 私人输出同步边界：`output_report.txt` 和 `results_extracted.md` 是用户个人星盘复验临时输出，已加入 `.gitignore`，默认不纳入 GitHub 同步。
- 完成 Antigravity Round 10 副手任务单：新增 `docs/research/antigravity_sidecar_work_order_round10_2026_06_25.md`，要求副手复核整机碎片/Git 云端同步、Round 9 校准透明度 P0/P1、全球对标差距，并只产出 `docs/research/*round10*2026_06_25.md` 报告。
- 完成 Round 10 副手报告接收：`docs/research/antigravity_round10_*_2026_06_25.md` 记录了整机碎片同步、Git 云端状态、全球对标差距和校准透明度缺口；结论确认 `.workbuddy/skills/jyotish-vedic-astrology` 是旧副本，不直接合并。
- 完成 Dasha/Shadbala 校准透明度前端修复：Trust Center 新增 `Dasha/Shadbala Calibration Status` 面板，直接展示 `ready_for_calibration: 0`、`valid_packets: 0`、`production_tuning_allowed: false` 与 `D1/D9/SAV 高可信` / 大运起点和 Shadbala 绝对值仍需外部 evidence validator 的边界。
- 完成 AI/Skill 边界同步：`ai-chat.js`、`api-bridge.js`、`public/api-bridge.js` 与 `SKILL.md` 均强制注入“不得把大运起点或 Shadbala 绝对值说成已完成外部校准”的提示，避免普通用户误解“已完全校准”。
- 验证完成：新增 `test_trust_center_and_ai_expose_dasha_shadbala_calibration_status` 先红灯后转绿；聚焦产品化测试 5 项通过；`npm run build --prefix jyotish-app` 通过；`python3 -m py_compile scripts/oracle_collection_queue.py scripts/oracle_evidence_validator.py scripts/oracle_boundary_audit.py scripts/run_quality_gate.py` 通过；`git diff --cached --check` 通过且暂未发现密钥特征。
- 完成 GitHub 同步：`codex/release-hygiene-ci` 已成功推送到远端 `56a86dd53ecdc906a546a51cf2c63f02b61a7475`；本地 tracking ref 已同步对齐，`git status --short --branch` 无未提交文件。
- 完成 Antigravity Round 11 副手任务单：新增 `docs/research/antigravity_sidecar_work_order_round11_2026_06_25.md`，要求副手复核远端同步、Trust Center/AI/Skill 校准透明度修复和下一批普通用户成品缺口。
- 完成 Antigravity Round 11 副手复核接收：新增 `docs/research/antigravity_round11_*_2026_06_25.md` 四份报告，确认远端同步、Trust Center/AI/Skill 校准透明度已修复，同时建议把 Dasha/Shadbala 校准状态写入导出 HTML/JSON。
- 完成导出报告校准边界同步：`jyotish-app/export.js` 新增 `DASHA_SHADBALA_EXPORT_CALIBRATION_STATUS`，JSON 导出在 `meta.calibration_status` 与 `modules.calibration_status.dasha_shadbala` 携带 `ready_for_calibration: 0`、`valid_packets: 0`、`production_tuning_allowed: false`；HTML 报告新增“高级技法校准状态”区块。
- TDD/验证完成：`test_provenance_panchanga_workspace_panel_is_productized` 先因导出模块缺 `DASHA_SHADBALA_EXPORT_CALIBRATION_STATUS` 红灯，修复后转绿；相关 10 项 pytest 通过；`npm run build --prefix jyotish-app` 通过；`oracle_collection_queue.py` + `oracle_evidence_validator.py` 复验仍保持 `valid_packets: 0` / `production_tuning_allowed: false`。
- 当前下一最高优先级：发布 Round 12 副手任务，复核导出 HTML/JSON 校准边界，并推进“外部真值采集表单化 / 手工 JHora 证据包录入模板”。
- 完成 Oracle Evidence Intake 用户端闭环第一层：Trust Center 新增 5 个外部真值 Evidence Packet 下载卡，覆盖 `template_user_REDACTED_YEAR_moon_longitude_lahiri`、`template_steve_jobs_dasha_lahiri`、`template_redacted_place_shadbala_raman`、`template_extreme_latitude_kp`、`template_historical_epoch_lahiri`，目标字段与 `oracle_collection_queue.py` 当前队列对齐。
- 完成 Evidence Packet 导入判卷：前端可导入填写后的 JSON，调用后端 `/api/oracle_evidence`，并展示 `valid_packets`、`ready_for_calibration`、`production_tuning_allowed` 与每个 packet 的 `problems`；后端复用 `oracle_collection_queue` 和 `oracle_evidence_validator` 规则，本地输出、空字段与 `draft` 仍被拒绝。
- 完成副手任务升级：新增 Round 13/14/15 工作单；Round 15 改为 6 个并行包，覆盖 Evidence 判卷闭环、Shadbala 六分量、Dasha 边界日期、高需求技法、外部截图存档规范与下一轮 Codex 任务建议。
- 验证完成：`python3 -B -m pytest tests/test_frontend_productization.py::test_trust_center_exposes_oracle_evidence_intake_cards tests/test_frontend_productization.py::test_trust_center_and_ai_expose_dasha_shadbala_calibration_status tests/test_frontend_productization.py::test_provenance_panchanga_workspace_panel_is_productized tests/test_api_server_security.py::test_oracle_evidence_api_validates_uploaded_packets tests/test_oracle_collection_queue.py tests/test_oracle_evidence_validator.py -q` 通过；`python3 scripts/oracle_collection_queue.py ...` + `python3 scripts/oracle_evidence_validator.py ...` 仍显示 `valid_packets: 0` / `ready_for_calibration: 0`；`npm run build --prefix jyotish-app` 通过；`git diff --check` 通过。
- 当前下一最高优先级：创建 `references/oracle/artifacts/` 存档规范和第一条真实 JHora/PyJHora 黑盒证据包，优先推动 Shadbala 六分量与 Vimshottari Dasha 边界日期从 0/5 进入至少 1/5 可人工复核状态。
- 完成前端 Multi-Ayanamsa 与 AI Prompt Pack 可视化补强：完整解盘页 `AI Prompt Pack` 面板新增 Ayanamsa runtime status，区分 `backend_computed` 与 `browser_fallback`，显示 requested/applied ayanamsa 与降级说明；新增“复制 Prompt / 复制 Evidence”按钮，复制内容包含 prompt、evidence_snapshot、retrieval_plan 与 calculation_boundary。
- TDD/验证完成：先让 `test_frontend_ayanamsa_settings_are_live_api_parameters` 和 `test_ai_prompt_pack_panel_exposes_copyable_audit_context` 红灯，随后实现转绿；`python3 -m pytest -q tests/test_frontend_productization.py -k "ayanamsa_settings or ai_prompt_pack_panel or ai_chat_prefers"` 通过；`npm run build --prefix jyotish-app` 通过；`git diff --check` 通过。
- 当前下一最高优先级：继续 `references/oracle/artifacts/` 存档规范与第一条 JHora/PyJHora 黑盒证据包采集说明，和 Antigravity Round 16 的 artifact storage / Shadbala component validator / first JHora sample checklist 对齐。
- 完成 Antigravity Round 18 重型副手任务单：新增 `docs/research/antigravity_sidecar_work_order_round18_2026_06_25.md`，要求副手至少产出 12 份报告，覆盖当前补丁复核、全网开源许可证矩阵、功能缺口重排、用户黑盒流程、隐私仓库卫生、测试债和 AI Prompt Pack/Skill 同步，明确只允许宽松许可证代码进入可复用候选。
- 完成 Oracle artifact 存档规范：新增 `references/oracle/artifacts/.gitkeep` 与 `references/oracle/artifacts/README.md`，README 同步 `references/oracle/artifacts/`、`source_artifact`、`external_oracle_artifact`、必须打码、不得提交私人 PDF 原件、不得提交完整出生报告、不得提交浏览器 scratch 的规则；前端 Evidence Packet 下载文案同步相对路径与脱敏要求。
- 完成 Shadbala evidence 强校验：`scripts/oracle_evidence_validator.py` 新增 `SHADBALA_REQUIRED_PLANETS` 与 `SHADBALA_REQUIRED_COMPONENTS`，对 Sun/Moon/Mars/Mercury/Jupiter/Venus/Saturn 七曜的 sthana/dig/kala/chesta/naisargika/drik 六分量逐项拦截；测试覆盖空 dict、只填 Sun、完整七曜六分量和 API 上传复用 validator。
- 完成 Trust Center 真实采集进度面板：`renderOracleEvidenceProgressDashboard()` 在 Oracle Evidence Intake 顶部展示 `Dasha/Shadbala 真实进度`、`0 / 5`、`valid_packets`、`ready_for_calibration`、`production_tuning_allowed=false`、`references/oracle/artifacts/` 与 `missing_shadbala_component` 边界，避免用户误以为 Dasha/Shadbala 已完成外部绝对值校准。
- 修复 Round 17 暴露的门禁失败：移动端布局测试失败根因是 CSS selector 组被新增 `.oracle-evidence-intake-grid` 打断，已恢复原断言组并单独声明 oracle intake 移动单列；`jyotish-app/public/api-bridge.js` 已同步 `validateOracleEvidence`，确保 public/static bridge 与源码 bridge 一致。
- 验证完成：`python3 -m pytest -q tests/test_frontend_productization.py::test_mobile_layout_keeps_dense_sections_single_column tests/test_frontend_productization.py::test_trust_center_exposes_oracle_evidence_intake_cards tests/test_frontend_productization.py::test_oracle_artifact_storage_policy_is_documented` 通过；`python3 -m pytest -q tests/test_api_server_security.py::test_oracle_evidence_api_validates_uploaded_packets tests/test_oracle_evidence_validator.py` 通过；`python3 -m pytest tests/test_frontend_productization.py tests/test_cli_smoke.py tests/test_api_server_security.py tests/test_jaimini.py tests/test_shadbala_complete.py tests/test_transit_trigger.py tests/test_oracle_collection_queue.py tests/test_oracle_evidence_validator.py -q` 238 项通过；`npm run build --prefix jyotish-app` 通过；`python3 scripts/run_quality_gate.py --profile quick --skip-yoga-logic` 通过，包含 runtime smoke。
- 当前下一最高优先级：把第一条 JHora/PyJHora 黑盒 evidence packet 教程/模板落成可交给人工执行的文档，并等待外部截图或 stdout 后把 `valid_packets` 从 0/5 推到 1/5；同时接收 Round 18 副手报告，优先吸收宽松许可证可复用候选和真实用户流程缺口。
- 完成 Antigravity Round 19 副手任务单：新增 `docs/research/antigravity_sidecar_work_order_round19_2026_06_25.md`，要求副手以当前工作树重新复核 Round 18 过期结论、JHora/PyJHora 教程、第一条 evidence packet 模板、1/5 人工 runbook、runtime artifact 卫生、progress dashboard DOM/UX、Top 30 开源许可证复筛、Ashtakoot 破冰、Shadbala 单位校验、AI Prompt Pack oracle progress 和 Git tracking 策略。
- 完成第一条外部证据包执行资产：新增 `docs/user_jhora_capture_guide.md` 与 `references/oracle/evidence_packet_templates/jhora_steve_jobs_lahiri_first_packet.json`；模板保持 `status=draft`，只预留 Steve Jobs Lahiri/true node 的 metadata、Vimshottari start date 和 Shadbala 七曜六分量空位，不伪造任何外部数值。
- 验证完成：`python3 -m pytest -q tests/test_oracle_collection_queue.py::test_first_jhora_evidence_packet_template_is_safe_and_fillable tests/test_frontend_productization.py::test_first_jhora_capture_guide_is_actionable` 通过；`python3 -m json.tool references/oracle/evidence_packet_templates/jhora_steve_jobs_lahiri_first_packet.json` 通过。
- 当前下一最高优先级：接收 Round 19 副手报告并继续修正其发现；并在没有人工 JHora/PyJHora 截图前，优先补 `.gitignore` runtime-smoke HTML 卫生、Shadbala 数值单位/类型校验和 AI Prompt Pack 的 oracle progress 摘要。
- 完成 Round 19 反馈的无需人工 P0/P1 修复：`.gitignore` 新增 `runtime-smoke-report-*.html` 与 `jyotish-app/runtime-smoke-report-*.html`，避免 runtime smoke HTML 上云；`oracle_evidence_validator.py` 对 Shadbala 七曜六分量增加 int/float 且非 bool、非负校验，拒绝字符串数字和负数；`jyotish_engine.py`、`jyotish_api_server.py` 与前端 fallback `normalizeAIPromptPack()` 的 `evidence_snapshot.oracle_progress` 均携带 `valid_packets: 0`、`ready_for_calibration: 0`、`production_tuning_allowed: false`、`references/oracle/artifacts/` 与 `external_verified` 晋级规则。
- TDD/验证完成：新增红灯测试 `test_runtime_smoke_html_artifacts_are_ignored`、`test_validator_rejects_non_numeric_or_negative_shadbala_components`、CLI prompt pack `oracle_progress` 断言和前端 fallback 静态断言；修复后 `python3 -m pytest -q tests/test_frontend_productization.py::test_frontend_branded_avatar_and_prompt_pack_are_productized tests/test_frontend_productization.py::test_api_bridge_variants_prefer_backend_prompt_pack_context tests/test_frontend_productization.py::test_runtime_smoke_html_artifacts_are_ignored` 通过；`python3 -m pytest -q tests/test_cli_smoke.py::test_full_reading_reports_ayanamsa_metadata_and_ai_prompt_pack tests/test_oracle_evidence_validator.py tests/test_api_server_security.py::test_oracle_evidence_api_validates_uploaded_packets` 通过；`npm run build --prefix jyotish-app` 通过；`python3 scripts/run_quality_gate.py --profile quick --skip-yoga-logic` 通过，当前 quick 集合 242 项 pytest、build 与 runtime smoke 均通过。
- 当前下一最高优先级：在无法本机生成真实 JHora/PyJHora 外部截图的前提下，推进 Ashtakoot 合婚破冰与外部 oracle template 设计；同时准备把 Round 16-19 副手报告、work orders、artifact policy、capture guide 与 first packet template 纳入 Git 跟踪，避免不同窗口再次遗漏。
- 完成 Antigravity Round 20 副手任务单：新增 `docs/research/antigravity_sidecar_work_order_round20_2026_06_25.md`，要求副手纠正 Round 19 “Ashtakoot 完全缺失”的过期结论，复核已有 `scripts/ashtakoot.py`、`tests/test_ashtakoot.py`、`jyotish_engine.py ashtakoot`、`/api/synastry` 与前端合盘入口；同时继续审计 Round 19 修复、Ashtakoot oracle case 设计、UI/E2E 流程、JHora 1/5 人工监督、Git 纳入策略、开源 Ashtakoot 许可证矩阵、Shadbala 单位/总分设计和 AI Prompt Pack oracle progress。
- 当前下一最高优先级：先不重写 Ashtakoot 已有算法，转为补 Ashtakoot 外部 oracle cases、E2E 用户流程和 Git tracking 收口；真实 JHora/PyJHora 1/5 仍等待人工外部工具。
- 完成 Antigravity Round 21 重型副手任务单：新增 `docs/research/antigravity_sidecar_work_order_round21_2026_06_25.md`，把副手工作量扩到 18 个报告包、至少 20 个联网开源/产品复核对象、Top 40 ROI 任务，并明确 Ashtakoot oracle、VedAstro/RaviKarrii/pyhora2 许可证深挖、Trust Center UX、Git 入库、Shadbala 二期校验和 Round 22 执行计划。
- 完成 Ashtakoot 外部 oracle 第一层队列与 validator 强化：新增 `references/oracle/ashtakoot_oracle_cases.json` 5 条 draft cases，`oracle_collection_queue.py` 可输出 `target_modules=["ashtakoot"]`，README 记录 `Ashtakoot 外部合婚 oracle` 命令；`oracle_evidence_validator.py` 增加 36 分制范围、8 Kuta 分项范围和总分求和一致性拦截，拒绝 99 分、字符串/非法范围与 sum mismatch 的假外部证据包。
- 验证完成：`python3 -m pytest -q tests/test_oracle_evidence_validator.py tests/test_oracle_collection_queue.py` 14 项通过；`python3 -m pytest -q tests/test_ashtakoot.py tests/test_frontend_productization.py::test_dasha_reference_audit_is_documented_and_gated` 53 项通过；`npm run build --prefix jyotish-app` 通过；Ashtakoot queue 输出 5 条 template-only 样本且 `production_tuning_allowed=false`。
# 2026-06-25 Round 25 地毯式扫描与副手派工

- 用户强调：所有工作前必须地毯式探索印度占星全部信息，尤其检查不同窗口/多个文件夹中的碎片。
- 已读取 `task_plan.md`、`findings.md`、`progress.md`，确认计划中已有“实现前扫描本地碎片、open_source_sources、现有测试与产品差距矩阵”的硬规则。
- 已发布 `docs/research/antigravity_sidecar_work_order_round25_2026_06_25.md`，要求副手纠正 Round 24 Ashtakoot 误判、复核 VedAstro MIT 可复用范围、验收 accuracy profile、继续拆 UI/API/CLI/Prompt Pack/Oracle 缺口。
- 已创建 `docs/research/whole_machine_fragment_sweep_round25_2026_06_25.md`，记录整机扫描范围、高价值本地资料源、Git 远端状态、隐私边界和后续实现前置命令。
- 已发现高价值碎片源：当前主仓、`.workbuddy/skills/jyotish-vedic-astrology`、`Documents/星轨talk/engines-repo/jyotish`、`Documents/Codex/2026-06-20/.../engines-repo/jyotish`、Obsidian Jyotish 笔记、Downloads 私人 PDF/zip/docx、`references/open_source_sources`、`benchmarks/jyotish`。
- Git 状态：本地 `bac3748 docs(research): archive antigravity round 23 and 24 audits` 已创建；push 通过 SSH 22 超时失败，远端 HTTPS refs 显示 `codex/release-hygiene-ci` 仍在 `6338cf5`。后续需换 SSH-443 或其他可达方式再推。
- TDD 状态：已为 `run_quality_gate.py --profile accuracy` 写红灯测试，当前失败点是 `accuracy` profile 未实现；实现前已先响应用户要求完成碎片扫描。
- 已发布 `docs/research/antigravity_sidecar_work_order_round26_2026_06_25.md`，要求副手纠正 Round 25 Panchang 过强结论、黑盒验收 accuracy profile、设计 Git 远端替代同步和继续拆解 Ashtakoot/Shadbala/Kuja/Prompt Pack 票据。
- 已实现并验证 `run_quality_gate.py --profile accuracy`：跳过浏览器重活，强制运行真实案例复验、Dasha/Oracle 审计、Yoga 逻辑对照和 `local_accuracy_report.py`；真实运行输出 `Quality gate passed`。
- 修复 `scripts/validate_logic_v2.py` 的 set 顺序抖动，让 `references/validation_logic_report.json` 的 false positive/negative 列表稳定排序，避免 accuracy profile 每次制造无意义 diff。
- 完成 Antigravity Round 27 重型副手任务单：新增 `docs/research/antigravity_sidecar_work_order_round27_2026_06_25.md`，把副手工作量提高到 24 份报告，强制复核 Round25/26 归档、accuracy profile 稳定性、Yoga diff 稳定性、SSH-443/HTTPS 同步方案、Shadbala Phase 2、Kuja enum、Prompt Pack 安全护栏、Panchanga 商业级 UI、Ashtakoot oracle/许可证、API/前端隐藏技能 ROI、全机碎片后续读取顺序和 Round28 Top60。
- 完成 Shadbala Evidence Validator Phase 2 第一批实现：在现有 `sthana/dig/kala/chesta/naisargika/drik` schema 上增加 `total_rupa` 必填、单项 Rupa 上限 20.0、七曜六分量求和与 `total_rupa` 0.05 容差校验，避免人工 evidence packet 只填分量但总分不自洽仍被误判有效。TDD 红灯确认 3 个缺口后转绿，聚焦 validator/API 13 项测试通过。
- 完成“有效文件复用索引”：新增 `docs/research/local_reuse_candidate_index_round28_2026_06_26.md`，把当前 repo、旧 WorkBuddy skill、历史 benchmark、本地开源镜像按 `direct current repo reuse`、`older WorkBuddy skill reuse`、`local open-source mirrors`、`benchmark-only sources` 分类，明确未来补 Kuja/Panchanga/Tajika/Chara/Prompt Pack 时必须先查已有文件和许可证边界，再决定是否新写。
- 2026-06-26：新增 `docs/research/antigravity_sidecar_work_order_round29_2026_06_26.md`，继续扩大副手任务规模，集中拆 skill 全量补齐、本地可直接测试、云端同步白名单、外部 oracle 精度闭环与 `Round30 Top120`。
- 2026-06-26：当前待正式归档并推云的核心资产为 `docs/research/antigravity_round28_*_2026_06_26.md` 与 `docs/research/antigravity_sidecar_work_order_round29_2026_06_26.md`；归档完成后主线程继续优先补高 ROI 的 API/CLI/前端隐藏技法，而不是重新空写算法。

## 2026-06-28 Oracle/Benchmark 收口

- 按用户要求继续完成未完成任务前，重新读取 `task_plan.md`、`findings.md`、`progress.md` 与 `docs/research/ACTIVE_FRONTS.md`，确认当前高价值遗漏集中在外部 oracle/PyJHora 黑盒证据包、pending packets、benchmark dashboard 与 Shadbala 组件边界。
- 先写红灯测试 `tests/test_oracle_benchmark_inventory.py`，要求项目能机器化索引 oracle registries、oracle cases、pending packets、PyJHora artifacts、manifest 与 dashboards。
- 新增 `scripts/oracle_benchmark_inventory.py`，生成 `oracle_benchmark_single_truth_inventory`，把 `references/oracle/`、`references/oracle/cases/`、`references/oracle/artifacts/pending_packets/` 与 dashboard 文件折叠成单一 JSON/Markdown 真相入口。
- 生成 `docs/research/oracle_benchmark_inventory_latest.json` 与 `docs/research/oracle_benchmark_inventory_latest.md`，当前索引统计为 3 个 oracle registry、9 个 oracle case、19 个 pending packet、8 个 PyJHora 黑盒 artifact、4 个 dashboard。
- 更新 `docs/research/ACTIVE_FRONTS.md` 的 Oracle Closure 入口，要求后续修改 oracle-dependent adjudicator 或 benchmark claims 前先运行 `python3 scripts/oracle_benchmark_inventory.py --format json`。
- 收口上一轮遗留的 finance Shadbala 组件审计：`mcp_server.py` 对 `shadbala.planets` 要求 `sthana/dig/kala/chesta/naisargika/drik` 六分量，缺失时 `confidence_cap = low` 且进入 `secondary_context += ["shadbala_component_gap"]`；补文档 `docs/research/shadbala_component_confidence_cap_v1_2026_06_28.md`。
- 验证：`python3 -m pytest tests/test_oracle_benchmark_inventory.py -q` 通过；`python3 -m pytest tests/test_mcp_strict_workflow_finance.py -q` 24 项通过；`python3 -m json.tool docs/research/oracle_benchmark_inventory_latest.json` 通过。
## 2026-06-28T18:27:42+08:00 - 全仓工作流遗漏扫描

- 读取并恢复 `task_plan.md`、`findings.md`、`progress.md`，确认当前已有“整机与 Git 云端地毯式遗漏审计”上下文。
- 执行仓库规模扫描：排除 venv/build/dist/cache 后约 1528 个文件，重点检查 docs/references/scripts/tests/jyotish-app/scratch。
- 执行 `python3 scripts/audit_fragments.py --strict`：注册表 89 技法的产品表面审计通过，问题数 0；候选碎片仍为 `oracle_functional_benefics.py`、`patch_api_tz.py`、`patch_engine_tz.py`。
- 执行 quick quality gate 时发现 `test_skill_map_surfaces_functional_benefic_malefic_audit_row` 红灯，根因为功能性吉凶层未在前端 Skill Map / Technique Audit Table 可见化；补齐后聚焦测试通过。
- 分类未跟踪残留 11 个，其中多数为 scratch/个人输出；`tests/test_dasha_raman_truth.py` 是未纳入 CI 的测试候选；`tests/verify-results-v6.1.json` 和中文报告应移出 tests 或明确接入测试。
- 复核 `ACTIVE_FRONTS.md` 与 `vedastro_parity_matrix_latest.md`：仍有 Vimsopaka 高阶语义映射、Functional role 审计表渲染后续、VedAstro adapter endpoint smoke、Life Event Graph、报告渲染等未闭合工作。
- 验证：`python3 scripts/run_quality_gate.py --profile quick --skip-frontend-runtime` 通过；`npm run build` 通过；`python3 -m pytest tests/ -q` 通过；`git diff --check` 通过。

## 2026-06-28T18:58:00+08:00 - 碎片残留与 Functional/Synastry 桥接收口

- 将散落在根目录和 `scripts/` 的临时输出、scratch 脚本、一次性 timezone patch 脚本移动到 ignored `scratch/local/...`，不再污染产品脚本面。
- 将旧 `tests/verify-results-v6.1.json` 与中文婚恋验证报告移动到 `docs/benchmark/legacy-marriage-v6.1/`，新增 README 标明它们是历史 benchmark evidence，不是 pytest。
- 将未成熟的 Raman Dasha oracle pytest 草稿改写为 `benchmarks/jyotish/reports/drafts/raman_dasha_oracle_draft_2026_06_28.md`，保留目标日期但明确 promotion boundary，避免被误纳入 CI。
- `oracle_functional_benefics.py` 新增 CLI JSON 合同测试；`python3 scripts/audit_fragments.py --strict` 显示 candidate_count 从 3 降到 0。
- Functional Benefic/Malefic 的 `Technique Audit Table` 与 real-reading checklist 现在显式要求/输出 `functional_neutrals` 与 `yogakarakas`。
- 合婚 strict bridge 修复 `additional_kutas.BadConstellations` 的 nested dict 形态，并把 mitigation exceptions 折叠成 `exception_mitigated_match`，防止已有 Ashtakoot 细节资产在 relationship adjudicator 中被吞掉。

## 2026-06-28T20:05:00+08:00 - REDACTED_YEAR REDACTED_PLACE真实用户全功能 QA

- 按用户要求以 `REDACTED_DATE REDACTED_TIME`、中国河北REDACTED_PLACEREDACTED_PLACE矿区近似坐标 `lat=36.4467 lon=114.2 tz=8` 跑真实用户全功能验收；scratch 产物放在 `scratch/local/sample_user_qa_2026_06_28/`。
- CLI 矩阵覆盖 30 条出生盘/事件/合盘/问事/年运/分盘命令，28 条通过；失败为 `varga-full --divisions` 高分盘 D81/D108/D144 路由旧实现、`muhurta` CLI tuple longitude 崩溃。
- API 矩阵覆盖 42 个请求，40 个通过；`/api/remedies` 对数值型 Shadbala 简写返回 500，官方 catalog payload 可通过；`/api/technique_example` 用 catalog example payload 通过，普通出生资料直打 400 归类为合同边界。
- 前端真实浏览器 `python3 tests/run_frontend_click_smoke.py --mode all --timeout 420` 通过，覆盖 core/mobile/offline/pdf/workspace/mobile-trust/import-files；`npm run build` 通过。
- 工程守门通过：`python3 scripts/audit_capabilities.py --mode validate` 有效；`python3 scripts/audit_fragments.py --strict` 有效且 candidate_count=0；`python3 scripts/run_quality_gate.py --profile quick --skip-frontend-runtime` 通过，配置内 283 项 pytest 通过。
- 新增正式报告 `docs/research/sample_user_full_function_qa_REDACTED_YEAR_redacted_place_2026_06_28.md`，下一步优先修复 `muhurta` CLI、`varga-full --divisions` 高分盘合同、`/api/remedies` 输入硬化，并单独处理当前 dirty worktree/scratch 残留。

## 2026-06-28T21:25:00+08:00 - VedAstro 596+/Events 高频雷达强制合同

- 用户明确要求必须使用外部 VedAstro 596+ 高频流年 API；本轮不把它误解成要本地硬复刻 596 个函数，而是把 VedAstro 作为外部高频 timing radar 接入 strict workflow 边界。
- 复核官方公开面：`APIBuilder.html` 对应通用 calculator surface；`EventsChartAPIBuilder.html` 元数据写明 `SearchEvents / GetEventTiming / ListEventTypes`、400+ pre-defined events，并有 `Scan precision (hours)`；PyPI `vedastro` 当前观测版本为 `1.23.25`。
- `scripts/vedastro_service_adapter.py --print-schema` 新增 `vedastro_calculation_coverage`，记录 `596+` Python calculations、`600+` API Builder calculators、`400+` Events Builder events、三事件方法，以及 `high_frequency_life_event_radar` 用途。
- VedAstro range-scan preview 现在显式包含 `vedastro_event_method = SearchEvents`，并继续通过 `VEDASTRO_API_ENDPOINT` 与 `VEDASTRO_ENABLE_NETWORK` 做外部服务边界控制。
- `mcp_server.py` 中 `career / relationship / finance` 的 strict workflow 现在把 `external_activation` 视为必需 VedAstro 外部雷达槽；缺失时输出 `missing_required_external_radar`、`vedastro_range_scan_missing` 和 `Technique Audit` blocked 行；有事件时输出 `used` 行和 event_count。
- 守住边界：VedAstro 事件证据不直接替代本地双重大运、分盘、Shadbala/Ashtakavarga/Jaimini/Functional role，也不直接设置 `dominant_label / payout_label`；缺本地 promise 时仍受原评分上限约束。
- 新增审计文档 `docs/research/vedastro_required_high_frequency_radar_contract_2026_06_28.md`。
- 验证：`python3 -m pytest tests/test_vedastro_service_adapter_executor.py tests/test_vedastro_external_technique_evidence.py tests/test_vedastro_parity_matrix.py tests/test_vedastro_adapter_candidate_guard.py -q` 通过；`python3 -m pytest tests/test_mcp_strict_workflow_finance.py tests/test_mcp_strict_workflow_relationship.py tests/test_mcp_strict_workflow_career.py tests/test_life_event_graph_v1.py -q` 通过。

## 2026-06-29T00:00:00+08:00 - VedAstro Adapter MVP 方案 A 收口

- 按用户批准的方案 A 执行：在 `scripts/vedastro_service_adapter.py` 中补齐外部 range scan 的 `request_hash`、`response_hash`、`called_at`、`endpoint_host`、`artifact_path`、`attempt_count`、`retry_error_codes`、allowlist/raw/filtered event counts，并把归一化结果写入 `scratch/local/vedastro_adapter/` evidence artifact。
- 新增安全状态面：`/api/vedastro/status` 只暴露配置状态、网络开关、endpoint host、live profile、artifact 目录与最新 artifact，不泄露完整 endpoint；Trust Center 运行健康检查时读取该状态并显示 VedAstro 外部雷达是否 live-ready / network-disabled / endpoint-missing。
- 质量门新增 `vedastro-live` profile：默认跳过浏览器重活和本地重型审计；没有 `VEDASTRO_API_ENDPOINT` 或 `VEDASTRO_ENABLE_NETWORK=1` 时输出受控 `blocked`，配置齐全后才执行真实 VedAstro range scan smoke。
- MCP strict workflow 不再要求人工把 adapter 结果重包装到 `external_activation`：`modules.vedastro_range_scan_result` 现在可直接进入 external activation ledger，并保留 adapter provenance；该外部雷达仍不覆盖本地双重大运、分盘、Shadbala/Ashtakavarga/Jaimini/Functional role，也不直接改写评分标签。
- 方案 A 文档与计划：新增 `docs/superpowers/plans/2026-06-29-vedastro-adapter-mvp.md`；`README.md` 记录 `vedastro-live` 命令。
- Fresh verification：`git diff --check` 通过；`python3 -m py_compile scripts/vedastro_service_adapter.py scripts/jyotish_api_server.py scripts/run_quality_gate.py mcp_server.py` 通过；`env -u VEDASTRO_API_ENDPOINT -u VEDASTRO_ENABLE_NETWORK python3 scripts/run_quality_gate.py --profile vedastro-live` 通过且明确返回 `status=blocked` / `reason=vedastro_live_endpoint_or_network_flag_missing`；`python3 scripts/run_quality_gate.py --profile quick --skip-frontend-runtime` 通过，配置内 295 项 pytest 通过；VedAstro/MCP/Life Event Graph 聚焦 33 项通过；strict workflow 58 项通过；`npm run build --prefix jyotish-app` 通过。
- 剩余诚实边界：本机尚未配置 VedAstro 官方实网 endpoint，因此只能说 adapter、状态面、artifact/provenance、重试、质量门和下游 strict workflow 已闭环；不能声称 VedAstro 官方 live smoke 已实际命中官方服务。

## 2026-06-29T05:30:00+08:00 - VedAstro 普通用户可点击入口

- 用户追问“普通用户是否可以用上 VedAstro”后，确认上一阶段只是底层/状态面已接好，普通用户还缺按钮式入口；本轮按最小产品入口继续补齐。
- 新增 `docs/superpowers/specs/2026-06-29-vedastro-user-range-scan-design.md` 与 `docs/superpowers/plans/2026-06-29-vedastro-user-range-scan.md`，约束 UI 必须使用当前星盘出生资料，不跑硬编码 demo case。
- 后端新增 `/api/vedastro/range_scan`：支持 `career / relationship / finance` UI domain，映射到 adapter 的 `career / marriage / wealth`；验证出生资料、日期范围、坐标、时区后调用 `vedastro_service_adapter.run_range_scan_for_case()`。
- 前端新增 `window.JyotishAPI.runVedAstroRangeScan()`，Trust Center 增加 `VedAstro Range Scan` 面板，用户生成星盘后可选择领域与日期范围点击“运行 VedAstro 外部雷达扫描”；结果会显示 status/event count/artifact 或 blocked reason，并写入 `chartData.modules.vedastro_range_scan_result`。
- 实测 HTTP：未配置 `VEDASTRO_API_ENDPOINT` / `VEDASTRO_ENABLE_NETWORK` 时，`POST /api/vedastro/range_scan` 返回 `success=true`、`ui_domain=relationship`、`adapter_domain=marriage`、`result.status=service_endpoint_not_configured`，且 request_preview 使用用户 `REDACTED_DATE REDACTED_TIME`、REDACTED_PLACE坐标与 Lahiri/mean node。
- Fresh verification：新增后端红灯测试先 404 后转绿；新增前端静态红灯测试先缺 bridge 后转绿；VedAstro/API/frontend 聚焦 19 项通过；`npm run build --prefix jyotish-app` 通过；`python3 scripts/run_quality_gate.py --profile quick --skip-frontend-runtime` 通过，当前 quick 集合 297 项 pytest 通过；`git diff --check` 与 `py_compile` 通过。
- 剩余诚实边界：普通用户现在可以点击使用 VedAstro 入口，但在服务端未配置官方 endpoint 和网络开关前，产品显示的是 blocked 边界；要看到真实 VedAstro 事件结果仍需配置 `VEDASTRO_API_ENDPOINT` 与 `VEDASTRO_ENABLE_NETWORK=1`。

## 2026-06-29T07:20:00+08:00 - VedAstro 596+ 最快路径矩阵收口

- 新增 `scripts/vedastro_python_bridge.py`：自动发现 `venv_vedastro`，兼容官方实际模块名 `vedastro`，并可通过 typed params 直接调用 `Calculate.*` 方法；live smoke 已验证 `PlanetNirayanaLongitude(Sun, REDACTED_DATE REDACTED_TIME, REDACTED_PLACE)` 返回官方结果。
- 新增 `scripts/vedastro_method_catalog_sync.py`：真实从官方 `GetAllEventDataGroupedByTag` 拉取 catalog 并写入 `scratch/local/vedastro_adapter/method_catalog_snapshot.json`；当前快照统计为 `tag_count=46`、`method_count=2258`。
- 扩展 `scripts/vedastro_parity_matrix.py` 与 latest 文档：新增 `fastest_path_lane` / `route_notes`，把高价值能力明确分流到 `official_mcp`、`official_python_bridge`、`rest_adapter`、`local_native_preferred`、`hybrid_router`、`external_evidence_only` 六条执行车道。
- 新增 `scripts/vedastro_fast_path_checklist.py` 与 `docs/research/vedastro_fast_path_checklist_latest.{md,json}`，正式沉淀“VedAstro 596+ 节点接入实施清单（按最快路径）”。
- 路由真相当前冻结为：`MCP/API Surface -> official_mcp`；`Shadbala / Ashtakavarga / Tajika -> official_python_bridge`；`EventsAtRange / Birth Time ML -> rest_adapter`；`D1-D60 / Jaimini / Synastry / Prashna -> local_native_preferred`；`Ayanamsa -> hybrid_router`；`Numerology -> external_evidence_only`。
- Fresh verification：`python3 -m pytest tests/test_vedastro_parity_matrix.py tests/test_vedastro_fast_path_checklist.py tests/test_vedastro_python_bridge.py tests/test_vedastro_method_catalog_sync.py tests/test_vedastro_range_scan_replay.py tests/test_vedastro_service_adapter_executor.py tests/test_vedastro_external_technique_evidence.py -q` 通过；`python3 scripts/vedastro_parity_matrix.py --write` 与 `python3 scripts/vedastro_fast_path_checklist.py --write --format markdown` 通过。

## 2026-06-29T07:45:00+08:00 - 官方 MCP 真接入与 career 骨架收口

- 新增 `scripts/vedastro_official_mcp_bridge.py`：以官方公共端点 `https://mcp.vedastro.org/api/mcp/public` 为默认入口，提供极薄的 `initialize` / `tools_list` 两个操作，只负责官方 MCP 可达性与工具发现，不允许外部 MCP 结果直接改写本地 `score / dominant_label / payout_label`。
- 新增 `tests/test_vedastro_official_mcp_bridge.py`：用本地 mock MCP 服务验证 `Mcp-Session-Id` 透传与 `tools/list` 结果归一化，确保这不是“手写文档假接入”。
- `scripts/vedastro_python_bridge.py` 继续往高价值方法层推进：新增 `--high-value` 快捷层，先把 `event_tag_catalog -> GetAllEventDataGroupedByTag`、`planet_longitude -> PlanetNirayanaLongitude`、`vimshottari_snapshot -> DasaAtTime` 收成稳定入口；`GetCharaDasaAtTime` 的真实调用形状仍在核对，不会把半通状态混进完成声明。
- 实测真相：官方公共 MCP `initialize` 与 `tools/list` 已通过真实 HTTP 返回；Python bridge 的 `DasaAtTime` 通过 positional args 已成功返回 Vimshottari 快照；`GetCharaDasaAtTime` 的 bound-method 形状已进一步探明，其真实桥接仍需按 positional contract 单独收口，但不再属于“完全未知调用面”。
- 本地主线真相同步：补齐 `references/event_judgment_career.md`，并将其挂入 `SKILL.md`、`references/quick-reference-guide.md` 与 `docs/research/ACTIVE_FRONTS.md`。这意味着 career 线不再缺“专用裁决骨架”，后续尾巴集中在裁决细化、报告渲染与 oracle 闭环，而非入口缺失。
- Fresh oracle status re-check：`python3 scripts/oracle_closure_master_dashboard.py --format json` 当前显示 `12` 个总任务中 `8` 个已 external_verified、`4` 个未闭合；未闭合核心已收缩到 `tajika_sahams` 前线，而非 Dasha/Shadbala 主前线。`python3 scripts/public_benchmark_dashboard.py --format json` 当前显示 `valid_packets=5`、`ready_for_calibration=5`、`production_tuning_allowed=false`，因此仍不能宣称全局 oracle 已封顶。

## 2026-06-29T08:20:00+08:00 - 项目进度深度检测

- 按用户要求深度检测当前印度占星项目进度；读取 `task_plan.md`、`findings.md`、`progress.md`、`ACTIVE_FRONTS.md`、VedAstro parity/fast-path 文档与 oracle benchmark inventory。
- Git 状态确认：当前分支 `codex/release-hygiene-ci` 与远端同步，HEAD 为 `d0af9f4 Productize VedAstro user range scan entry`，工作区无未提交 diff。
- 能力面确认：`python3 scripts/audit_capabilities.py --mode validate` 通过，注册表 `89` 个技法中 `10 complete / 79 covered / 0 missing / 0 partial / 0 not-integrated`。
- 碎片面确认：`python3 scripts/audit_fragments.py --strict` 通过，`engine_command_count=37`、`api_endpoint_count=43`、`candidate_count=0`、`untracked_count=0`。
- Oracle 面确认：`oracle_closure_master_dashboard` 显示 `12` 个任务中 `8` 个 external_verified、`4` 个 open；Dasha 与 Shadbala 当前可声明对应 front closure，但全局 oracle closure 仍为 false，生产调参仍不允许。
- VedAstro 面确认：当前已进入可点击用户入口和 adapter/provenance 阶段；官方 MCP/Python bridge 有真实可达记录，REST range scan 的官方 endpoint smoke 仍依赖 `VEDASTRO_API_ENDPOINT` 与 `VEDASTRO_ENABLE_NETWORK=1`。
- 质量门确认：`python3 scripts/run_quality_gate.py --profile quick --skip-frontend-runtime` 通过，聚焦集合 `297 passed`；`env -u VEDASTRO_API_ENDPOINT -u VEDASTRO_ENABLE_NETWORK python3 scripts/run_quality_gate.py --profile vedastro-live` 通过但返回受控 `blocked`，不得宣称官方实网 VedAstro range scan 已闭环。
- 当前最值钱下一步：继续推进 VedAstro range scan 的官方样本调参和 EventTagList 映射质量，同时补 Tajika/Sahams 4 个未闭合外部 oracle 任务；之后再处理 Vimsopaka 高阶语义映射、Life Event Graph v1 产品化和报告渲染 polish。

## 2026-06-29T23:57:36+08:00 - 高严谨默认入口复用接线

- 按用户要求先做地毯式扫描：读取既有计划/发现/进度、运行 `preflight_fragment_scan.py`、`audit_fragments.py --strict`、`audit_capabilities.py --mode validate`，确认主仓已有校时、历史事件回测、主题推运、VedAstro 官方证据层，不需要重写算法。
- 新增 `/api/high_rigor_workflow`：复用 `/api/chart` 的 VedAstro official-first 主入口、`/api/rectification_gate`、`scripts/historical_event_backtest.py`、`/api/thematic_report`，输出 source priority、reused modules、VedAstro catalog summary、rectification、historical backtest、thematic report。
- 为 API Explorer 增加 `dry_run` plan-only 样例，避免目录页意外触发重型 VedAstro/full-reading 链路；真实用户请求不带 `dry_run` 才执行完整高严谨链路。
- 将 `high-rigor-workflow` 挂到已有 `thematic_report_orchestrator` 注册表命令上，能力总数保持 89，不新增伪技能。
- 验证：新增高严谨 workflow 合同测试通过；Technique Catalog 入口测试通过；相关 4 项 API 回归通过；`audit_capabilities.py --mode validate` 仍显示 `technique_count=89`、`10 complete / 79 covered / 0 missing`；`py_compile` 通过。

## 2026-06-30T00:34:00+08:00 - VedAstro 641 项轻量映射表

- 在 `scripts/vedastro_official_capability_runner.py` 给 `official_full_capability_catalog` 增加轻量路由元数据：每个官方方法返回 `domains`、`execution_policy`、`priority`，总报告返回 `domain_routing`。
- 映射策略按方法名、签名、bucket 和参数名做保守分类：`career / marriage / wealth / rectification / timing / general`；`MatchReport` 等需要伴侣资料的方法保留为 `needs_user_context`，不进入自动高优先级列表。
- 修正 `Dashamamsha` 字符串误判：D10 分盘类能力不再因为包含 `dasha` 字符串被归入 timing；真实 641 轻扫显示 `AllPlanetDashamamshaSign` 只归入 `career/marriage/wealth`。
- 将 `domain_routing` 从 service adapter 透传到 `VedAstroEvidenceOrchestrator`、`jyotish_api_server.py` 和 `jyotish_engine.py` 的官方证据摘要，网页/Skill/MCP 共享入口可以消费同一张路由表。
- 验证：官方 runner 映射测试、orchestrator 透传测试、full snapshot 透传测试、高严谨 API 摘要测试共 5 项通过；`py_compile` 通过；`audit_capabilities.py --mode validate` 仍为 `technique_count=89`、`10 complete / 79 covered / 0 missing`；`VEDASTRO_FULL_CATALOG_SAMPLE_LIMIT=0` 真实轻扫读到 `catalog_method_count=641`、`domain_routing_count=6`。

## 2026-06-30T01:05:00+08:00 - VedAstro 动态选择器与报告引用层

- 在 `official_full_capability_catalog` 返回中新增 `dynamic_selection`：按请求主题从 641 项官方能力里选择 Top N，保留 `selected_methods`、`needs_user_context_methods`、`needs_user_text_methods`、`needs_rectification_profile_methods`、`blocked_methods`。
- 每个被选能力生成稳定引用 ID：`vedastro:<theme>:<method>`；每个主题生成 `report_reference`，包含 `citation_ids`、自动可用数量、需补资料数量和 blocked 数量。
- 将 `dynamic_selection` 从 service adapter 透传到 `VedAstroEvidenceOrchestrator`、`jyotish_api_server.py` 和 `jyotish_engine.py`；高严谨入口和 prompt pack 现在能输出 `official_report_references`。
- 真实 641 轻扫验证：`dynamic_selection_theme_count=5`；示例引用包括 `vedastro:career:EventsAtRange`、`vedastro:marriage:EventsAtRange`、`vedastro:timing:EventsAtRange`、`vedastro:timing:DasaAtRange`；婚恋主题标出 `marriage_needs_context=9`。
- Fresh verification：6 个聚焦 pytest 通过；`py_compile` 通过；`audit_capabilities.py --mode validate` 仍为 89 项技能、0 problem、0 warning；`git diff --check` 通过。

## 2026-06-30T02:30:00+08:00 - Top-reader adjudication contract 通贯

- 在 `mcp_server.py` 的 career / relationship / finance strict workflow 上统一接入共享 `adjudication_stages`（promise -> activation -> manifestation -> label）与 `multi_reference_reading_summary`，并把 `verdict`、`dominant_label`、`main_conflicts` 作为轻量可消费合同输出。
- `scripts/jyotish_engine.py` 的 prompt-pack 压缩层已透传上述合同，因此 `ai_prompt_pack.evidence_snapshot.vedastro_official_full_snapshot.strict_workflow_contracts[*]` 不再只包含官方/本地/blocked 元信息，也能给出顶层裁决骨架。
- `scripts/jyotish_api_server.py::_high_rigor_vedastro_official_summary()` 现优先从 `vedastro_official_full_snapshot` 读取 strict contract，并把 `strict_workflow_primary_route`、`strict_workflow_contracts`、`adjudication_stages`、`multi_reference_reading_summary`、`verdict`、`dominant_label`、`main_conflicts` 直接暴露给 consultation/high-rigor 用户层摘要。
- `scripts/historical_event_backtest.py` 现会把 strict contract 的 `adjudication_stages`、`multi_reference_reading_summary`、`main_conflicts` 继续写进每条事件 evidence，避免回测结果只看 hit/miss 却丢失裁决骨架。
- 前端 `jyotish-app/main.js` 与 `jyotish-app/ai-chat.js` 已消费同一套合同：Prompt Pack 面板会显示 Top-reader adjudication 摘要与 multi-reference frame keys，AI Chat 上下文会附带 `【Top Reader Contract】` 边界，网页/app 与 skill 对话入口看到的是同一份官方优先证据结构。
- Focused verification：
  - `python3 -m pytest tests/test_mcp_strict_workflow_career.py tests/test_mcp_strict_workflow_relationship.py tests/test_mcp_strict_workflow_finance.py tests/test_cli_smoke.py::test_full_reading_reports_ayanamsa_metadata_and_ai_prompt_pack tests/test_vedastro_official_full_snapshot.py::test_full_reading_prompt_pack_exposes_vedastro_official_snapshot_boundary tests/test_api_server_security.py tests/test_historical_event_backtest.py tests/test_frontend_productization.py -k "adjudication_stages or multi_reference_reading_summary or top_reader_contract or modifier_frame" -q` -> `9 passed`.
- 完成“官方日窗口 -> 用户可读日期信号”最小翻译层接回默认主链：
  - `mcp_server.py` 的 `external_activation` 现会基于 `daily_windows` 派生 `official_day_signals`
  - 当前最小标签为：
    - 事业：`事业机会日 / 事业风险日 / 事业混合日`
    - 婚恋：`婚恋推进日 / 婚恋风险日 / 婚恋混合日`
    - 财富：`财富机会日 / 财富风险日 / 财富混合日`
  - 这层只复用已有 `signal_families + top_signal_label + confidence + score`，没有新造重推理器
- strict workflow compact contract 现已保留 `official_day_signal_summary`，因此这层不会只存在于原始 `present_evidence.external_activation` 里。
- `scripts/guided_topic_discovery.py` 已把 `official_day_signal_summary` 压进每条 guided topic；`jyotish-app/main.js` 的 guided topic 卡片会直接显示最重要的官方日期提示；`jyotish-app/ai-chat.js` 也会把这层塞进 guided topic chat payload，后续追问不再丢失。
- 新增并跑通的定点回归：
  - `python3 -m pytest tests/test_mcp_strict_workflow_career.py::test_career_external_activation_derives_user_readable_day_signals tests/test_mcp_strict_workflow_relationship.py::test_relationship_external_activation_derives_progress_day_signals tests/test_mcp_strict_workflow_finance.py::test_finance_external_activation_derives_wealth_day_signals tests/test_cli_smoke.py::test_full_reading_guided_topics_can_carry_official_day_signal_summary tests/test_frontend_productization.py::test_guided_topic_questions_reuse_ai_chat_entry -q`

## 2026-07-01T19:40:00+08:00 - 外部官方细算 sanity / 三方 oracle 闭环账本

- 新增 `scripts/external_oracle_sanity_closure.py`：把 VedAstro official precision sanity、PyJHora black-box artifact ledger、jyotishganit MIT reference layer 统一成可审计 JSON/Markdown 账本。
- 当前三方状态：PyJHora `ok`（12 artifacts / 8 packets）、jyotishganit `ok`（MIT source + benchmark available）、VedAstro `blocked`（longitude sanity 通过，但 official full snapshot 细算仍返回 `official_snapshot_budget_exhausted`，不能宣称 fully closed）。
- 新增 `tests/test_external_oracle_sanity_closure.py`，并将 sanity closure 纳入 `scripts/run_quality_gate.py` 的 oracle audit 链路；README 增加总控命令。
- 生成 `docs/benchmark/external_official_sanity_oracle_closure.{md,json}` 作为当前快照；诚实边界为 `can_claim_fully_closed=false`、`can_claim_high_rigor_with_blocks=true`。
- 为避免质量门被 VedAstro 免费层节流长时间阻塞，sanity closure 默认只跑非阻塞官方证据审计；真实 official full snapshot 细算保留为显式 `--live-official-full-snapshot` 开关。

## 2026-07-01T20:35:00+08:00 - 第四批 repo truth 升格包

- 新增 `docs/research/promote_fourth_repo_truth_pack_2026_07_01.md`，把 5 份高价值草稿锚回主仓真源：Round40 whole-machine fragment shortlist、Dasha accuracy closure status、Dasha code-only priority rerank、skill fragment source-of-truth map、skill truth conflict matrix。
- 将第四批挂入 `docs/research/repo_cleanup_promotion_map_2026_07_01.md` 与 `docs/research/ACTIVE_FRONTS.md`，避免后续只看到前三批升格包。
- 新增治理守门：`tests/test_research_governance_docs.py` 检查第四批 pack 的关键锚点，`tests/test_preflight_fragment_scan.py` 检查第四批 5 份草稿不再出现在 high-value unpromoted pool。
- TDD 红灯确认：第四批 pack 缺失时治理测试失败，preflight 仍列出第四批草稿；补齐后两条测试通过。
- `python3 scripts/preflight_fragment_scan.py` 当前显示 `high_value_unpromoted_count=16`，已从第三批后的 `21` 下降 5 项；剩余主要是 skill/cloud sync 草稿和 Gemini recovery-only VedAstro artifacts。

## 2026-07-02T11:26:34+08:00 - 解释资料层调用链审计启动

- 按用户要求，在任何实现前先做只读地毯式探索：读取 `AGENTS.md`、`SKILL.md`、`task_plan.md`、`findings.md`、`progress.md`、strict router、MEVG、event skeleton、解释模板注册表、P1-P12、house framework 与现有 strict workflow 代码。
- 当前主仓验证：`validate_interpretation_templates.py --format json` 通过；`audit_capabilities.py --mode validate` 通过；`audit_fragments.py --strict` 通过。
- 跨目录验证：当前主仓和 `.workbuddy/skills/jyotish-vedic-astrology` 的 `planet-house-details-a/b/c.js` SHA256 一致；资料库中存在 BPHS/Raman PDF；云端 HTTPS refs 显示本地与远端 `codex/release-hygiene-ci` HEAD 对齐。
- 根因假设冻结：资料和规则本来存在，但 strict workflow / prompt pack 缺少“解释资料源包 + MEVG/真实案例门控行”的显式 evidence contract 与红灯测试；下一步按 TDD 只补调用链和测试。

## 2026-07-02T11:31:43+08:00 - 解释资料层显式调用链接入

- TDD 红灯：新增 career/relationship/finance 三条 strict workflow 测试，均因 `present_evidence.interpretation_source_pack` 缺失失败；新增 CLI prompt pack 检索文档断言，因未列出解释资料层失败。
- 最小实现：`mcp_server.py` 新增 `_existing_interpretation_source_pack()`，把现有 `interpretation_template_registry`、P1-P12、house framework、Raman/BPHS、MEVG、真实案例 checklist、前端 planet-house-details 作为只读 evidence pack 挂入 career/relationship/finance strict workflow；`technique_audit_summary` 新增 `interpretation_source_pack`、`mevg_global_web_evidence`、`real_case_calibration` 三行。
- Prompt pack：`scripts/jyotish_engine.py` 的 `technique_audit_table` 新增 `Interpretation Source Pack`、`MEVG / Global Web Evidence`、`Real Case Calibration`；`retrieval_plan.local_reference_docs` 显式列出对应本地资料路径。
- 红绿验证：5 条新增/修改聚焦测试通过；随后 `tests/test_mcp_strict_workflow_career.py tests/test_mcp_strict_workflow_relationship.py tests/test_mcp_strict_workflow_finance.py tests/test_mcp_strict_workflow_functional_layer.py -q` 通过，合计 86 项；`validate_interpretation_templates.py --format json` 仍为 `valid=true`、`template_count=11`。

## 2026-07-02T14:05:00+08:00 - 全量解释资料分级审计启动

- 用户要求把此前机器审计发现的 922 个未分级候选资料逐批分类。
- 范围优先级：先处理 references/、references/real_case_studies/、references/open_source_sources/rishi-ai-mcp、references/open_source_sources/vedic-astro-skills；普通 docs/research 流水账只分桶，不升格。
- 实施策略：扩展 interpretation_source_inventory_gate，生成可复现 full_classification 报告；用测试确保重点层被分级、local_drafts/research 流水账不会误进 primary truth。

## 2026-07-02T14:18:00+08:00 - 全量解释资料分级审计完成第一版

- 扩展 `scripts/interpretation_source_inventory_gate.py`：现在输出 `full_classification`，对解释/规则/案例/模板/证据候选逐项给出 classification、priority、promotion_status 与 reason。
- 当前候选池 `candidate_count=947`，`unclassified_candidate_count=0`；其中 runtime 25、priority_1 264、priority_2 101、priority_3 557。
- 重点优先层已覆盖：`references/` -> reference_candidate，`references/real_case_studies/` -> real_case_calibration，`open_source_sources/rishi-ai-mcp` 与 `vedic-astro-skills` -> open_source_reference。
- 普通研究流水账与本地草稿已降级：`docs/research` -> research_governance，`docs/research/local_drafts` -> quarantined_draft / not_truth_source。
- 新增快照文档：`docs/research/interpretation_source_full_classification_2026_07_02.md`。

## 2026-07-02T14:44:00+08:00 - priority_1 references 第一批升格审计

- 从 `references/` 的 priority_1 `reference_candidate` 中挑出 30 个最像规则源头的文件，形成第一批升格审计包。
- 新增机器可测审计 JSON：`docs/research/interpretation_source_priority1_batch1_promotion_audit_2026_07_02.json`。
- 新增人读审计说明：`docs/research/interpretation_source_priority1_batch1_promotion_audit_2026_07_02.md`。
- 当前处置：`promote=16`、`reference-only=6`、`obsolete=3`、`duplicate=3`、`quarantine=2`。
- 明确边界：本批只做 audit-only 分级，不直接接入 runtime source pack；后续升格仍需调用链、冲突仲裁、可见性测试。

## 2026-07-02T15:05:00+08:00 - priority_1 promote 核心 5 源头调用链接入

- 将第一批 promote 中的 5 个全局核心源头显式接入 `_existing_interpretation_source_pack()`：`prediction-boundary-protocol`、`event_judgment_skeleton`、`planetary-dignity-complete-reference`、`retrograde-combustion-war-guide`、`transit-multi-reference-guide`。
- 新增 `core_rule_source_layer` 与 inventory `core_rule_sources` 层，标记为 `priority1_batch1_core5` / `primary_truth_candidate`。
- `technique_audit_summary.interpretation_source_pack` 现在直接暴露 `core_rule_source_refs`，career / relationship / finance strict workflow 都能看到同一组核心源头。
- 新增 `tests/test_interpretation_source_core5_strict_visibility.py`；同时加固 `tests/test_interpretation_source_inventory_gate.py` 对核心层的断言。
- 边界仍保留：核心 5 已进入调用链可见性层，但具体解释仍需冲突仲裁、MEVG、真实案例校准和领域分盘/大运证据。

## 2026-07-02T15:42:00+08:00 - 核心 5 内容级调用与第二批资料层闭环

- 核心 5 不再只是可见：career / relationship / finance strict workflow 现在生成 `prediction_boundary_contract`，强制绑定 `promise -> activation -> manifestation -> label`、MEVG blocked、Real Case Calibration blocked 与核心 5 source refs。
- 第二批 promote 11 个专题源头已接成 `promote_batch2_topic_layer`：Vimshottari、Pratyantar、分盘深读、Shadbala、Ashtakavarga、Tajika、Jaimini、KP、Argala、Badhaka、Condition Dasha。
- `reference-only` 3 个源头已接成 `reference_only_conflict_layer`，只允许作为冲突/参考材料：`dasa-convergence-methodology`、`multi-dasha-convergence-protocol`、`yoga-strength-scoring-system`。
- duplicate / obsolete / quarantine 8 个文件已列入 `blocked_non_runtime_layer`，并由 inventory gate 检查不进入 runtime source refs；重点包括 `kp-practical-event-timing.md` 与 `consultation-case-library.md`。
- Prompt Pack / API fallback / AI Chat 已同步 `prediction_boundary_contract`、核心 5、第二批 11、reference-only 3；AI Chat 上下文新增 `【Prediction Boundary Contract】` 段落。
- 真实 full-reading 回归确认：REDACTED_DATE REDACTED_TIME REDACTED_PLACE矿区样例中 relationship / career / finance 三条 strict contract 均带 prediction boundary，且 MEVG 与真实案例校准仍为 blocked。

## 2026-07-02T16:12:00+08:00 - 第二批领域调用层与后续队列合同

- 第二批 11 个 promote 源头已拆成四个领域调用层：`dasha_timing`、`varga_strength`、`annual_special`、`modifier_obstacle`；career / relationship / finance strict workflow 均暴露 `domain_invocation_contract`。
- 新增 `output_template_contract`，要求最终中文输出按 `promise / activation / manifestation / label / confidence_boundary` 组织；当前以合同和测试约束为主，后续可继续做 golden narrative snapshot。
- 新增 `mevg_collection_queue`，fortune strict workflow 会生成外部采集队列合同：global web evidence、real case search、source grading、conflict arbitration、unverified downgrade。
- 新增 `real_case_calibration_layer`，按 career / finance / relationship / health / rectification / timing 六个桶连接 `references/real_case_studies` 与 `docs/benchmark`。
- 新增 `technical_debt_contract`，诚实标记 Narayana 与 Tajika 仍为 `partial`：Narayana 需 Antardasha/Pratyantar oracle parity，Tajika 需 solar return precision、Muntha placeholder audit 与 annual yoga oracle parity。
- 前端 AI Prompt Pack 新增 `Source Governance` 面板，显示 core sources、reference-only、blocked non-runtime、confidence downgrade、MEVG queue、case calibration、Narayana/Tajika debt 与 next batches。
- 剩余 priority_1 队列明确为：`real_case_studies_batch1`、`rishi_ai_mcp_batch1`、`vedic_astro_skills_batch1`、`references_batch2`。

## 2026-07-02T16:48:00+08:00 - P0-P8 用户可见输出与可执行队列闭环

- P0：`career_narrative`、`finance_narrative`、`relationship_narrative` 的中文 markdown 已强制写出 `promise / activation / manifestation / label / confidence_boundary`，并在真实 full-reading 样例中通过 golden-style 回归。
- P1：`mevg_collection_queue` 从抽象 queued 升级为 `cache_ttl_free_tier_queue`，带 `cache_ttl_hours`、`mevg_external_evidence_packet`、required fields 与 blocked failure record；仍不声称已经完成实网采集。
- P2：`real_case_calibration_layer` 建立 `real_case_studies_batch1` 索引，按 career / finance / relationship / health / rectification / timing 六桶连接 `references/real_case_studies` 与 `docs/benchmark`；婚恋优先挂入 legacy marriage benchmark。
- P3：第二批领域调用层不再只作为 source refs，已进入 `event_judgement.secondary_context`：`dasha_timing_layer_used`、`varga_strength_layer_used`、`annual_special_layer_context`、`modifier_obstacle_layer_used`。
- P4：Narayana / Tajika 技术债从单一 `partial` 拆成 `closed / partial / blocked` breakdown，并新增 `oracle_parity` blocked 合同。
- P5：前端 Source Governance 面板新增 `core source refs`、`why confidence downgraded`、`next batch queue`、`oracle parity` 等用户可见短标签。
- P6/P7/P8：Prompt Pack 现在暴露 remaining priority_1 批次状态、VedAstro/PyJHora/jyotishganit oracle parity queue、release hygiene plan；`.git/gc.log` 仍标记为单独安全清理计划，不随本轮 prune。

## 2026-07-02T16:42:00+08:00 - 字符级资料 manifest 第一阶段

- 新增 `scripts/character_level_inventory_manifest.py`，对项目内重点资料层做轻量字符级索引：`references/`、`references/open_source_sources/`、`docs/research/`、`SKILL.md`、`AGENTS.md`。
- 生成 `docs/research/character_level_inventory_manifest_latest.json` 与 `.md`，当前覆盖 `1069` 个文件：`unhashed_files=0`、`unclassified_files=0`、`unknown_extraction_status=0`。
- 当前分类计数：`open_source_reference=299`、`reference_candidate=180`、`research_governance=439`、`quarantined_draft=93`、`real_case_calibration=5`、`oracle_artifact=51`、`project_governance=2`。
- 当前提取状态：`text_indexed=1032`、`binary_indexed=34`、`image_ocr_queued=3`；本轮为省算力模式，未跑重 OCR，也未跑全机器长扫描。
- 新增 `tests/test_character_level_inventory_manifest.py`，并把 manifest gate 接入 `scripts/run_quality_gate.py`；质量门使用 `--no-write --summary-only`，避免 CI 反复刷新报告或打印全量 `by_path`。

## 2026-07-02T17:08:00+08:00 - 外部高相关资料 manifest 第一阶段

- 扩展 `scripts/character_level_inventory_manifest.py --scope external`，只扫高相关外部路径，不做全机器深扫，不复制私人正文进仓库。
- 新增 `docs/research/character_level_external_manifest_latest.json` 与 `.md`，当前覆盖 `883` 个外部高相关文件：`unhashed_files=0`、`unclassified_files=0`、`unknown_extraction_status=0`。
- 外部来源桶：`~/.workbuddy=767`、`~/文件仓库=43`、`~/WorkBuddy=36`、`~/Downloads=15`、`~/Documents/ObsidianVault=11`、`~/engines-repo=6`、`~/Desktop=5`。
- 外部提取状态：`text_indexed=735`、`text_decode_lossy=2`、`pdf_text_extraction_queued=2`、`document_text_extraction_queued=11`、`image_ocr_queued=50`、`binary_indexed=83`。
- 外部分级：`external_skill_fragment=767`、`external_book_or_document=46`、`external_historical_report=37`、`external_engine_fragment=10`、`external_archive_or_binary=23`；均为 index/reference 阶段，不进入 runtime truth chain。

## 2026-07-02T17:11:00+08:00 - PDF/图片/文档提取队列 manifest

- 新增 `scripts/character_level_inventory_manifest.py --scope extraction-queue`，把项目内与外部 manifest 中的 PDF / 图片 / Office 文档待提取项合并为单独队列。
- 新增 `docs/research/character_level_extraction_queue_latest.json` 与 `.md`，当前 queued_files=`66`、`unhashed_files=0`。
- 队列构成：`image_ocr_queued=53`、`document_text_extraction_queued=11`、`pdf_text_extraction_queued=2`；来源为 `external=63`、`project=3`。
- 边界：本轮只做提取队列，不跑重 OCR，不把外部私人资料正文写进仓库，也不升格为 runtime truth。

## 2026-07-02T17:22:00+08:00 - PDF/DOCX 提取结果与 OCR blocked 分级

- 新增 `scripts/character_level_inventory_manifest.py --scope extraction-results`，对 extraction queue 做实际提取，但只保存文本 hash、字符数、行数、方法、状态和分级，不保存正文。
- 新增 `docs/research/character_level_extraction_results_latest.json` 与 `.md`，当前 total_files=`66`、`unhashed_files=0`、`stored_text_payload_fields=0`。
- 提取结果：`text_extracted=12`、`ocr_blocked_missing_engine=53`、`extraction_failed=1`。
- 方法分布：`docx=11`、`pdfplumber=2`、`pytesseract=53`；系统当前没有 `tesseract` 可执行文件，因此图片 OCR 全部明确 blocked。
- 失败项：`/Users/wuyongnaren/文件仓库/印度占星文章/4印度占星.docx`，`python-docx` 返回 `KeyError: "There is no item named 'NULL' in the archive"`；保留为 extraction_failed，不伪装为已提取。
- 提取后分级：`extracted_candidate_for_review=10`、`extracted_private_reference_only=3`、`extracted_reference_only=53`；仍未进入 runtime truth chain。
