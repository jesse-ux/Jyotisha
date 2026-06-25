# Antigravity AI 副手任务单 Round 18（2026-06-25）

## 任务目标

本轮升级为“重型外部对标 + 当前补丁复核 + 可复用资产筛选”任务。Codex 主线正在修复 Round 17 暴露的基建缺口，包括：

1. `references/oracle/artifacts/` 外部证据归档与隐私打码规范。
2. `scripts/oracle_evidence_validator.py` 对 Shadbala 七曜六分量的强校验。
3. Trust Center 的 Dasha/Shadbala 真实采集进度面板。
4. `test_mobile_layout_keeps_dense_sections_single_column` 移动端布局门禁失败。
5. 第一条 JHora/PyJHora 真实外部样本教程和录入流程。

你的任务不是替 Codex 写核心实现，而是尽量提前承担高体量探索、黑盒复核、全网开源对标、许可证风险判断和下一轮任务拆解，减少 Codex 在主线程里的算力消耗。

## 工作量升级要求

本轮必须至少产出 12 份 `round18` 报告文件。每份报告必须包含：

- 至少 10 个明确检查点。
- 至少 2 条可复制命令、搜索 query、URL 或代码检索 token。
- 至少 1 个“Codex 应该改哪个文件/哪类测试”的落地建议。
- 明确标注 `已成立`、`部分成立`、`未成立` 或 `需要人工外部工具`。
- 如果引用开源项目，必须记录项目 URL、license、可复用范围、不可复制范围。
- 如果发现可以直接复用的代码，只允许推荐 MIT/Apache-2.0/BSD/ISC/CC0 等宽松许可证；GPL/AGPL/LGPL/商业闭源项目只能用于功能对标和行为观察，不得建议复制实现。

最终总报告必须给 Codex 一个按 ROI 排序的 Top 20 待办清单，并单独列出“必须等待用户或外部人工工具”的事项。

## 严格边界

禁止事项：

- 不要提交、推送、重置、删除、移动、批量格式化或覆盖现有文件。
- 不要读取、记录、传播任何 GitHub token、API key、cookie、SSH 私钥、浏览器登录态、系统钥匙串或远程凭证。
- 不要打开、摘录或扩散用户私人完整星盘报告、PDF 原件、出生资料正文。
- 不要修改 `scripts/`、`jyotish-app/`、`skills/`、`tests/`、`README.md`、`references/oracle/` 的实现内容。
- 不要把本仓库输出、`template_only`、`local_baseline` 或空目标字段标成 `external_verified`。
- 不要复制 JHora、PyJHora、AGPL/GPL 项目的实现代码、公式常量、内部表格或商业产品截图中的受保护内容。
- 不要使用“绝对可信”“世界第一”“完全校准”等过度准确率话术。

允许事项：

- 可以新增 `docs/research/*round18*2026_06_25.md` 报告文件。
- 可以读取 `README.md`、`SKILL.md`、`progress.md`、`task_plan.md`、Round 16/17 报告、本任务单。
- 可以读取 `references/oracle/dasha_shadbala_oracle_cases.json`、`references/oracle/artifacts/README.md`、`scripts/oracle_collection_queue.py`、`scripts/oracle_evidence_validator.py`、`scripts/run_quality_gate.py`、`scripts/jyotish_api_server.py`、`jyotish-app/main.js`、`jyotish-app/style.css`、`tests/test_frontend_productization.py`、`tests/test_oracle_evidence_validator.py`、`tests/test_api_server_security.py`，只做复核。
- 可以运行只读命令：`git status`、`git log`、`rg`、`python3 ... --format json`、`pytest`、`npm run build --prefix jyotish-app`、`python3 scripts/run_quality_gate.py --profile quick --skip-yoga-logic`。
- 可以联网检索公开开源项目、公开文档、公开产品页面；只记录 URL、license、能力点和差距，不抓取私人数据。

## 当前主线状态提示

注意：Round 17 报告可能是在 Codex 最新补丁之前运行的。你必须以当前工作树为准重新验证，不要复述旧结论。

当前需要重点复核的事实：

- `.gitignore` 当前已经包含 `output_report.txt` 和 `results_extracted.md`，请验证是否还存在其它高风险本地输出未屏蔽。
- `references/oracle/artifacts/README.md` 当前可能已经存在，请验证其中是否包含 `source_artifact`、`external_oracle_artifact`、`必须打码`、`不得提交私人 PDF 原件`、`不得提交完整出生报告`、`浏览器 scratch`。
- `scripts/oracle_evidence_validator.py` 当前可能已经包含 `SHADBALA_REQUIRED_PLANETS` 和 `SHADBALA_REQUIRED_COMPONENTS`，请验证是否真的拦截七曜六分量，而不是只检查空 dict。
- `jyotish-app/main.js` 当前可能已经包含 `renderOracleEvidenceProgressDashboard`，请验证用户是否能看懂 `0 / 5` 和隐私边界。
- 已知当前门禁失败点：`tests/test_frontend_productization.py::test_mobile_layout_keeps_dense_sections_single_column`，请定位是 CSS 真缺口还是测试断言字符串过脆。

