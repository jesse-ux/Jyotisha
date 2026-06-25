# Antigravity AI 副手任务单 Round 24（2026-06-25）

## 任务目标

本轮最高优先级从“云端/文档/提交卫生”切换为：**本地电脑立即可用、对标应用技能完整、准确率可测、解盘可信**。请副手承担更大体量的并行研究、黑盒复核和任务拆解，尽量减少 Codex 主线算力消耗。

你需要像一个独立 QA + 产品研究 + Jyotish 校准团队一样工作：地毯式复核当前项目到底有哪些印度占星能力、哪些只是注册但未经过真实对标验收、哪些可以直接本地运行、哪些还缺 JHora/PyJHora/VedAstro/AstroSage 等外部 oracle 证据。

## 当前事实基线

必须先重新验证，不要直接相信旧报告：

- 当前分支：`codex/release-hygiene-ci`。
- `scripts/local_accuracy_report.py` 正在由 Codex 新增，用于聚合本地准确率/能力报告。
- 技能注册表当前应有约 68 项 technique，状态不应有 `missing` 或 `partial`，但“注册完整”不等于“对标应用全部验收完成”。
- 已知本地可测基线：
  - BPHS/Varga/Ashtakavarga invariants：18/18。
  - Public real-person gated chart checks：66/66。
  - Yoga logic report：precision 0.9648, recall 0.9399, F1 0.9522。
  - VedAstro 外部经度行最大偏差约 26.2254 arcsec，阈值 120 arcsec 内。
  - Dasha/Shadbala external oracle packets 仍未达到可生产调参。
  - `/api/synastry` 已切到完整 `ashtakoot.calculate_ashtakoot`，但仍需 UI/E2E/外部采样验收。
- Round 23 产物中可能缺 `antigravity_round23_shadbala_total_unit_acceptance_2026_06_25.md`，需要核对“副手声称创建”和“磁盘实际存在”是否一致。

## 工作量要求

本轮至少产出 **24 份 round24 报告**，全部写入 `docs/research/`，文件名必须含 `antigravity_round24_*_2026_06_25.md`。

每份报告必须包含：

- 至少 16 个检查点。
- 至少 5 条可复制命令、检索 token、URL、文件路径或代码位置。
- 至少 1 个“Codex 可直接实现”的任务建议。
- 至少 1 个“副手下一轮继续深挖”的任务建议。
- 状态必须标为：`已成立`、`部分成立`、`未成立`、`需要人工外部工具`、`需要用户决策`。
- 对外部项目必须记录 license；只有 MIT/Apache-2.0/BSD/ISC/CC0 可列为“可复制代码候选”，GPL/AGPL/LGPL/闭源只能做行为参考。
- 不允许把 `template_only`、`sample_only`、本仓库输出或空目标字段包装成 `external_verified`。

最终必须产出一份总报告，包含：

- Top 100 ROI 任务。
- “今天本地可做”任务。
- “必须人工 JHora/PyJHora/网页截图”任务。
- “必须联网/外部账号/API key”任务。
- “必须等用户决策”任务。
- “已完成但仍需证明准确率”的任务。
- “看似完成但其实只是表面 UI/注册表”的任务。

## 严格边界

禁止事项：

- 不要提交、推送、重置、删除、移动、覆盖或批量格式化现有文件。
- 不要修改 `scripts/`、`jyotish-app/`、`tests/`、`README.md`、`references/` 的实现内容。
- 不要读取或传播 token、API key、cookie、SSH 私钥、浏览器登录态、系统钥匙串。
- 不要摘录用户私人完整出生资料、PDF 原件或完整星盘报告正文。
- 不要复制 GPL/AGPL/LGPL/闭源项目代码、常量表或实现细节。
- 不要声称“全部技能已完成”除非有逐项本地入口、测试、外部证据和 UI/API 可用性证据。

允许事项：

- 只能新增 `docs/research/*round24*2026_06_25.md` 报告文件。
- 可以读取全部仓库文件做只读复核。
- 可以运行只读命令、pytest、npm build、quality gate。
- 可以联网检索公开开源项目、公开产品页面、公开文档，只记录 URL/license/能力差距。

## 必跑命令

