# Antigravity AI 副手任务单 Round 27（2026-06-25）

## 任务目标

用户第一目标不是“多写报告”，而是：**让本地印度占星网页/app 尽快具备同品类应用的完整技能覆盖、可本机运行、可测准确率、解盘边界清楚**。

Round 25/26 已经暴露两个问题：

- 副手有时会给出过强结论，例如把 Panchanga 说成“完全空白”，但当前项目已有 Panchanga range、Muhurta range、Rahu Kala、Choghadiya、CSV/ICS 等底层能力；真实缺口是商业级 UI、节日权威表和外部 oracle。
- Codex 已实现 `python3 scripts/run_quality_gate.py --profile accuracy`，副手需要复核“本地准确率门禁”是否稳定，而不是重复旧失败。

本轮目标：**加大副手任务体量，减轻 Codex 主线程算力压力；把 Round25/26 报告归档、accuracy 门禁稳定性、Shadbala/Kuja/Prompt Pack/Panchanga/Ashtakoot 下一批实现任务拆成可测试票据**。

## 当前事实基线

必须重新验证，不要照搬旧报告：

- 当前工作树已有 Round 25 的 18 份报告、Round 26 的 20 份报告，尚未全部归档提交。
- 当前本地 branch 可能 ahead 1；SSH 22 push 曾超时，必须复核 SSH-443 或 HTTPS fallback。
- `run_quality_gate.py --profile accuracy` 已由 Codex 实现，必须跑最新代码确认。
- `references/validation_logic_report.json` 可能因 Yoga 逻辑报告排序稳定化产生 diff；要判断是否为语义变更。
- Panchanga/Muhurta 不是空白；应区分“已有计算/API/导出”和“缺商业级日历体验/外部对标”。
- Ashtakoot 不是全零；当前 `/api/synastry` 已接入 36 分制本地引擎，但还缺外部 AstroSage/JHora/VedAstro oracle 样本与更完整矩阵核对。

## 联网对标种子

副手必须联网二次确认 license、最新提交和可复用边界；不要只使用下列摘要。

- VedAstro / VedAstro：MIT 候选，C# 主库，可用于 Ashtakoot/Panchanga/API 行为与表格候选复核。https://github.com/VedAstro/VedAstro
- VedAstro open source page：声称 MIT/open-source，可作为许可证与产品定位复核入口。https://vedastro.org/OpenSource.html
- RoxyAPI / jyotish-vedic-astrology-app：MIT Next.js 模板，功能覆盖 Panchang、Ashtakoot、Vimshottari、Dosha，可作为 UI/用户路径对标，不要照抄服务端私有 API。https://github.com/RoxyAPI/jyotish-vedic-astrology-app
- RaviKarrii / Marriage-Compatibility-Asthakoot：MIT Java Ashtakoot 候选，可做 8 Kuta 表格/接口行为参考。https://github.com/RaviKarrii/Marriage-Compatibility-Asthakoot
- naturalstupid / PyJHora：AGPL-3.0，只允许黑盒行为基准、截图/manual oracle，不得复制代码。https://github.com/naturalstupid/PyJHora
- kunjara / jyotish：GPL-2.0+，只允许行为基准，不得复制代码。https://github.com/kunjara/jyotish
- PriyankGahtori / hora-prakash：免费网页 app，对标首屏、Dasha/Panchang/图表交互。https://github.com/PriyankGahtori/hora-prakash
- fusionstrings / panchangam、@ishubhamx/panchangam-js、jayeshmepani/panchang-core、northtara/jyotishganit、pyhora2、jyotishyamitra 等：必须查清 license 后再决定是可复制、可移植、只基准、还是隔离。

## 工作量要求

本轮至少产出 **24 份 round27 报告**，全部写入 `docs/research/`，文件名必须含 `antigravity_round27_*_2026_06_25.md`。

每份报告必须包含：

- 至少 25 个检查点。
- 至少 10 条可复制命令、检索 token、URL、文件路径或代码位置。
- 至少 5 条 Codex 可直接实现的任务，必须含文件路径、测试、验收标准。
- 至少 3 条副手下一轮可继续做的任务。
- 至少 1 条需要人工 JHora/AstroSage/网页截图的任务。
- 状态必须标为：`已成立`、`部分成立`、`未成立`、`误判已纠正`、`需要人工外部工具`。
- 所有开源复用建议必须带 license；只有 MIT/Apache-2.0/BSD/ISC/CC0 可列为可复制候选。
- GPL/AGPL/LGPL/闭源项目只能列为 `benchmark_only`，不得建议复制代码。

## 严格边界

禁止：

- 不要修改 `scripts/`、`tests/`、`jyotish-app/`、`README.md`、`references/` 实现文件。
- 不要提交、推送、重置、删除、移动、覆盖文件。
- 不要读取或传播 token、API key、cookie、SSH 私钥、浏览器登录态、系统钥匙串。
- 不要把用户私人 PDF、Obsidian 完整解盘、Downloads 原文提交或摘录。
- 不要把本地 baseline、模板值、空目标字段或副手推测写成 `external_verified`。
- 不要复制 GPL/AGPL/LGPL/闭源代码。

