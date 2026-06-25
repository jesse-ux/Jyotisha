# Antigravity AI 副手任务单 Round 19（2026-06-25）

## 任务目标

本轮任务升级为“1/5 外部证据破冰准备 + 当前工作树事实复核 + 高体量开源复用二审”。你必须以当前工作树为准重新验证，不要复述 Round 18 里已经过期的判断。

Codex 主线正在把第一条 JHora/PyJHora 黑盒证据从 0/5 推向 1/5。你要承担高体量只读审计、教程复核、模板安全性复核、外部人工执行清单、许可证复筛和下一轮任务拆解，减少 Codex 主线程算力消耗。

## 当前事实基线

请先独立验证以下事实，不能照抄旧报告：

- `references/oracle/artifacts/README.md` 当前已经存在。
- `references/oracle/artifacts/.gitkeep` 当前已经存在。
- `jyotish-app/main.js` 当前已经调用 `renderOracleEvidenceProgressDashboard()`。
- `scripts/oracle_evidence_validator.py` 当前已经有 `SHADBALA_REQUIRED_PLANETS` 和 `SHADBALA_REQUIRED_COMPONENTS`。
- `python3 scripts/run_quality_gate.py --profile quick --skip-yoga-logic` 在 Codex 上轮已通过。
- `docs/user_jhora_capture_guide.md` 当前可能已经存在，请复核而不是假设缺失。
- `references/oracle/evidence_packet_templates/jhora_steve_jobs_lahiri_first_packet.json` 可能会在 Codex 主线创建，请复核其安全性。

## 工作量要求

本轮至少产出 14 份 `round19` 报告文件。每份报告必须包含：

- 至少 10 个检查点。
- 至少 2 条可复制命令、检索 token 或 URL。
- 至少 1 个 Codex 可直接改的文件建议。
- 明确状态：`已成立`、`部分成立`、`未成立`、`需要人工外部工具`。
- 发现过期结论时必须写“旧结论已过期”，并说明当前证据。
- 所有开源复用建议必须带 license；只允许 MIT/Apache-2.0/BSD/ISC/CC0 进入“可复制候选”，GPL/AGPL/LGPL/闭源只能作为行为参考。

最终汇总必须给 Codex 一个 Top 25 ROI 任务列表，并拆出“现在可做”和“必须等人工 JHora/PyJHora”的任务。

## 严格边界

禁止事项：

- 不要提交、推送、重置、删除、移动、批量格式化或覆盖现有文件。
- 不要读取、记录或传播任何 token、API key、cookie、SSH 私钥、浏览器登录态、系统钥匙串或远程凭证。
- 不要打开、摘录、传播用户私人完整星盘报告、PDF 原件、出生资料正文。
- 不要修改 `scripts/`、`jyotish-app/`、`skills/`、`tests/`、`README.md`、`references/oracle/` 的实现内容。
- 不要把本仓库输出、`template_only`、`local_baseline` 或空目标字段标成 `external_verified`。
- 不要复制 JHora、PyJHora、AGPL/GPL 项目的实现代码、公式常量、内部表格或商业产品截图中的受保护内容。
- 不要使用“绝对可信”“世界第一”“完全校准”等过度准确率话术。

允许事项：

- 只能新增 `docs/research/*round19*2026_06_25.md` 报告文件。
- 可以读取 README、SKILL、progress、task_plan、Round 16-18 报告、本任务单。
- 可以读取 `docs/user_jhora_capture_guide.md`、`references/oracle/**`、`scripts/oracle_collection_queue.py`、`scripts/oracle_evidence_validator.py`、`scripts/jyotish_api_server.py`、`jyotish-app/main.js`、`jyotish-app/style.css`、`jyotish-app/api-bridge.js`、`jyotish-app/public/api-bridge.js`、`tests/**`。
- 可以运行只读命令：`git status`、`git log`、`rg`、`python3 ... --format json`、`pytest`、`npm run build --prefix jyotish-app`、`python3 scripts/run_quality_gate.py --profile quick --skip-yoga-logic`。
- 可以联网检索公开开源项目、公开文档、公开产品页面；只记录 URL、license、能力点和差距，不抓取私人数据。

