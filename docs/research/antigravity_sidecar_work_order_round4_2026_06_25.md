# Antigravity AI 副手任务单 Round 4（2026-06-25）

## 角色边界

Antigravity AI 继续作为外部审计与 oracle 采集副手。本轮只做外部资料复核、黑盒结果采集建议、报告产出和当前 oracle 模板链路复验，不直接修改核心计算、前端主逻辑、Skill 文件或测试文件。

禁止事项：

- 不要提交、重置、删除、批量格式化或覆盖现有文件。
- 不要读取、记录、传播任何 token、API key、浏览器登录态、系统钥匙串或远端凭证。
- 不要把本地引擎输出伪装成 JHora、PyJHora、VedAstro、AstroSage、Prokerala 或商业软件结果。
- 不要修改 `scripts/`、`jyotish-app/`、`skills/`、`SKILL.md`、`tests/` 下的实现文件。
- 不要为单个 PDF 或单个 API 样本建议调生产常数、Shadbala 系数、Dasha 年长常数。
- 不要复制 AGPL/GPL 项目的实现代码、公式常量或内部数据表。

允许事项：

- 可以读取 `references/oracle/dasha_shadbala_oracle_cases.json`、`scripts/oracle_boundary_audit.py`、`tests/test_oracle_boundary_audit.py`、Round 3 报告和 README。
- 可以运行只读验证命令：
  - `python3 scripts/oracle_boundary_audit.py --oracle-file references/oracle/dasha_shadbala_oracle_cases.json`
  - `python3 -B -m pytest tests/test_oracle_boundary_audit.py -q`
  - `python3 scripts/audit_fragments.py --strict`
- 可以创建 `docs/research/*round4*2026_06_25.md` 报告。
- 可以在 `/tmp` 建临时实验环境试调用外部包或 HTTP API，但不得把其代码复制进本仓库。

## 当前背景

Codex 已把 Round 3 副手提出的 oracle 模板从报告草稿纳入正式审计资产：

- `references/oracle/dasha_shadbala_oracle_cases.json` 已新增 `template_cases`，目前 5 条，全部为 `template_only`。
- `scripts/oracle_boundary_audit.py` 已输出：
  - `summary.template_cases = 5`
  - `summary.template_status_counts = {"template_only": 5}`
  - `template_cases[].missing_target_fields`
  - `template_cases[].ready_for_calibration = false`
- `tests/test_oracle_boundary_audit.py` 已守住这些状态。
- 当前报告仍保持 `production_tuning_recommended = false`，不得改成 true。

本轮副手目标：不要继续泛泛说“缺 oracle”，而是回答“哪些模板能被哪些外部来源填充、每个字段如何采集、哪些仍然不能升级”。

## 对标任务 A：外部 oracle 来源可信度分层

目标：建立外部来源分层，不写代码。

必须复核这些来源：

- **JHora / Jagannatha Hora**：作为人工截图/手工录入真值的高优先级来源，重点 Dasha start boundary、Shadbala 六分量、D1/D9、Ayanamsa 设置。
- **PyJHora**：作为黑盒运行参考。注意许可证为 AGPL-3.0，不能复制实现；只允许采集输出值并写来源说明。
- **VedAstro / VedAstro.Python / VedAstro HTTP API**：作为 MIT 开源 API/SDK 参考，适合黄经、部分基础排盘、可用方法清单；Dasha/Shadbala 是否可靠需实际验证。
- **Swiss Ephemeris 文档**：作为 ayanamsa/sidereal mode 使用规范参考，不是 Dasha/Shadbala 真值来源。
- **AstroSage / Prokerala**：可作为 C 端展示对标，不作为 Shadbala/Dasha 绝对真值首选来源。

输出文件：

- `docs/research/antigravity_round4_oracle_source_ranking_2026_06_25.md`

必须包含表格：

| 来源 | 许可证/使用边界 | 可采集字段 | 不适合作为真值的字段 | 推荐状态 |
|---|---|---|---|---|

推荐状态只能使用：

- `preferred_external_oracle`
- `secondary_external_check`
- `display_reference_only`
- `not_suitable`

## 开源参考任务 B：5 个 template_cases 逐项填充路线

目标：把当前 5 个 `template_only` 的样本逐项变成采集路线图。

读取：

- `references/oracle/dasha_shadbala_oracle_cases.json`
- `scripts/oracle_boundary_audit.py`
- `docs/research/antigravity_round3_oracle_feasibility_2026_06_25.md`

输出文件：

- `docs/research/antigravity_round4_template_case_fill_plan_2026_06_25.md`

每个模板必须给出：

| case_id | 当前 status | 缺失字段 | 首选外部来源 | 采集步骤 | 升级为 external_verified 的判据 | 风险 |
|---|---|---|---|---|---|---|

要求：

- 不允许把 `template_only` 写成已完成。
- 如果无法采集某字段，明确写 `blocked_by_external_tool_access` 或 `blocked_by_api_limit`。
- 如果字段来自本仓库输出，只能标 `local_baseline`，不能标 `external_verified`。

## Bug 任务 C：Oracle 审计脚本黑盒复验

目标：验证 Codex 新增的 template case 守门是否真实有效。

步骤：

1. 运行：
   `python3 scripts/oracle_boundary_audit.py --oracle-file references/oracle/dasha_shadbala_oracle_cases.json`
2. 检查输出必须包含：
   - `summary.template_cases: 5`
   - `summary.template_status_counts.template_only: 5`
   - `summary.production_tuning_recommended: false`
   - `template_cases[0].missing_target_fields`
   - `template_cases[0].ready_for_calibration: false`
3. 运行：
   `python3 -B -m pytest tests/test_oracle_boundary_audit.py -q`
4. 记录是否通过。

输出文件：

- `docs/research/antigravity_round4_oracle_audit_blackbox_2026_06_25.md`

Bug 表格式：

| 严重程度 | 文件路径 | 行号 | 现象 | 复现步骤 | 修复建议 |
|---|---|---:|---|---|---|

严重度：

- P0：审计脚本会把 template/local/sample 数据误判为可调参。
- P1：审计脚本不输出缺失字段或无法追踪模板状态。
- P2：报告字段命名/文案不清晰。

## 普通用户/产品任务 D：准确率页面下一步建议

目标：从普通用户角度解释“准确率如何继续变准”，但不能夸大。

输出文件：

- `docs/research/antigravity_round4_accuracy_transparency_next_steps_2026_06_25.md`

必须分四类写：

| 模块 | 当前状态 | 可对用户说的话 | 不能对用户说的话 | 下一步数据 |
|---|---|---|---|---|

模块：

- 基础黄经 / D1 / D9
- Vimshottari Dasha
- Shadbala
- AI 解读

要求：

- 必须强调：AI 解读可信度来自 `ai_prompt_pack/evidence_snapshot`，但不等同于人生事件预测准确率。
- 必须强调：Shadbala 需要外部六分量组件目标，不允许全局 scaling。
- 必须强调：Dasha 起点需要 Moon longitude、ayanamsa、node mode、year length/start-boundary 共同对齐。

## 最终回复格式

完成后在 Antigravity 聊天里回复：

1. 已创建哪些 `docs/research/*round4*2026_06_25.md` 文件。
2. 当前 5 个 template case 的状态是否仍全部为 `template_only`。
3. 有无任何可以安全升级为 `external_verified` 的字段；如果没有，明确说没有。
4. P0/P1/P2 Bug 总表。
5. 下一步建议给 Codex 的可执行修复事项。

最终报告必须使用中文，章节固定为：

- 对标
- 开源参考
- Bug