允许：

- 只能新增 `docs/research/*round27*2026_06_25.md` 报告文件。
- 可以运行只读测试、grep、build、quality gate。
- 可以联网检索公开项目、公开 docs、公开 license。
- 可以读取 `task_plan.md`、`findings.md`、`progress.md`、Round 25/26 报告和地毯式扫描文档。

## 必跑命令

```bash
git status --short --branch
git log --oneline --decorate -n 20
git ls-remote https://github.com/732642856/yinduzhanxing.git 'refs/heads/*' 'refs/tags/*' | sort
python3 scripts/local_accuracy_report.py --format json
python3 scripts/local_accuracy_report.py --format markdown
python3 scripts/run_quality_gate.py --profile accuracy
python3 -m pytest -q tests/test_local_accuracy_report.py tests/test_frontend_productization.py::test_quality_gate_declares_fast_browser_release_profiles tests/test_frontend_productization.py::test_accuracy_quality_gate_runs_local_accuracy_report_without_frontend_click
python3 -m pytest -q tests/test_oracle_evidence_validator.py tests/test_oracle_collection_queue.py tests/test_ashtakoot.py
python3 -m py_compile scripts/run_quality_gate.py scripts/validate_logic_v2.py scripts/local_accuracy_report.py scripts/oracle_evidence_validator.py
rg -n "accuracy|local_accuracy_report|skip_local_accuracy_report|profile ==|QUALITY_GATE_PROFILES" scripts/run_quality_gate.py tests README.md
rg -n "shadbala_components|sthana|dig|kala|chesta|naisargika|drik|total|rupa|missing_shadbala_component" scripts/oracle_evidence_validator.py tests references
rg -n "kuja|manglik|mangal|dosha|ashtakoot|kuta|varna|vashya|tara|yoni|graha_maitri|gana|bhakoot|nadi" scripts tests jyotish-app README.md
rg -n "panchanga|Panchanga|muhurta|Rahu Kala|Yamaganda|Gulika|Choghadiya|Hora|festival|vrata|ics|csv" scripts tests jyotish-app README.md
rg -n "ai_prompt_pack|oracle_progress|production_tuning_allowed|铁口|准确率|medical|financial|legal|免责声明|boundary" scripts jyotish-app tests README.md SKILL.md
find docs/research -maxdepth 1 -name 'antigravity_round25_*_2026_06_25.md' | sort | wc -l
find docs/research -maxdepth 1 -name 'antigravity_round26_*_2026_06_25.md' | sort | wc -l
git diff --check
npm run build --prefix jyotish-app
```

如果某条命令失败，记录完整失败摘要，不要用旧结论替代。

## 工作包 A：Round25/26 报告归档前总审计

输出：`docs/research/antigravity_round27_round25_26_archive_readiness_2026_06_25.md`

检查 38 份报告是否齐全、是否空文件、是否含敏感信息、是否存在过强结论、是否需要 Codex 提交前修正文档。

## 工作包 B：accuracy profile 稳定性复核

输出：`docs/research/antigravity_round27_accuracy_profile_stability_2026_06_25.md`

跑 `python3 scripts/run_quality_gate.py --profile accuracy`，记录是否通过、耗时、关键摘要、失败时最小复现。

## 工作包 C：Yoga 报告 diff 稳定性复核

输出：`docs/research/antigravity_round27_validation_logic_diff_stability_2026_06_25.md`

判断 `references/validation_logic_report.json` 的变化是排序稳定化还是准确率语义变化；给 Codex 是否应提交该 JSON 的建议。

## 工作包 D：Git 远端同步实操计划

输出：`docs/research/antigravity_round27_git_sync_ssh443_https_plan_2026_06_25.md`

复核 SSH-22 超时后，给出 SSH-443、HTTPS PAT、`git update-ref`、`ls-remote` 验证和不泄漏凭证的步骤。只写计划，不执行 push。

## 工作包 E：GitHub Actions accuracy workflow 审查

输出：`docs/research/antigravity_round27_accuracy_github_actions_review_2026_06_25.md`

给出 `.github/workflows/accuracy.yml` 的最小 YAML 草案、触发条件、缓存策略、避免 Playwright 重活的理由。

## 工作包 F：Shadbala validator Phase 2 蓝图

输出：`docs/research/antigravity_round27_shadbala_phase2_validator_blueprint_2026_06_25.md`

拆解 Rupas 单位、七曜六分量、每行总分、总和容差、非法 bool/string/负数、极大值、缺 total 的处理；输出测试名和 schema。

## 工作包 G：Kuja/Manglik enum validator 蓝图

输出：`docs/research/antigravity_round27_kuja_enum_validator_blueprint_2026_06_25.md`

定义 `none/low_dosha/medium_dosha/high_dosha/requires_review` 等候选 enum，审计当前 API 是否仍返回 bool，提出兼容策略和测试。

## 工作包 H：Prompt Pack 解盘安全护栏测试蓝图