## 必跑命令

### 1. Git 与当前状态

```bash
git status --short --branch
git log --oneline --decorate -n 10
```

### 2. 事实基线复核

```bash
rg -n "renderOracleEvidenceProgressDashboard|Dasha/Shadbala 真实进度|0 / 5|references/oracle/artifacts|source_artifact|必须打码|不得提交私人 PDF 原件|不得提交完整出生报告|浏览器 scratch" \
  README.md docs/user_jhora_capture_guide.md references/oracle jyotish-app/main.js tests
```

### 3. Shadbala 强校验

```bash
rg -n "SHADBALA_REQUIRED_PLANETS|SHADBALA_REQUIRED_COMPONENTS|missing_shadbala_component|Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|sthana|dig|kala|chesta|naisargika|drik" \
  scripts/oracle_evidence_validator.py tests/test_oracle_evidence_validator.py tests/test_oracle_collection_queue.py tests/test_api_server_security.py
```

### 4. Evidence 队列与 validator

```bash
python3 scripts/oracle_collection_queue.py \
  --oracle-file references/oracle/dasha_shadbala_oracle_cases.json \
  --format json > /tmp/jyotish_oracle_queue_round19.json

python3 scripts/oracle_evidence_validator.py \
  --queue-file /tmp/jyotish_oracle_queue_round19.json
```

### 5. Targeted tests

```bash
python3 -m pytest -q \
  tests/test_frontend_productization.py::test_first_jhora_capture_guide_is_actionable \
  tests/test_frontend_productization.py::test_trust_center_exposes_oracle_evidence_intake_cards \
  tests/test_frontend_productization.py::test_oracle_artifact_storage_policy_is_documented \
  tests/test_oracle_collection_queue.py \
  tests/test_oracle_evidence_validator.py \
  tests/test_api_server_security.py::test_oracle_evidence_api_validates_uploaded_packets
```

### 6. Build / quality gate

```bash
npm run build --prefix jyotish-app
python3 scripts/run_quality_gate.py --profile quick --skip-yoga-logic
```

若失败，必须列出失败测试名、断言、真实风险等级和最小修复文件。

## 工作包 A：Round 18 旧结论复核与纠偏

输出：`docs/research/antigravity_round19_round18_claim_recheck_2026_06_25.md`

至少检查：

1. artifacts README 是否已存在。
2. artifacts `.gitkeep` 是否已存在。
3. Trust Center progress dashboard 是否已调用。
4. progress dashboard 是否包含 `0 / 5`。
5. Shadbala 七曜六分量数组是否已存在。
6. mobile layout gate 是否已通过。
7. api bridge public/source 是否一致。
8. `.gitignore` 是否已有 `output_report.txt`。
9. `.gitignore` 是否已有 `results_extracted.md`。
10. 哪些 Round 18 P1 仍成立。
11. 哪些 Round 18 P1 已过期。
12. Codex 下一步不应重复做什么。

## 工作包 B：JHora/PyJHora 教程可执行性复核

输出：`docs/research/antigravity_round19_jhora_capture_guide_review_2026_06_25.md`

至少检查：

1. `docs/user_jhora_capture_guide.md` 是否存在。
2. 是否优先建议 Steve Jobs 或合成样本。
3. 是否覆盖 Lahiri/Raman/KP。
4. 是否覆盖 mean node / true node。
5. 是否覆盖 Moon sidereal longitude。
6. 是否覆盖 Vimshottari start date。
7. 是否覆盖 Shadbala 七曜六分量。
8. 是否列出 Sun/Moon/Mars/Mercury/Jupiter/Venus/Saturn。
9. 是否列出 sthana/dig/kala/chesta/naisargika/drik。
10. 是否说明 `references/oracle/artifacts/` 命名。
11. 是否说明 `source_artifact`。
12. 是否说明 `external_verified` 晋级。
13. 是否说明 validator 命令。
14. 是否说明退回重采条件。
15. 是否避免要求提交私人 PDF 原件。

## 工作包 C：第一条 evidence packet 模板安全性复核

输出：`docs/research/antigravity_round19_first_packet_template_audit_2026_06_25.md`

