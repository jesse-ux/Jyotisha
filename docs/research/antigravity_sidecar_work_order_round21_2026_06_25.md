# Antigravity AI 副手任务单 Round 21（2026-06-25）

## 任务目标

本轮继续把高体量、低耦合、可并行的研究和黑盒复核交给副手，重点从“Dasha/Shadbala 证据基础设施”扩展到“Ashtakoot 外部 oracle、同品类开源复用、真实用户流程、Git 入库风险、下一轮实现优先级”。你要用当前工作树重新验证，不要继承 Round 19/20 的旧结论。

你只做只读复核、联网对标、报告、任务拆解和下一轮建议；不要改核心实现。

## 当前事实基线

必须先验证这些事实，发现不符就以当前代码为准：

- Round 21 开始前，`references/oracle/ashtakoot_oracle_cases.json` 已存在，包含 5 条 Ashtakoot 外部合婚 oracle draft cases。
- `scripts/oracle_collection_queue.py` 已有 Ashtakoot 字段到 `target_modules: ["ashtakoot"]` 的映射。
- `README.md` 已出现 `Ashtakoot 外部合婚 oracle`、`references/oracle/ashtakoot_oracle_cases.json`、`ashtakoot_36_point` 和 10 个目标字段说明。
- `scripts/ashtakoot.py`、`tests/test_ashtakoot.py`、`/api/synastry`、`jyotish-app` 合盘入口已存在；“Ashtakoot 完全缺失”是过期结论。
- Dasha/Shadbala 真实 `external_verified` 仍然是 0/5，不能用本地引擎、自填空值或模板文件伪造。
- 第一条真实 JHora/PyJHora 证据仍必须等待人工外部工具截图或 stdout。
- 当前存在大量 untracked `docs/research/antigravity_round16` 到 `round20` 报告，Git 纳入策略仍是 P0 级项目治理问题。

## 联网检索基线

本轮需要继续联网复核，不允许只看旧报告。起始候选如下：

- VedAstro/VedAstro：GitHub 显示 MIT，公开介绍含 Match Checker / marriage compatibility，优先调查其 Ashtakoot 常量与 API 输出结构。
- RaviKarrii/Marriage-Compatibility-Asthakoot：GitHub 搜索结果显示 MIT，Java Ashtakoot REST API，优先调查是否有可复用 8 Kuta 打分表。
- alireza-da/pyhora2：GitHub 搜索结果显示 MIT，声称包含 horoscope and matching，优先调查是否真有 Ashtakoot 可复用代码。
- naturalstupid/PyJHora：AGPL-3.0，只允许黑盒运行/输出对照，不允许复制代码、常量表或内部公式。
- Hora Prakash / Ascendant / jyothisha-service / PyJHora MCP 等 AGPL/GPL/闭源或 license 不明项目只能作为行为参考。

联网时至少再找 20 个同品类项目或公开产品页面，记录 URL、license、可复制性、能力点、最后活动时间和风险。

## 工作量要求

本轮至少产出 18 份 `round21` 报告文件。每份报告必须包含：

- 至少 12 个检查点。
- 至少 3 条可复制命令、检索 token、URL 或代码位置。
- 至少 1 个 Codex 可直接改的文件建议。
- 状态必须标为 `已成立`、`部分成立`、`未成立`、`需要人工外部工具`。
- 发现旧结论过期时必须写“旧结论已过期”，并给出当前证据。
- 开源复用建议必须带 license；只有 MIT/Apache-2.0/BSD/ISC/CC0 进入“可复制候选”，GPL/AGPL/LGPL/闭源只能做行为参考。
- 最终总报告必须输出 Top 40 ROI 任务，并拆成：
  - Codex 可立即做
  - 副手继续可做
  - 必须等人工外部工具
  - 必须等用户决策/凭证

## 严格边界

禁止事项：