```bash
git status --short --branch
git log --oneline --decorate -n 14
find docs/research -maxdepth 1 -name 'antigravity_round23_*_2026_06_25.md' -print | sort
find docs/research -maxdepth 1 -name 'antigravity_sidecar_work_order_round*_2026_06_25.md' -print | sort
python3 scripts/audit_capabilities.py --mode validate
python3 scripts/audit_capabilities.py --mode table
python3 scripts/validate_bphs_invariants.py
python3 tests/run_real_case_revalidation.py --summary
python3 scripts/oracle_boundary_audit.py --oracle-file references/oracle/dasha_shadbala_oracle_cases.json
python3 scripts/oracle_collection_queue.py --oracle-file references/oracle/dasha_shadbala_oracle_cases.json --format json > /tmp/jyotish_round24_queue.json
python3 scripts/oracle_evidence_validator.py --queue-file /tmp/jyotish_round24_queue.json
python3 scripts/local_accuracy_report.py --format json
python3 scripts/local_accuracy_report.py --format markdown
python3 -m pytest -q tests/test_local_accuracy_report.py tests/test_ashtakoot.py tests/test_api_server_security.py::test_synastry_api_uses_full_ashtakoot_engine
npm run build --prefix jyotish-app
git diff --check
```

## 工作包 A：本地准确率总控入口黑盒验收

输出：`docs/research/antigravity_round24_local_accuracy_report_blackbox_2026_06_25.md`

至少检查：

1. `scripts/local_accuracy_report.py --format json` 是否存在。
2. JSON 是否可被机器解析。
3. Markdown 是否可直接给用户阅读。
4. 是否包含 technique_count。
5. 是否包含 BPHS invariants。
6. 是否包含 real-person gated checks。
7. 是否包含 Yoga precision/recall/F1。
8. 是否包含 Dasha/Shadbala oracle readiness。
9. 是否包含 Ashtakoot API parity。
10. 是否明确“解盘预测准确率未外部认证”。
11. 是否区分本地回归和外部 oracle。
12. 是否可作为 README 用户入口。
13. 是否会超时。
14. 是否有隐私泄露。
15. 是否适合用户本机测试。
16. 缺口和 Round 25 建议。

## 工作包 B：全技能注册表 vs 对标应用能力矩阵

输出：`docs/research/antigravity_round24_skill_registry_vs_benchmark_apps_2026_06_25.md`

对比至少这些应用/库：

- JHora。
- PyJHora。
- AstroSage/Kundli。
- Prokerala/Kundli。
- VedAstro。
- Maitreya。
- Jagannatha Hora 文档/截图能力点。
- Swiss Ephemeris 相关开源生态。

至少输出 100 行矩阵：能力项、当前本地入口、测试证据、UI/API 是否暴露、外部对标状态、是否算“完成”。

## 工作包 C：看似完成但只是表面完成清单

输出：`docs/research/antigravity_round24_surface_completion_risk_audit_2026_06_25.md`

重点找：

1. 只在 registry 有但无 UI。
2. 只在 CLI 有但无用户入口。
3. 只有文档无测试。
4. 只有测试无外部 oracle。
5. 只有样例无真实值。
6. 只有本仓库 baseline。
7. 只有 Prompt Pack 文案。
8. 只有静态 demo。
9. 未接 API。
10. 未接导出。
11. 未接 Trust Center。
12. 未写 README。
13. 未做移动端。
14. 未做错误处理。
15. 未做隐私边界。
16. 未做精度验收。

## 工作包 D：Dasha 精准度外部校准作战包

输出：`docs/research/antigravity_round24_dasha_external_accuracy_battle_plan_2026_06_25.md`

要求：

- 给出至少 12 个 dasha 测试样本类型。
- 每个样本必须说明输入、外部工具、目标字段、容差、截图要求、晋级规则。
- 必须覆盖 Vimshottari 起算、Antardasha 边界、Moon longitude、ayanamsa/node mode、时区/DST、历史日期。

## 工作包 E：Shadbala 精准度外部校准作战包

输出：`docs/research/antigravity_round24_shadbala_external_accuracy_battle_plan_2026_06_25.md`

必须覆盖：

- 7 星。
- 六分量：sthana, dig, kala, chesta, naisargika, drik。
- total Rupas/Virupas。
- 单位换算。
- JHora/PyJHora/VedAstro 差异。
- 容差。
- 截图字段。
- JSON schema。
- 何时允许 production tuning。

## 工作包 F：解盘准确率评分标准

输出：`docs/research/antigravity_round24_interpretation_accuracy_rubric_2026_06_25.md`