如果模板存在，至少检查：

1. 文件路径是否为 `references/oracle/evidence_packet_templates/jhora_steve_jobs_lahiri_first_packet.json`。
2. 是否仍为 `status=draft`。
3. 是否没有伪造外部数值。
4. 是否包含 `template_steve_jobs_dasha_lahiri`。
5. metadata 是否保留空位。
6. `source_artifact` 是否指向 `references/oracle/artifacts/`。
7. ayanamsa 是否为 Lahiri。
8. node mode 是否为 true node。
9. Vimshottari target 是否为 null。
10. Shadbala 七曜是否齐全。
11. 六分量是否齐全。
12. 所有分量是否为 null 而不是本地计算值。
13. integrity checks 是否拒绝本地引擎。
14. validator 对该模板是否保持不通过。

如果模板不存在，请写明 Codex 应该新建的最小 JSON 结构。

## 工作包 D：1/5 真实样本人工执行单

输出：`docs/research/antigravity_round19_human_jhora_1_of_5_runbook_2026_06_25.md`

请写一份发给真实人工执行者的 runbook，要求：

1. 使用公开 Steve Jobs 样本优先。
2. 不使用用户私人样本作为第一条。
3. JHora 输入字段逐项列出。
4. PyJHora 黑盒 stdout 替代路径逐项列出。
5. 截图文件命名规范。
6. 必须打码清单。
7. 要采集的 3 张核心截图。
8. 要填写的 JSON 字段。
9. 退回重采标准。
10. 完成后如何交给 Codex。
11. 为什么 `valid_packets: 1` 仍不等于生产调参。
12. 需要人工外部工具，不能由 Codex 本地引擎代替。

## 工作包 E：runtime-smoke HTML 与本地输出卫生审计

输出：`docs/research/antigravity_round19_runtime_artifact_hygiene_2026_06_25.md`

至少检查：

1. `.gitignore` 是否屏蔽 `runtime-smoke-report-*.html`。
2. 是否存在未跟踪 runtime smoke HTML。
3. 是否存在 `output_report.txt`。
4. 是否存在 `results_extracted.md`。
5. 是否存在私人 PDF。
6. 是否存在完整出生报告。
7. 是否存在浏览器 scratch。
8. 是否有 artifacts 目录误收私人文件。
9. 是否有 dist 构建产物需要忽略。
10. Codex 下一步最小 `.gitignore` 建议。

## 工作包 F：前端 progress dashboard 真实 DOM/用户体验复核

输出：`docs/research/antigravity_round19_progress_dashboard_dom_ux_2026_06_25.md`

至少检查：

1. 函数是否定义。
2. 函数是否被 `renderOracleEvidenceIntakePanel()` 调用。
3. 是否显示 `Dasha/Shadbala 真实进度`。
4. 是否显示 `0 / 5`。
5. 是否显示 `valid_packets`。
6. 是否显示 `ready_for_calibration`。
7. 是否显示 `production_tuning_allowed=false`。
8. 是否显示 artifact 路径。
9. 是否提示隐私。
10. 移动端 CSS 是否单列。
11. 用户是否能理解“0/5 是等待外部证据，不是功能坏了”。
12. 是否建议 Playwright 截图。

## 工作包 G：开源许可证复筛 Top 30

输出：`docs/research/antigravity_round19_open_source_license_rescreen_2026_06_25.md`

联网检索至少 30 个相关项目，字段：

- project
- URL
- license
- latest activity
- relevant feature
- direct reuse allowed?
- copy-safe candidate files/modules
- reference-only areas
- legal risk
- Codex action

必须分三类：

- 可复制/改写候选：MIT/Apache-2.0/BSD/ISC/CC0。
- 只能行为参考：GPL/AGPL/LGPL/闭源/商业。
- 需要许可证复核：license 不明或冲突。

## 工作包 H：Ashtakoot 合婚下一阶段破冰方案

输出：`docs/research/antigravity_round19_ashtakoot_breakthrough_plan_2026_06_25.md`

Round 18 指出 Ashtakoot 用户价值高，请复核并拆成可执行计划：