- 不要提交、推送、重置、删除、移动、批量格式化或覆盖现有文件。
- 不要读取、记录、传播 token、API key、cookie、SSH 私钥、浏览器登录态、系统钥匙串或远程凭证。
- 不要打开、摘录或传播用户私人完整星盘报告、PDF 原件、出生资料正文。
- 不要修改 `scripts/`、`jyotish-app/`、`tests/`、`README.md`、`references/oracle/` 的实现内容。
- 不要把本仓库输出、`template_only`、`local_baseline` 或空目标字段标成 `external_verified`。
- 不要复制 JHora、PyJHora、AGPL/GPL/LGPL/闭源项目的实现代码、公式常量或内部表格。
- 不要用“绝对可信”“世界第一”“完全校准”等话术。

允许事项：

- 只能新增 `docs/research/*round21*2026_06_25.md` 报告文件。
- 可以读取 README、SKILL、progress、task_plan、Round 16-20 报告和本任务单。
- 可以读取 `scripts/ashtakoot.py`、`scripts/synastry.py`、`scripts/jyotish_engine.py`、`scripts/jyotish_api_server.py`、`scripts/oracle_collection_queue.py`、`scripts/oracle_evidence_validator.py`、`tests/**`、`jyotish-app/**`、`references/oracle/**`。
- 可以运行只读命令：`git status`、`git log`、`rg`、`pytest`、`npm run build --prefix jyotish-app`、`python3 scripts/run_quality_gate.py --profile quick --skip-yoga-logic`。
- 可以联网检索公开开源项目、公开文档、公开产品页面；只记录 URL、license、能力点和差距，不抓取私人数据。

## 必跑命令

### 1. Git 与任务资产

```bash
git status --short --branch
git log --oneline --decorate -n 10
rg -n "antigravity_sidecar_work_order_round2|round21|Ashtakoot 外部合婚 oracle|external_verified|ready_for_calibration" docs README.md progress.md task_plan.md references/oracle
```

### 2. Ashtakoot queue 事实复核

```bash
python3 scripts/oracle_collection_queue.py \
  --oracle-file references/oracle/ashtakoot_oracle_cases.json \
  --format json > /tmp/jyotish_ashtakoot_queue_round21.json

python3 - <<'PY'
import json
data=json.load(open('/tmp/jyotish_ashtakoot_queue_round21.json'))
print(data['summary'])
print(data['tasks'][0]['case_id'])
print(data['tasks'][0]['target_modules'])
print(data['tasks'][0]['target_fields'])
PY
```

### 3. Dasha/Shadbala queue 事实复核

```bash
python3 scripts/oracle_collection_queue.py \
  --oracle-file references/oracle/dasha_shadbala_oracle_cases.json \
  --format json > /tmp/jyotish_dasha_shadbala_queue_round21.json

python3 scripts/oracle_evidence_validator.py \
  --queue-file /tmp/jyotish_dasha_shadbala_queue_round21.json
```

### 4. 当前产品与测试覆盖

```bash
python3 -m pytest -q \
  tests/test_oracle_collection_queue.py \
  tests/test_oracle_evidence_validator.py \
  tests/test_ashtakoot.py \
  tests/test_frontend_productization.py::test_dasha_reference_audit_is_documented_and_gated \
  tests/test_frontend_productization.py::test_trust_center_exposes_oracle_evidence_intake_cards \
  tests/test_cli_smoke.py::test_full_reading_reports_ayanamsa_metadata_and_ai_prompt_pack
```

### 5. 构建与快速质量门

```bash
npm run build --prefix jyotish-app
python3 scripts/run_quality_gate.py --profile quick --skip-yoga-logic
git diff --check
```

若失败，报告失败测试名、断言、最小复现、真实风险等级和最小修复文件。

## 工作包 A：Round 21 当前事实总复核

输出：`docs/research/antigravity_round21_current_fact_baseline_2026_06_25.md`

至少检查：

