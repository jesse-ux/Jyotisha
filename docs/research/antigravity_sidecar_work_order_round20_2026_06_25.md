# Antigravity AI 副手任务单 Round 20（2026-06-25）

## 任务目标

本轮继续把高体量、低耦合的审计和研究交给副手，重点是：纠正 Round 19 对 Ashtakoot 的过期判断、复核 Codex 已修的 runtime artifact / Shadbala 类型校验 / AI Prompt Pack oracle progress、设计 Ashtakoot 外部 oracle cases 与 E2E 测试、整理 Git 纳入策略，并继续推动 JHora/PyJHora 1/5 人工采集。

你只做只读复核、联网对标、报告和下一轮任务拆解；不要修改核心实现。

## 当前事实基线

必须以当前工作树重新验证，不要照抄旧报告：

- Ashtakoot 并非空白：当前已有 `scripts/ashtakoot.py`、`tests/test_ashtakoot.py`、`scripts/jyotish_engine.py ashtakoot` 子命令、`/api/synastry`、`jyotish-app` 合盘入口。
- `.gitignore` 当前已加入 `runtime-smoke-report-*.html` 和 `jyotish-app/runtime-smoke-report-*.html`。
- `scripts/oracle_evidence_validator.py` 当前已加入 `invalid_shadbala_component_type` 与 `invalid_shadbala_component_negative`。
- `ai_prompt_pack.evidence_snapshot.oracle_progress` 当前已在 CLI、API 和前端 fallback 路径补入。
- 第一条外部证据模板已存在：`references/oracle/evidence_packet_templates/jhora_steve_jobs_lahiri_first_packet.json`。
- 第一条真实 `external_verified` 仍必须等待人工 JHora/PyJHora 截图或 stdout，不能由本地引擎伪造。

## 工作量要求

本轮至少产出 12 份 `round20` 报告文件。每份报告必须包含：

- 至少 10 个检查点。
- 至少 2 条可复制命令、检索 token、URL 或代码位置。
- 至少 1 个 Codex 可直接改的文件建议。
- 状态必须标为 `已成立`、`部分成立`、`未成立`、`需要人工外部工具`。
- 发现旧结论过期时必须写“旧结论已过期”，并给出当前证据。
- 开源复用建议必须带 license；只允许 MIT/Apache-2.0/BSD/ISC/CC0 进入可复制候选，GPL/AGPL/LGPL/闭源只能做行为参考。

最终汇总必须给 Codex Top 25 ROI 任务列表，并拆成“Codex 可立即做”和“必须等人工外部工具”。

## 严格边界

禁止事项：

- 不要提交、推送、重置、删除、移动、批量格式化或覆盖现有文件。
- 不要读取、记录、传播 token、API key、cookie、SSH 私钥、浏览器登录态、系统钥匙串或远程凭证。
- 不要打开、摘录或传播用户私人完整星盘报告、PDF 原件、出生资料正文。
- 不要修改 `scripts/`、`jyotish-app/`、`tests/`、`README.md`、`references/oracle/` 的实现内容。
- 不要把本仓库输出、`template_only`、`local_baseline` 或空目标字段标成 `external_verified`。
- 不要复制 JHora、PyJHora、AGPL/GPL 项目的实现代码、公式常量或内部表格。
- 不要用“绝对可信”“世界第一”“完全校准”等话术。

允许事项：

- 只能新增 `docs/research/*round20*2026_06_25.md` 报告文件。
- 可以读取 README、SKILL、progress、task_plan、Round 18/19 报告和本任务单。
- 可以读取 `scripts/ashtakoot.py`、`scripts/synastry.py`、`scripts/jyotish_engine.py`、`scripts/jyotish_api_server.py`、`scripts/oracle_evidence_validator.py`、`tests/test_ashtakoot.py`、`tests/test_frontend_productization.py`、`tests/test_cli_smoke.py`、`tests/test_oracle_evidence_validator.py`、`jyotish-app/main.js`、`jyotish-app/skill-map.js`、`jyotish-app/index.html`、`references/oracle/**`。
- 可以运行只读命令：`git status`、`git log`、`rg`、`pytest`、`npm run build --prefix jyotish-app`、`python3 scripts/run_quality_gate.py --profile quick --skip-yoga-logic`。
- 可以联网检索公开开源项目、公开文档、公开产品页面；只记录 URL、license、能力点和差距，不抓取私人数据。

## 必跑命令

### 1. Git 与工作树

```bash
git status --short --branch
git log --oneline --decorate -n 10
```