1. 当前项目已有 Ashtakoot 能力在哪里。
2. 前端是否露出给普通用户。
3. API 是否已有。
4. 需要哪些 UI。
5. 需要哪些 external oracle cases。
6. 可复用开源候选。
7. 不可复制项目。
8. 测试建议。
9. 首批 3 个样本建议。
10. Codex 最小实现顺序。

## 工作包 I：Shadbala 单位/格式下一轮校验方案

输出：`docs/research/antigravity_round19_shadbala_unit_format_plan_2026_06_25.md`

至少设计：

1. 当前 validator 只检查完整性还是检查类型。
2. 是否应该要求 int/float。
3. 是否允许字符串数字。
4. Rupa/Virupa 单位如何记录。
5. 负数如何处理。
6. 极端大数如何处理。
7. total 与 component sum 是否要检查。
8. JHora/PyJHora 显示差异。
9. 需要哪些测试。
10. 是否应进入 Round 20。

## 工作包 J：AI Prompt Pack 加入 oracle progress 的建议

输出：`docs/research/antigravity_round19_ai_prompt_oracle_progress_plan_2026_06_25.md`

至少检查：

1. `ai_prompt_pack` 当前是否包含 oracle progress。
2. 是否包含 Dasha/Shadbala 边界。
3. 是否包含 `valid_packets: 0`。
4. 是否包含 `production_tuning_allowed: false`。
5. 是否应把 `references/oracle/artifacts/` 写入 retrieval plan。
6. 是否应把 external_verified 规则写入 prompt。
7. 是否避免误导 AI 说已校准。
8. 修改文件建议。
9. 测试建议。
10. 用户价值。

## 工作包 K：全链路用户压力测试脚本建议

输出：`docs/research/antigravity_round19_user_flow_automation_plan_2026_06_25.md`

设计至少 25 条可自动化用户流程，重点包括：

- 下载 evidence packet。
- 导入空 packet。
- 导入缺 Shadbala packet。
- 导入完整但本地引擎伪造 packet。
- 导入完整外部 packet 草稿。
- 导入 external_verified 但缺 artifact。
- 移动端查看 progress dashboard。
- 复制 AI Prompt Pack。
- 无 API 静态壳。
- API 恢复路径。

每条写预期结果、风险、自动化工具建议。

## 工作包 L：Git 远端/未跟踪文件纳入策略

输出：`docs/research/antigravity_round19_git_tracking_strategy_2026_06_25.md`

至少检查：

1. 当前 branch。
2. ahead/behind。
3. Round 16-19 工作单是否未跟踪。
4. Round 16-18 报告是否未跟踪。
5. artifacts README 是否未跟踪。
6. guide 是否未跟踪。
7. template 是否未跟踪。
8. 哪些必须纳入 Git。
9. 哪些不应纳入 Git。
10. 是否存在敏感文件。
11. Codex 最小 stage 清单。
12. 是否需要推送。

## 工作包 M：Round 20 副手任务建议

输出：`docs/research/antigravity_round19_round20_sidecar_recommendations_2026_06_25.md`

请给出下一轮副手任务的建议，至少 10 个工作包，继续把高体量研究交给副手。

## 工作包 N：Codex Round 20 执行计划

输出：`docs/research/antigravity_round19_codex_round20_execution_plan_2026_06_25.md`

请按以下结构输出：

1. 当前已成立能力。
2. 当前未成立能力。
3. 必须先修的 P0/P1。
4. 可直接修改的文件。
5. 可直接新增的测试。
6. 必须等待人工工具的任务。
7. 可复用开源候选。
8. 只能参考项目。
9. 隐私/许可证风险。
10. Top 25 ROI 任务。

## 最终汇总格式

完成后请输出：

1. 已创建文件列表。
2. 每个工作包一句话结论。
3. 过期旧结论纠偏表。
4. 当前 P0/P1/P2 bug 表。
5. 可直接复用开源项目 Top 5。
6. 只能参考不能复制项目 Top 5。
7. 必须等待人工外部工具的事项。
8. 给 Codex 的 Top 25 下一步。

结尾必须明确写：

> 下一步建议 Codex 优先……