1. 当前分支和 ahead/behind 状态。
2. modified tracked 文件。
3. untracked 报告文件数量。
4. `references/oracle/ashtakoot_oracle_cases.json` 是否存在。
5. Ashtakoot queue 是否输出 5 条任务。
6. Dasha/Shadbala queue 是否仍为 5 条任务。
7. `valid_packets` 是否仍为 0。
8. `ready_for_calibration` 是否仍为 0。
9. Trust Center 是否显示 0/5。
10. AI Prompt Pack 是否包含 `oracle_progress`。
11. README 是否同步最新采集命令。
12. 哪些 Round 20 结论已过期。

## 工作包 B：Ashtakoot oracle cases 黑盒复核

输出：`docs/research/antigravity_round21_ashtakoot_oracle_queue_blackbox_2026_06_25.md`

至少检查：

1. 5 个 `case_id` 是否唯一。
2. 每个 case 是否有隐私等级。
3. 是否全部 `template_only` 或非生产状态。
4. target 字段是否覆盖 8 Kuta。
5. 是否包含 `total_score`。
6. 是否包含 `kuja_status`。
7. 是否标明 `ashtakoot_36_point`。
8. 是否有 artifact 命名要求。
9. 是否能被 collection queue 识别为 `ashtakoot`。
10. 是否误触发生产校准。
11. 是否可能泄漏私人关系资料。
12. 是否需要独立 validator 范围检查。

## 工作包 C：Ashtakoot validator 下一层设计

输出：`docs/research/antigravity_round21_ashtakoot_validator_range_design_2026_06_25.md`

设计 Codex 可直接实现的校验规则：

1. `total_score` 必须是数值。
2. `0 <= total_score <= 36`。
3. `varna` 范围 0-1。
4. `vashya` 范围 0-2。
5. `tara` 范围 0-3。
6. `yoni` 范围 0-4。
7. `graha_maitri` 范围 0-5。
8. `gana` 范围 0-6。
9. `bhakoot` 范围 0-7。
10. `nadi` 范围 0-8。
11. 8 Kuta 分项求和应近似等于 `total_score`，容差建议 0.01。
12. `kuja_status` 是否应该枚举化。
13. 错误码命名建议，例如 `invalid_ashtakoot_score_range:target.nadi`。
14. 对 `bool`、字符串、空值、负数、超大值的拒绝策略。
15. 测试文件建议。

## 工作包 D：开源 Ashtakoot 直接复用矩阵

输出：`docs/research/antigravity_round21_ashtakoot_open_source_reuse_matrix_2026_06_25.md`

联网检索至少 20 个项目或页面，至少包含：

1. VedAstro/VedAstro。
2. VedAstro Python 或相关 wrapper。
3. RaviKarrii/Marriage-Compatibility-Asthakoot。
4. alireza-da/pyhora2。
5. RoxyAPI jyotish starter。
6. PyJHora。
7. Hora Prakash。
8. AstroSage。
9. Maitreya。
10. Prokerala API。

每项必须记录：

- URL
- license
- language
- latest activity or date
- can copy code/constants?
- can black-box compare?
- Ashtakoot coverage
- Dasha/Shadbala coverage
- API/UI ideas
- Codex action

## 工作包 E：VedAstro 深挖但不盲抄

输出：`docs/research/antigravity_round21_vedastro_reuse_deep_dive_2026_06_25.md`

至少检查：

1. 仓库 license 文件。
2. 是否 MIT 覆盖目标代码路径。
3. Match Checker / marriage compatibility 入口。
4. 8 Kuta 或 10 Kuta 方法。
5. 是否有常量表。
6. 是否依赖 Swiss Ephemeris/JPL。
7. C# 到 Python 移植成本。
8. attribution 需求。
9. 可复制的最小文件或函数。
10. 不应复制的附带依赖。
11. 与本仓库现有 `scripts/ashtakoot.py` 的差异。
12. 推荐是否进入 Codex Round 22 实现。

## 工作包 F：RaviKarrii MIT Java Ashtakoot 深挖

输出：`docs/research/antigravity_round21_ravikarrii_ashtakoot_deep_dive_2026_06_25.md`

至少检查：