输出：`docs/research/antigravity_round27_prompt_pack_guardrail_blueprint_2026_06_25.md`

把“不铁口直断、不夸大准确率、不做医疗法律金融承诺、必须引用 evidence/oracle_progress 边界”转成测试。

## 工作包 I：Panchanga 商业级 UI 最小实现规格

输出：`docs/research/antigravity_round27_panchanga_commercial_ui_spec_2026_06_25.md`

基于已有 API，设计前端日历表格、筛选器、festival/vrata candidate 标注、CSV/ICS 入口和移动端验收。

## 工作包 J：Muhurta range solver 外部 oracle SOP

输出：`docs/research/antigravity_round27_muhurta_external_oracle_sop_2026_06_25.md`

设计 AstroSage/Drik Panchang/Prokerala/JHora 对照截图采集表，不要求 Codex 编造外部真值。

## 工作包 K：Ashtakoot VedAstro/RaviKarrii 迁移许可证复核

输出：`docs/research/antigravity_round27_ashtakoot_license_and_table_reuse_2026_06_25.md`

联网确认 VedAstro、RaviKarrii、RoxyAPI、PyJHora、kunjara 的 license；列出可复制表格、不可复制代码和必须重写的部分。

## 工作包 L：Ashtakoot 5 个 oracle packet 手工表单

输出：`docs/research/antigravity_round27_ashtakoot_oracle_packet_forms_2026_06_25.md`

把 5 对合婚样本转成人工填写表，字段覆盖 8 Kuta 分项、总分、截图相对路径、来源、ayanamsa、工具版本。

## 工作包 M：API 未暴露技能 ROI 重排

输出：`docs/research/antigravity_round27_api_missing_skills_after_registry_2026_06_25.md`

必须先读取 registry/API route，再排除已经暴露的能力；输出 Top 50。

## 工作包 N：前端隐藏技能 ROI 重排

输出：`docs/research/antigravity_round27_frontend_hidden_skills_after_current_api_2026_06_25.md`

必须先跑/读前端 Skill Workbench；输出“后端已有但用户看不到”的 Top 50。

## 工作包 O：CLI 普通用户入口规格

输出：`docs/research/antigravity_round27_cli_table_mode_usability_spec_2026_06_25.md`

设计本地命令 `full-reading`、accuracy report、oracle queue、Muhurta/Panchanga 的表格输出体验。

## 工作包 P：Tajika endpoint gap 黑盒复核

输出：`docs/research/antigravity_round27_tajika_endpoint_gap_blackbox_2026_06_25.md`

确认 Tajika 是否只有内部模块/前端展示，是否缺 `/api/tajika`；给测试与实现边界。

## 工作包 Q：Chara Dasha 前端可见性复核

输出：`docs/research/antigravity_round27_chara_dasha_frontend_visibility_2026_06_25.md`

确认 Chara/Jaimini Dasha 是否在普通用户页面可见，提出最小 UI 票据。

## 工作包 R：D7/D60/深分盘前端复用规格

输出：`docs/research/antigravity_round27_deep_varga_frontend_reuse_spec_2026_06_25.md`

确认 D24/D30/D60 已有哪些后端能力，设计前端下拉、SVG renderer 复用和导出边界。

## 工作包 S：错误 JSON 包装审计

输出：`docs/research/antigravity_round27_error_json_wrapping_audit_2026_06_25.md`

扫描 API 是否仍返回裸异常/HTML，尤其登录、订阅、AI、导入、PDF、oracle evidence。

## 工作包 T：全机碎片后续读取顺序

输出：`docs/research/antigravity_round27_whole_machine_followup_read_order_2026_06_25.md`

基于 `whole_machine_fragment_sweep_round25`，列出下轮真正值得读的本地文件顺序；禁止摘录私人报告原文。

## 工作包 U：开源许可证隔离清单

输出：`docs/research/antigravity_round27_open_source_license_quarantine_2026_06_25.md`

至少 35 个项目/包，分类为 `copy_allowed`、`port_with_attribution`、`benchmark_only`、`do_not_use`。

## 工作包 V：用户准确率解释文案二稿

输出：`docs/research/antigravity_round27_user_accuracy_explainer_v2_2026_06_25.md`

面向普通用户说明“哪些技能本地可用、哪些准确率已可测、哪些需要外部 oracle”，不能用技术堆砌。

## 工作包 W：Codex Round 28 立即实现 Top 60

输出：`docs/research/antigravity_round27_codex_round28_top60_2026_06_25.md`

每项必须含文件、测试、验收、风险、是否需要人工；优先前 20 项必须能由 Codex 无需询问直接执行。

## 工作包 X：最终总报告与自检

输出：`docs/research/antigravity_round27_final_summary_and_self_audit_2026_06_25.md`

必须回答：

1. Round27 是否完成 24 份报告。
2. 本地准确率门禁是否可靠。
3. 还有多少“同品类重要技能”未产品化。
4. 哪些是 Codex 可立即做的。
5. 哪些必须等人工截图/外部工具。
6. 哪些旧结论已被纠正。
7. 下一轮副手应该继续做什么。