## 必跑命令

### 1. Git / 当前补丁状态

```bash
git status --short --branch
git log --oneline --decorate -n 10
```

### 2. Oracle artifact 与隐私规范

```bash
rg -n "references/oracle/artifacts|source_artifact|external_oracle_artifact|必须打码|不得提交私人 PDF 原件|不得提交完整出生报告|浏览器 scratch|output_report|results_extracted" \
  .gitignore README.md references/oracle docs/research tests jyotish-app/main.js
```

### 3. Shadbala 七曜六分量强校验

```bash
rg -n "SHADBALA_REQUIRED_PLANETS|SHADBALA_REQUIRED_COMPONENTS|missing_shadbala_component|Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|sthana|dig|kala|chesta|naisargika|drik" \
  scripts/oracle_evidence_validator.py tests/test_oracle_evidence_validator.py tests/test_api_server_security.py
```

### 4. Evidence queue / validator

```bash
python3 scripts/oracle_collection_queue.py \
  --oracle-file references/oracle/dasha_shadbala_oracle_cases.json \
  --format json > /tmp/jyotish_oracle_queue_round18.json

python3 scripts/oracle_evidence_validator.py \
  --queue-file /tmp/jyotish_oracle_queue_round18.json
```

### 5. Targeted tests

```bash
python3 -m pytest -q \
  tests/test_oracle_evidence_validator.py \
  tests/test_frontend_productization.py::test_trust_center_exposes_oracle_evidence_intake_cards \
  tests/test_frontend_productization.py::test_oracle_artifact_storage_policy_is_documented \
  tests/test_api_server_security.py::test_oracle_evidence_api_validates_uploaded_packets
```

### 6. Known failing mobile gate

```bash
python3 -m pytest -q \
  tests/test_frontend_productization.py::test_mobile_layout_keeps_dense_sections_single_column
```

请在报告中明确：

- 失败的确切断言。
- CSS 中实际存在的相关 media query。
- 是产品布局真风险，还是测试硬编码字符串需要同步。
- Codex 最小修复建议。

### 7. Build / quality gate

```bash
npm run build --prefix jyotish-app
python3 scripts/run_quality_gate.py --profile quick --skip-yoga-logic
```

如果 quality gate 失败，必须把失败测试按 P0/P1/P2 分类，不允许只写“失败”。

## 全网开源对标任务

请联网检索并报告至少 15 个同品类或相关开源项目。优先包括但不限于：

- PyJHora
- VedAstro
- Maitreya
- Swiss Ephemeris wrappers
- flatlib
- Kerykeion
- astrology-js / astrology libraries
- panchanga / hindu calendar libraries
- jyotish / vedic astrology Python/JS/Rust projects
- muhurta / panchangam calculators
- KP astrology calculators
- ashtakavarga/yoga calculators
- chart rendering components
- desktop/web astrology apps with public source

每个项目必须记录：

- URL
- license
- 活跃度（最近提交/版本，如果可见）
- 可对标功能
- 可复用代码范围
- 不可复制/只可参考范围
- 与本项目当前能力差距
- 是否值得 Codex 下一步集成或借鉴

建议搜索 query：

```text
vedic astrology open source MIT JavaScript
jyotish calculator open source Python license
PyJHora GitHub license shadbala dasha
VedAstro GitHub license Vedic astrology API
ashtakavarga calculator GitHub license
panchanga calculator GitHub MIT
KP astrology open source GitHub
muhurta calculator open source GitHub
Swiss Ephemeris JavaScript wrapper license
Maitreya astrology source license
```

## 工作包 A：当前补丁后 artifact 存档规范复核

输出：`docs/research/antigravity_round18_artifact_storage_current_postfix_2026_06_25.md`

至少检查：

1. `references/oracle/artifacts/README.md` 是否存在。
2. 是否存在 `.gitkeep` 或其它占位，保证目录入库。
3. `README.md` 是否公开写明 `references/oracle/artifacts/`。
4. `source_artifact` 是否被限定为脱敏外部证据。
5. 是否出现 `external_oracle_artifact`。
6. 是否明确“必须打码”。
7. 是否明确“不得提交私人 PDF 原件”。
8. 是否明确“不得提交完整出生报告”。
9. 是否明确“浏览器 scratch” 不可提交。
10. Web 下载证据包是否提示 artifact 路径与打码。
11. 是否还有其它高风险本地输出应加入 `.gitignore`。
12. 是否存在把本地计算输出伪装成外部 evidence 的路径。