### 2. Ashtakoot 当前事实复核

```bash
rg -n "Ashtakoot|ashtakoot|calculate_ashtakoot|calc_ashtakoot|/api/synastry|Synastry / Ashtakoot|36" \
  scripts tests jyotish-app README.md docs/research/antigravity_round19_*_2026_06_25.md
```

### 3. Round 19 修复复核

```bash
rg -n "runtime-smoke-report-\\*.html|invalid_shadbala_component_type|invalid_shadbala_component_negative|oracle_progress|artifact_policy: 'references/oracle/artifacts/'|external_oracle_evidence_validation" \
  .gitignore scripts tests jyotish-app
```

### 4. 目标测试

```bash
python3 -m pytest -q \
  tests/test_ashtakoot.py \
  tests/test_frontend_productization.py::test_runtime_smoke_html_artifacts_are_ignored \
  tests/test_frontend_productization.py::test_frontend_branded_avatar_and_prompt_pack_are_productized \
  tests/test_cli_smoke.py::test_full_reading_reports_ayanamsa_metadata_and_ai_prompt_pack \
  tests/test_oracle_evidence_validator.py
```

### 5. 质量门

```bash
npm run build --prefix jyotish-app
python3 scripts/run_quality_gate.py --profile quick --skip-yoga-logic
```

若失败，列出失败测试名、断言、真实风险等级和最小修复文件。

## 工作包 A：Round 19 Ashtakoot 旧结论纠偏

输出：`docs/research/antigravity_round20_ashtakoot_claim_recheck_2026_06_25.md`

至少检查：

1. `scripts/ashtakoot.py` 是否存在。
2. `tests/test_ashtakoot.py` 是否存在。
3. `jyotish_engine.py` 是否有 `ashtakoot` 子命令。
4. `jyotish_api_server.py` 是否通过 `/api/synastry` 暴露。
5. `jyotish-app/index.html` 是否有 Ashtakoot 按钮。
6. `jyotish-app/main.js` 是否有 Ashtakoot 渲染。
7. `jyotish-app/skill-map.js` 是否列出 Synastry / Ashtakoot。
8. Round 19 “完全缺失”结论是否过期。
9. 当前真实缺口是什么。
10. Codex 不应重复造什么。
11. 下一步该做 oracle cases 还是重写算法。
12. 是否需要用户体验/E2E 补强。

## 工作包 B：Ashtakoot 外部 oracle cases 设计

输出：`docs/research/antigravity_round20_ashtakoot_oracle_case_design_2026_06_25.md`

至少设计 5 个 draft cases，字段建议：

- `case_id`
- `privacy`
- male/female birth data 或 male/female Moon longitude
- ayanamsa
- node mode
- expected targets: total score, varna, vashya, tara, yoni, graha maitri, gana, bhakoot, nadi, kuja status
- preferred external sources
- artifact naming
- promotion criteria

必须标明哪些需要 JHora/AstroSage/VedAstro 等外部截图，哪些可用公开 MIT 项目交叉。

## 工作包 C：Ashtakoot UI/E2E 用户流程计划

输出：`docs/research/antigravity_round20_ashtakoot_ui_e2e_plan_2026_06_25.md`

至少设计 15 条用户流程，覆盖：

1. 输入双方完整出生资料。
2. 只输入月亮黄经快算。
3. 无 API fallback。
4. API 可用深度合盘。
5. 移动端按钮不溢出。
6. 36 分总分可见。
7. 8 Kuta 分项可见。
8. Kuja Dosha 可见。
9. D9 婚姻专题可见。
10. Dasha 同步边界可见。
11. 保存关系案例。
12. 导出报告。
13. AI Prompt Pack 引用关系证据。
14. 错误出生时间提示。
15. 外部 oracle 进度提示。

## 工作包 D：Round 19 修复黑盒复核

输出：`docs/research/antigravity_round20_round19_fix_blackbox_2026_06_25.md`

至少检查：

1. `.gitignore` runtime smoke HTML。
2. Shadbala 字符串数字拒绝。
3. Shadbala 负数拒绝。
4. bool 是否拒绝。
5. `oracle_progress` CLI。
6. `oracle_progress` API。
7. `oracle_progress` 前端 fallback。
8. Prompt Pack retrieval tag 是否有 `external_oracle_evidence_validation`。
9. quick gate 是否通过。
10. 是否还有 stale Round 19 bug。

## 工作包 E：JHora 1/5 人工采集监督清单