1. license 是否 MIT。
2. 是否含完整 REST API。
3. 是否含 Kuta 打分常量。
4. 是否含 Nakshatra/Rashi 映射。
5. 输入模型。
6. 输出模型。
7. Java 到 Python 移植成本。
8. 是否有测试样本。
9. 与现有算法差距。
10. 可复制文件列表。
11. attribution 方式。
12. 是否优先于 VedAstro。

## 工作包 G：pyhora2 MIT 深挖

输出：`docs/research/antigravity_round21_pyhora2_reuse_review_2026_06_25.md`

至少检查：

1. license 是否真为 MIT。
2. 是否是 PyJHora 派生或独立重写。
3. 是否含 matching/ashtakoot。
4. 是否可能混入 AGPL 来源。
5. 是否能复制。
6. 是否只能行为参考。
7. 代码质量。
8. 测试质量。
9. 最近 release。
10. 与本仓库依赖冲突。
11. Codex 是否应引入为依赖。
12. 最终风险等级。

## 工作包 H：JHora/PyJHora 1/5 人工采集执行监督

输出：`docs/research/antigravity_round21_jhora_1_of_5_execution_supervision_2026_06_25.md`

继续拆细真实人工采集：

1. 电脑/系统要求。
2. JHora 设置截图。
3. Steve Jobs 输入字段。
4. Lahiri 设置。
5. true node 设置。
6. Vimshottari start date 截图。
7. Shadbala 七曜六分量截图。
8. 文件命名。
9. 打码验收。
10. JSON 填写。
11. validator 命令。
12. `valid_packets: 1` 判据。
13. `ready_for_calibration: 1` 判据。
14. 为什么仍不能生产调参。
15. 失败重采清单。

## 工作包 I：Trust Center 用户体验压力测试计划

输出：`docs/research/antigravity_round21_trust_center_ux_stress_plan_2026_06_25.md`

至少覆盖：

1. 用户能否理解 0/5。
2. 用户能否下载模板。
3. 用户能否知道必须打码。
4. 用户能否找到 JHora 指南。
5. 用户是否误以为已经校准。
6. 移动端密集信息是否溢出。
7. 失败上传如何解释。
8. Ashtakoot oracle 与 Dasha/Shadbala oracle 是否混淆。
9. AI Prompt Pack 是否如实提示证据阶段。
10. 无 API 时静态 demo 边界是否明显。
11. 是否需要贡献者 checklist。
12. Playwright/E2E 建议。

## 工作包 J：AI Prompt Pack 扩展到 Ashtakoot oracle 设计

输出：`docs/research/antigravity_round21_ai_prompt_ashtakoot_oracle_design_2026_06_25.md`

至少设计：

1. 是否新增 `ashtakoot_oracle_progress`。
2. 是否合并进现有 `oracle_progress`。
3. 是否需要 `scope` 数组。
4. Prompt 文案如何避免误称校准。
5. CLI 输出结构。
6. API 输出结构。
7. 前端 fallback 输出结构。
8. retrieval tag。
9. token 成本。
10. 测试改动。
11. UI 展示方式。
12. Codex 最小实现路径。

## 工作包 K：Ashtakoot UI/E2E 深度测试设计

输出：`docs/research/antigravity_round21_ashtakoot_ui_e2e_deep_plan_2026_06_25.md`

至少 20 条流程：

1. 完整出生资料合盘。
2. 只输入月亮黄经。
3. API 不可用 fallback。
4. API 可用 `/api/synastry`。
5. 36 分总分显示。
6. 8 Kuta 分项显示。
7. Kuja Dosha 显示。
8. D9 婚姻专题显示。
9. Dasha 同步说明。
10. 保存关系样本。
11. 导出合盘报告。
12. AI Prompt Pack 引用合盘证据。
13. 移动端按钮不溢出。
14. 空输入错误。
15. 非法经度错误。
16. 时区错误。
17. 边界经度 0/360。
18. 同一人资料防呆。
19. 隐私提示。
20. 外部 oracle 进度提示。

## 工作包 L：Shadbala 单位/总分强校验二期

输出：`docs/research/antigravity_round21_shadbala_units_totals_phase2_2026_06_25.md`

至少设计：