## 工作包 B：Shadbala 七曜六分量强校验黑盒复核

输出：`docs/research/antigravity_round18_shadbala_seven_planet_validator_2026_06_25.md`

至少检查：

1. 是否存在 `SHADBALA_REQUIRED_PLANETS`。
2. 是否存在 `SHADBALA_REQUIRED_COMPONENTS`。
3. 七曜是否包含 Sun/Moon/Mars/Mercury/Jupiter/Venus/Saturn。
4. 六分量是否包含 sthana/dig/kala/chesta/naisargika/drik。
5. 空 `{}` 是否返回 `missing_shadbala_component:all_planets`。
6. 只填 Sun 两项是否拦截 Sun 缺项。
7. 只填 Sun 是否拦截 Moon 等缺失行。
8. 完整七曜六分量是否通过。
9. 是否避免 `reject_global_shadbala_scaling` 被误认为真实分量。
10. API 层上传 evidence 是否复用同一 validator。
11. 错误信息是否适合前端给用户阅读。
12. 是否需要把单位/格式也纳入下一轮校验。

## 工作包 C：Trust Center 真实进度仪表盘复核

输出：`docs/research/antigravity_round18_trust_center_progress_dashboard_2026_06_25.md`

至少检查：

1. 是否存在 `renderOracleEvidenceProgressDashboard`。
2. 是否显示 `Dasha/Shadbala 真实进度`。
3. 是否显示 `0 / 5`。
4. 是否显示 `valid_packets`。
5. 是否显示 `ready_for_calibration`。
6. 是否显示 `production_tuning_allowed=false`。
7. 是否显示 `references/oracle/artifacts/`。
8. 是否提示 `source_artifact`。
9. 是否提示“必须打码”。
10. 是否提到 `missing_shadbala_component`。
11. 用户是否能区分 D1/D9/SAV 已较高可信和 Dasha/Shadbala 尚未外部校准。
12. 移动端是否可能因为新增面板溢出。

## 工作包 D：移动端布局失败根因分析

输出：`docs/research/antigravity_round18_mobile_layout_gate_root_cause_2026_06_25.md`

至少检查：

1. 失败测试的完整断言。
2. CSS 当前 `@media` 区块真实文本。
3. `.calculation-settings-grid` 是否仍会单列。
4. `.rule-variant-grid` 是否仍会单列。
5. `.first-use-grid` 是否仍会单列。
6. `.runtime-health-grid` 是否仍会单列。
7. `.trust-status-grid` 是否仍会单列。
8. `.terminology-mode-options` 是否仍会单列。
9. `.case-workspace-controls` 是否仍会单列。
10. 是真实布局风险还是测试字符串过度严格。
11. 最小 CSS 修复建议。
12. 是否需要 Playwright mobile screenshot 复核。

## 工作包 E：第一条 JHora/PyJHora 真实样本教程

输出：`docs/research/antigravity_round18_first_jhora_capture_guide_draft_2026_06_25.md`

请写出可直接给志愿者使用的教程草稿，但不要包含私人数据。至少覆盖：

1. 推荐先用公开人物 Steve Jobs 或合成样本。
2. JHora 设置 Lahiri/Raman/KP ayanamsa 的步骤。
3. mean/true node 的标注要求。
4. 时区与地点输入检查。
5. Moon sidereal longitude 截图要求。
6. Vimshottari 起点截图要求。
7. Shadbala 七曜六分量表截图要求。
8. 保存到 `references/oracle/artifacts/` 的命名规范。
9. 如何打码。
10. 如何填写 `source_artifact`。
11. 如何把 evidence packet 从 `draft` 升为待审。
12. 如何运行 validator。
13. 哪些情况必须退回重采。
14. 截图不够清晰时的最小补采清单。

## 工作包 F：全网开源项目许可证与可复用性矩阵

输出：`docs/research/antigravity_round18_open_source_reuse_matrix_2026_06_25.md`

至少 15 个项目，每个项目按以下字段列成表：

- project
- URL
- license
- language
- last activity
- relevant features
- reusable directly?
- copy-safe code candidates
- reference-only areas
- risks
- Codex action

必须单独列出：

- 可以直接复制/改写的宽松许可证代码候选。
- 只能学习行为、不能复制实现的项目。
- 需要法律/许可证复核的项目。

## 工作包 G：印度占星功能缺口重新排序

输出：`docs/research/antigravity_round18_jyotish_feature_gap_rerank_2026_06_25.md`