设计一个能真正测试“解盘精准”的评分体系：

1. 计算事实正确性。
2. 规则引用正确性。
3. 强弱排序正确性。
4. 事件时间窗口正确性。
5. 反证和不确定性表达。
6. 不胡编。
7. 可追溯证据。
8. 与公开人生事实比对。
9. 用户主观反馈如何避免污染。
10. 隐私保护。
11. 分数权重。
12. 测试样本。
13. 自动化可测部分。
14. 人工评审部分。
15. CI gate。
16. Prompt Pack 接入。

## 工作包 G：本地用户路径端到端压力测试计划

输出：`docs/research/antigravity_round24_local_user_e2e_stress_plan_2026_06_25.md`

覆盖普通用户从本地启动到得到解盘：

- API 启动。
- 静态页面启动。
- 输入出生资料。
- 查看 D1/D9/D10。
- 查看 Dasha。
- 查看 Shadbala。
- 查看 Yoga。
- 合盘。
- 生成 AI prompt。
- 导出 JSON。
- 查看准确率报告。
- 遇到无外部 oracle 时的提示。
- 移动端。
- 断网。
- 错误输入。
- 隐私提示。

## 工作包 H：开源项目全网地毯式检索包

输出：`docs/research/antigravity_round24_open_source_jyotish_landscape_2026_06_25.md`

联网检索至少 40 个公开项目/页面，记录：

- URL。
- license。
- 语言。
- 能力点。
- 是否可复制。
- 可复用文件。
- 与本项目差距。
- 风险。

只允许 MIT/Apache-2.0/BSD/ISC/CC0 进入可复制候选。GPL/AGPL/LGPL/闭源只做行为参考。

## 工作包 I：PyJHora/JHora 对标差距专报

输出：`docs/research/antigravity_round24_pyjhora_jhora_gap_deep_audit_2026_06_25.md`

至少列出 80 个 JHora/PyJHora 能力点，标注：

- 本项目已有。
- 本项目缺失。
- 本项目部分有。
- 是否本地 UI 可见。
- 是否有测试。
- 是否有准确率证据。
- 实现优先级。

## 工作包 J：AstroSage/Prokerala/VedAstro 用户体验对标

输出：`docs/research/antigravity_round24_commercial_ux_gap_audit_2026_06_25.md`

重点不是抄 UI，而是找用户自然期待：

- 输入体验。
- 图表展示。
- 报告结构。
- 合盘流程。
- Dasha 展示。
- Panchang/Muhurta。
- 解读可信感。
- 错误提示。
- 导出分享。
- 移动端。
- 付费/高级功能启发。

## 工作包 K：前端是否承载全部技能审计

输出：`docs/research/antigravity_round24_frontend_full_skill_exposure_audit_2026_06_25.md`

对 `jyotish-app/main.js/style.css/index.html` 做只读审计，输出：

- 哪些技能有 UI。
- 哪些技能无 UI。
- 哪些技能只有 API/CLI。
- 哪些按钮只是 demo。
- 哪些结果没有来源/置信度。
- 哪些移动端拥挤。
- 哪些应该进入下一轮实现。

## 工作包 L：API 是否承载全部技能审计

输出：`docs/research/antigravity_round24_api_full_skill_exposure_audit_2026_06_25.md`

检查 `scripts/jyotish_api_server.py` 与引擎脚本：

- endpoint 列表。
- 每个 endpoint 覆盖能力。
- 未暴露能力。
- 输入校验。
- 输出 schema。
- 错误处理。
- 隐私风险。
- 测试覆盖。

## 工作包 M：CLI 是否承载全部技能审计

输出：`docs/research/antigravity_round24_cli_full_skill_exposure_audit_2026_06_25.md`

检查所有 `scripts/*.py` 用户可执行入口：

- 命令。
- 能力。
- 输出。
- 是否能普通用户理解。
- 是否有 README。
- 是否有测试。
- 是否能接到 Web。

## 工作包 N：Prompt Pack 解盘可信度审计

输出：`docs/research/antigravity_round24_prompt_pack_reading_trust_audit_2026_06_25.md`

检查 prompt 是否：

- 引用计算证据。
- 标注不确定性。
- 避免过度预测。
- 能解释 Dasha/Shadbala/Yoga。
- 能处理缺外部 oracle。
- 能输出可验证结论。
- 能做中文用户体验。

## 工作包 O：第一条真实 oracle 样本阻塞清单