输出：`docs/research/antigravity_round20_jhora_1_of_5_supervision_checklist_2026_06_25.md`

继续把真实人工工作拆细：

1. 外部工具环境。
2. Steve Jobs 输入字段。
3. Lahiri/true node 设置。
4. Vimshottari 截图。
5. Shadbala 七曜六分量截图。
6. artifact 命名。
7. 打码检查。
8. JSON 填写检查。
9. validator 运行检查。
10. 1/5 成功判据。
11. 仍不能生产调参的边界。
12. 失败退回清单。

## 工作包 F：Git 纳入与提交策略复核

输出：`docs/research/antigravity_round20_git_stage_commit_strategy_2026_06_25.md`

至少输出：

1. 当前 modified 文件列表。
2. 当前 untracked 文件列表。
3. 哪些是产品代码必须纳入。
4. 哪些是副手报告应纳入。
5. 哪些是 artifacts policy/template 应纳入。
6. 哪些不应纳入。
7. 是否有 runtime HTML 被忽略。
8. 是否有私人文件。
9. 建议 stage 清单。
10. 建议 commit message。
11. 是否需要 push。
12. 风险提示。

## 工作包 G：开源 Ashtakoot 可复用矩阵

输出：`docs/research/antigravity_round20_ashtakoot_open_source_matrix_2026_06_25.md`

联网检索至少 15 个 Ashtakoot/compatibility/matchmaking 项目，记录：

- URL
- license
- language
- last activity
- reusable directly?
- scoring factors
- constants/tables availability
- risks
- Codex action

必须单独列出 MIT/Apache/BSD 可用候选和 GPL/AGPL/闭源参考候选。

## 工作包 H：Shadbala 单位/总分下一轮设计

输出：`docs/research/antigravity_round20_shadbala_units_totals_design_2026_06_25.md`

在类型/非负校验之后，设计下一层：

1. Rupa/Virupa 单位字段。
2. 是否允许百分比。
3. component sum 与 total 校验。
4. 浮点容差。
5. JHora 截图如何读单位。
6. PyJHora stdout 如何标注单位。
7. validator schema 变更。
8. API/UI 错误展示。
9. tests。
10. 是否进入 Round 21。

## 工作包 I：AI Prompt Pack oracle progress 用户价值复核

输出：`docs/research/antigravity_round20_ai_prompt_oracle_progress_review_2026_06_25.md`

至少检查：

1. CLI JSON。
2. API JSON。
3. 前端 fallback。
4. AI Chat buildReadingPrompt。
5. evidence copy。
6. retrieval tags。
7. 是否避免误称校准。
8. 是否增加 token 成本。
9. 是否适合展示给用户。
10. 下一步是否加 Ashtakoot oracle progress。

## 工作包 J：全项目遗漏风险回归

输出：`docs/research/antigravity_round20_project_omission_regression_2026_06_25.md`

复核当前是否还有被反复遗忘的资料：

1. Round 16-20 work orders。
2. Round 16-19 reports。
3. `docs/user_jhora_capture_guide.md`。
4. `references/oracle/artifacts/README.md`。
5. `references/oracle/evidence_packet_templates/`。
6. Ashtakoot 报告与实际代码冲突。
7. `.gitignore`。
8. `task_plan.md`。
9. `progress.md`。
10. 必须纳入 Git 的最小集合。

## 工作包 K：Round 21 副手建议

输出：`docs/research/antigravity_round20_round21_sidecar_recommendations_2026_06_25.md`

给出下一轮至少 10 个副手工作包，继续承担高体量研究与复核。

## 工作包 L：Codex Round 21 执行计划

输出：`docs/research/antigravity_round20_codex_round21_execution_plan_2026_06_25.md`

输出：

1. 当前已成立能力。
2. 当前未成立能力。
3. 已过期旧结论。
4. 必须先修 P0/P1。
5. 可直接改的文件。
6. 可直接新增测试。
7. 必须等人工工具。
8. 可复用开源候选。
9. 只能参考候选。
10. Top 25 ROI 任务。

## 最终汇总格式

完成后输出：

1. 已创建文件列表。
2. 每个工作包一句话结论。
3. 过期旧结论纠偏表。
4. 当前 P0/P1/P2 bug 表。
5. 可直接复用开源项目 Top 5。
6. 只能参考不能复制项目 Top 5。
7. 必须等待人工外部工具事项。
8. 给 Codex 的 Top 25 下一步。

结尾必须写：

> 下一步建议 Codex 优先……