请对标成熟印度占星软件/开源项目，给出至少 30 个功能缺口或深化点，按用户价值和实现风险排序。至少覆盖：

- Dasha 体系
- Shadbala
- Ashtakavarga
- Vargas
- Yogas
- Panchanga
- Muhurta
- Prashna / KP
- Compatibility / Ashtakoot
- Tajika / Varshaphala
- Remedial suggestions
- Chart rendering / South-North-East style
- Report export
- Evidence/accuracy transparency
- AI explanation / prompt pack
- Localization / Chinese terminology

## 工作包 H：用户黑盒流程压力测试计划

输出：`docs/research/antigravity_round18_user_flow_stress_plan_2026_06_25.md`

至少设计 20 条用户流程，覆盖：

1. 新用户无后端 API 打开网页。
2. 用户填写出生信息后首次计算。
3. 用户切换 Lahiri/Raman/KP。
4. 用户查看 D1/D9/SAV。
5. 用户打开 Dasha/Shadbala 边界说明。
6. 用户下载 Evidence Packet。
7. 用户导入空 evidence packet。
8. 用户导入本地引擎伪造 packet。
9. 用户导入缺 Shadbala 分量 packet。
10. 用户导入完整七曜六分量 packet。
11. 用户尝试移动端查看 Trust Center。
12. 用户导出报告。
13. 用户复制 AI Prompt Pack。
14. 用户打开术语/文档。
15. 用户查看关系合盘。
16. 用户查看 Muhurta。
17. 用户查看 KP/Prashna。
18. 用户使用极端纬度案例。
19. 用户无网络情况下使用。
20. 用户遇到 API 失败后的恢复路径。

每条流程给出预期结果、风险、需要的自动化测试建议。

## 工作包 I：隐私与仓库卫生审计

输出：`docs/research/antigravity_round18_privacy_repo_hygiene_audit_2026_06_25.md`

至少检查：

1. `.gitignore` 对命理输出文本的覆盖。
2. 是否有 `output_report`。
3. 是否有 `results_extracted`。
4. 是否有疑似 `api_key`。
5. 是否有疑似 `token`。
6. 是否有 cookie/session。
7. 是否有私人 PDF。
8. 是否有完整出生报告。
9. 是否有浏览器 scratch。
10. 是否有 remote URL 嵌入凭证。只报告“嵌入凭证”，不要打印 token。
11. 是否有 docs 中误导上传私人数据的文案。
12. 下一轮 `.gitignore` 建议。

## 工作包 J：测试债与 CI 门禁分流

输出：`docs/research/antigravity_round18_test_debt_ci_triage_2026_06_25.md`

至少输出：

- 当前 targeted tests 结果。
- 当前 build 结果。
- 当前 quick quality gate 结果。
- 失败测试列表。
- 每个失败的真实风险等级。
- 哪些是产品 bug。
- 哪些是测试断言陈旧。
- 哪些需要 Playwright。
- 哪些需要真实外部 artifact。
- Codex 最小修复顺序。

## 工作包 K：AI Prompt Pack / Skill 同步复核

输出：`docs/research/antigravity_round18_ai_prompt_pack_skill_sync_2026_06_25.md`

至少检查：

1. `ai_prompt_pack` 后端是否输出。
2. 前端是否可复制 Prompt。
3. 前端是否可复制 Evidence。
4. Prompt 是否包含 D1/D9/Dasha/Shadbala/Ashtakavarga 证据快照。
5. 是否提示 Dasha/Shadbala 尚未外部校准。
6. Skill 文档是否同步这些边界。
7. API bridge 是否同步。
8. 是否存在夸大准确率话术。
9. 是否需要加入 oracle progress 摘要。
10. 是否需要加入 license/source provenance 摘要。

## 工作包 L：Round 19 给 Codex 的执行清单

输出：`docs/research/antigravity_round18_codex_round19_execution_plan_2026_06_25.md`

请按以下结构写：

1. 当前已成立的能力。
2. 当前未成立的能力。
3. 必须先修的 P0/P1。
4. 可并行交给副手继续做的研究任务。
5. 需要用户人工外部截图的任务。
6. 建议 Codex 立刻修改的文件。
7. 建议新增/修改的测试。
8. 下一轮开源复用候选。
9. 下一轮 UI/UX 优化候选。
10. Top 20 ROI 排序任务。

## 最终汇总格式

完成后请输出：

1. 已创建文件列表。
2. 每个工作包一句话结论。
3. 当前 P0/P1/P2 bug 表。
4. 可直接复用开源项目 Top 5。
5. 只能参考不能复制项目 Top 5。
6. 必须等待人工外部工具的事项。
7. 给 Codex 的 Top 20 下一步。

结尾必须明确写：

> 下一步建议 Codex 优先……