1. Rupa vs Virupa 表示。
2. 是否必须保存 `unit`。
3. component sum 与 total 的关系。
4. 七曜 total 必填。
5. 每一分量合理上限。
6. `component_sum_mismatch` 错误码。
7. 截图读数不清如何标记。
8. 小数容差。
9. Validator 测试。
10. API 上传错误。
11. UI 展示。
12. 是否阻塞 1/5 晋级。

## 工作包 M：仓库隐私与污染审计二期

输出：`docs/research/antigravity_round21_privacy_repo_hygiene_phase2_2026_06_25.md`

至少检查：

1. `.gitignore` 是否屏蔽 runtime HTML。
2. `output_report.txt` 是否屏蔽。
3. `results_extracted.md` 是否屏蔽。
4. `references/oracle/artifacts/` 是否只包含 `.gitkeep` 和 README。
5. 是否有私人截图。
6. 是否有私人 PDF。
7. 是否有 token。
8. 是否有 API key。
9. 是否有 cookie。
10. 是否有完整出生资料报告。
11. 应纳入 Git 的文件。
12. 不应纳入 Git 的文件。

## 工作包 N：Git stage/commit 最小风险策略

输出：`docs/research/antigravity_round21_git_stage_commit_strategy_2026_06_25.md`

至少输出：

1. 建议分几次 commit。
2. 第一 commit 应包含哪些产品代码。
3. 第二 commit 应包含哪些 oracle/doc 报告。
4. 是否把 `docs/research/antigravity_round16-21` 一次纳入。
5. 是否排除任何文件。
6. `git add` 精确命令。
7. `git diff --cached --stat` 检查。
8. commit message。
9. push 前检查。
10. GitHub 443 SSH 超时 fallback。
11. 是否需要 `update-ref`。
12. 回滚风险提示。

## 工作包 O：同品类缺口重新排名

输出：`docs/research/antigravity_round21_competitor_gap_rerank_2026_06_25.md`

从真实同品类产品/库重新排名至少 30 项功能缺口，覆盖：

1. Dasha。
2. Shadbala。
3. Ashtakoot。
4. Manglik/Kuja。
5. Panchang。
6. Muhurta。
7. Transit。
8. KP。
9. Jaimini。
10. Ashtakavarga。
11. Yoga。
12. Varga D1-D60。
13. PDF 报告。
14. AI 问答。
15. 隐私/本地化。
16. 开源证据。
17. API。
18. 移动端。
19. 多语言。
20. 贡献者采集流程。

## 工作包 P：下一轮 Codex 实现计划

输出：`docs/research/antigravity_round21_codex_round22_execution_plan_2026_06_25.md`

必须把所有发现转成 Codex 可执行计划：

1. Top 10 P0/P1。
2. 每项影响面。
3. 具体文件。
4. 具体测试。
5. 是否需要联网。
6. 是否需要人工外部工具。
7. 是否需要用户确认。
8. 最小实现路径。
9. 不做事项。
10. 验收命令。
11. 建议 commit 拆分。
12. 副手下一轮继续任务。

## 工作包 Q：遗漏回归测试清单

输出：`docs/research/antigravity_round21_omission_regression_checklist_2026_06_25.md`

检查是否还有“之前没提过但同品类重要”的遗漏，至少 25 项，并标注：

- 已有
- 部分已有
- 缺失
- 不应做
- 需要外部 oracle
- 需要用户决策

## 工作包 R：总报告与 Round 22 副手建议

输出：`docs/research/antigravity_round21_final_summary_and_round22_recommendations_2026_06_25.md`

必须汇总：

1. 本轮新增报告列表。
2. 每个工作包一句话结论。
3. 旧结论纠偏表。
4. P0/P1/P2 bug 表。
5. 可复制开源 Top 10。
6. 只能参考 Top 10。
7. 必须等待人工外部工具事项。
8. Codex 可立即做 Top 40。
9. 副手继续可做 Top 40。
10. Git 纳入建议。
11. 生产调参是否允许。
12. Round 22 任务单建议。