输出：`docs/research/antigravity_round24_first_real_oracle_blocker_list_2026_06_25.md`

列出为什么现在仍是 0/5：

- 需要谁操作。
- 操作哪款工具。
- 保存哪个截图。
- 填哪些字段。
- 命令如何验收。
- 哪些隐私必须打码。
- 成功后哪几个文件会变。

## 工作包 P：Round 23 产物完整性审计

输出：`docs/research/antigravity_round24_round23_artifact_integrity_audit_2026_06_25.md`

必须核对：

- Round 23 声称创建多少文件。
- 磁盘实际存在多少文件。
- 是否缺 `shadbala_total_unit_acceptance`。
- 是否有空文件。
- 是否重复。
- 是否敏感。
- 是否可提交。
- 是否应要求副手补交。

## 工作包 Q：本地准确率报告 README 接入建议

输出：`docs/research/antigravity_round24_readme_accuracy_entry_plan_2026_06_25.md`

写出 README 应该如何告诉用户：

- 一条命令测试准确率。
- 哪些结果代表本地计算可信。
- 哪些不代表预测精准。
- 如何提交外部 oracle。
- 如何解读 0/5。
- 如何测试前端。

## 工作包 R：质量门禁补强建议

输出：`docs/research/antigravity_round24_quality_gate_accuracy_profile_plan_2026_06_25.md`

设计一个 `accuracy` profile：

- 包含哪些 pytest。
- 包含哪些脚本。
- 是否跑 local_accuracy_report。
- 是否阻塞 push。
- 运行时间预算。
- 失败信息如何展示。

## 工作包 S：数据隐私与出生资料安全审计

输出：`docs/research/antigravity_round24_birth_data_privacy_audit_2026_06_25.md`

只读检查：

- 是否存在私人出生资料。
- 是否有未打码截图。
- `.gitignore` 是否够。
- artifact README 是否够。
- 前端/导出是否提醒。
- 测试是否误收私人数据。

## 工作包 T：可复制开源代码候选清单

输出：`docs/research/antigravity_round24_copyable_code_candidate_inventory_2026_06_25.md`

只列 MIT/Apache-2.0/BSD/ISC/CC0：

- 项目 URL。
- license 证据。
- 可复制模块。
- 对应本项目缺口。
- 移植成本。
- 测试策略。
- 不可复制项说明。

## 工作包 U：下一批高优先级本地实现任务拆解

输出：`docs/research/antigravity_round24_codex_round25_implementation_backlog_2026_06_25.md`

拆成至少 60 个 Codex 可直接做的 issue，每个包含：

- 文件。
- 变更。
- 测试。
- 验收。
- 风险。
- 是否需要外部 oracle。

## 工作包 V：副手下一轮 Round 25 深挖任务

输出：`docs/research/antigravity_round24_sidecar_round25_recommendations_2026_06_25.md`

列出至少 40 个副手适合继续做的并行审计/研究任务。

## 工作包 W：最终总报告

输出：`docs/research/antigravity_round24_final_summary_2026_06_25.md`

必须回答：

1. 当前印度占星 app 是否已经包含对标应用全部技能。
2. 哪些技能“本地能用”。
3. 哪些技能“能算但未证明准”。
4. 哪些技能“UI 不可见”。
5. 哪些技能“API 不可见”。
6. 哪些技能“缺外部 oracle”。
7. 哪些技能“解盘可信度不足”。
8. 用户今天如何测试准确率。
9. 最高 ROI 的 100 个任务。
10. Round 25 第一优先级。

## 工作包 X：副手自检

输出：`docs/research/antigravity_round24_self_audit_2026_06_25.md`

副手必须自检：

- 是否跑了必跑命令。
- 是否漏文件。
- 是否误信旧结论。
- 是否把本地 baseline 当外部 oracle。
- 是否写够 24 份报告。
- 是否列够 Top 100 ROI。
- 是否有网络来源 license。
- 是否有敏感信息。
- 是否给 Codex 足够可执行任务。

## 交付格式

最后请在回复里列出：

- 创建的 24+ 文件。
- 最重要的 20 个发现。
- 当前“全部技能完成度”的真实判断。
- 当前“准确率可测程度”的真实判断。
- 必须由 Codex 下一步立刻做的 20 个任务。
- 必须由副手继续做的 20 个任务。
- 必须由人拿 JHora/PyJHora/网页完成的 10 个任务。
