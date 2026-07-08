# Antigravity AI 副手任务单 Round 17（2026-06-25）

## 任务目标

本轮继续做只读黑盒复核，但工作量升级为“重型并行审计包”。Codex 主线将修复 Round 16 暴露的三类缺口：

1. `references/oracle/artifacts/` 外部截图/工件存档规范。
2. `scripts/oracle_evidence_validator.py` 对 Shadbala 六分量的强校验。
3. Trust Center 中 Dasha/Shadbala 外部真值采集进度仪表盘。

请并行复核这些修复是否真正落地，并把下一批 oracle、公开教程、全球对标、用户端交付和风险话术拆到可直接交给 Codex 的粒度。你只做复核、对标、报告，不修改核心实现。

## 工作量升级要求

本轮不接受只写 1-2 页的轻量报告。每个工作包必须包含：

- 至少 8 个明确检查点。
- 至少 1 个可复制命令或搜索 token。
- 至少 1 个“如果失败，Codex 应该改哪个文件”的建议。
- 明确标注是否需要人工外部截图。
- 区分 `已成立`、`部分成立`、`未成立`，不要只写模糊判断。

最终至少产出 9 份 `round17` 报告文件。若某项无法验证，写明阻断原因和下一步最小复现命令。

## 严格边界

禁止事项：

- 不要提交、推送、重置、删除、移动、批量格式化或覆盖现有文件。
- 不要读取、记录、传播任何 GitHub token、API key、浏览器登录态、cookie、SSH 私钥或系统钥匙串。
- 不要打开或摘录用户私人星盘完整报告正文。
- 不要修改 `scripts/`、`jyotish-app/`、`skills/`、`SKILL.md`、`tests/`、`README.md`、`references/oracle/` 的实现内容。
- 不要把 `output_report.txt`、`results_extracted.md`、PDF 原件、Antigravity scratch 或私人出生资料纳入同步建议。
- 不要复制 JHora、PyJHora、AGPL/GPL 项目的实现代码、公式常量或内部数据表。
- 不要把 `template_only`、`local_baseline`、本仓库输出或空目标字段标成 `external_verified`。
- 不要使用“绝对可信”“世界第一”“完全校准”等过度准确率话术。

允许事项：

- 可以读取 `README.md`、`SKILL.md`、`progress.md`、`task_plan.md`。
- 可以读取 `docs/research/*round16*`、本任务单和相关公开研究报告。
- 可以读取 `references/oracle/dasha_shadbala_oracle_cases.json`、`references/oracle/artifacts/README.md`、`scripts/oracle_collection_queue.py`、`scripts/oracle_evidence_validator.py`、`scripts/jyotish_api_server.py`、`jyotish-app/main.js`、`jyotish-app/style.css`、`api-bridge.js`、`tests/test_frontend_productization.py`、`tests/test_api_server_security.py`、`tests/test_oracle_evidence_validator.py`，只做复核。
- 可以运行只读命令：`git status`、`git log`、`rg`、`python3 ... --format json`、`pytest`、`npm run build --prefix jyotish-app`。
- 只能新增 `docs/research/*round17*2026_06_25.md` 报告文件。

## 必跑命令

### 1. Git / 本地状态复核

```bash
git status --short --branch
git log --oneline --decorate -n 8
```

### 2. Artifacts 存档规范复核

```bash
rg -n "references/oracle/artifacts|source_artifact|external_oracle_artifact|必须打码|不得提交私人 PDF 原件|不得提交完整出生报告|浏览器 scratch" \
  README.md \
  references/oracle \
  docs/research \
  tests \
  jyotish-app/main.js
```

### 3. Shadbala 六分量强校验复核

```bash
rg -n "SHADBALA_REQUIRED_COMPONENTS|missing_shadbala_component|sthana|dig|kala|chesta|naisargika|drik|reject_global_shadbala_scaling" \
  scripts/oracle_evidence_validator.py \
  tests/test_oracle_evidence_validator.py \
  tests/test_api_server_security.py
```

### 4. Oracle / evidence gate 复验

```bash
python3 scripts/oracle_collection_queue.py \
  --oracle-file references/oracle/dasha_shadbala_oracle_cases.json \
  --format json > /tmp/jyotish_oracle_queue_round17.json
```

```bash
python3 scripts/oracle_evidence_validator.py \
  --queue-file /tmp/jyotish_oracle_queue_round17.json
```

```bash
python3 -B -m pytest \
  tests/test_oracle_collection_queue.py \
  tests/test_oracle_evidence_validator.py \
  tests/test_api_server_security.py::test_oracle_evidence_api_validates_uploaded_packets \
  tests/test_frontend_productization.py::test_trust_center_exposes_oracle_evidence_intake_cards \
  tests/test_frontend_productization.py::test_oracle_artifact_storage_policy_is_documented \
  -q
```

### 5. 用户端构建复核

```bash
npm run build --prefix jyotish-app
```

### 6. 质量门与发布路径只读复核

```bash
python3 scripts/run_quality_gate.py --profile quick --skip-yoga-logic
```

如果该命令耗时或失败，不要修代码；把 stdout/stderr 关键片段写入报告，并判断失败属于环境、测试、还是产品逻辑。

### 7. 前端静态边界复核

```bash
rg -n "static_demo_boundary|Local API required|Validation Transparency|Oracle Evidence Intake|Dasha/Shadbala Calibration Status|AI Prompt Pack" \
  jyotish-app/index.html \
  jyotish-app/main.js \
  jyotish-app/style.css \
  README.md
```

### 8. Skill / Web App 同步复核

```bash
rg -n "Shadbala|Dasha|external_oracle|ai_prompt_pack|Ayanamsa|Oracle Evidence|references/oracle/artifacts" \
  SKILL.md \
  skills \
  jyotish-app \
  scripts \
  tests
```

## 工作包 A：Artifacts 存档规范修复后黑盒复核

输出文件：

- `docs/research/antigravity_round17_artifact_storage_postfix_2026_06_25.md`

固定小节：

1. 对标
2. 开源参考
3. Bug

判断：

- `references/oracle/artifacts/README.md` 是否存在。
- Evidence Packet 下载文案是否提示 `source_artifact` 应写相对路径。
- 是否明确要求私人截图必须打码。
- 是否禁止私人 PDF 原件、完整出生报告、浏览器 scratch 入库。
- 是否仍允许公开名人或合成样本在脱敏后进入 artifacts。

## 工作包 B：Shadbala 六分量强校验修复后复核

输出文件：

- `docs/research/antigravity_round17_shadbala_component_validator_postfix_2026_06_25.md`

请检查 validator 是否强制七曜每颗具备：

- `sthana`
- `dig`
- `kala`
- `chesta`
- `naisargika`
- `drik`

输出：

| 规则 | 是否检查 | 证据 token | 仍有缺口 |
|---|---|---|---|

额外要求：

- 构造或引用测试中“缺 `kala/chesta/naisargika/drik` 应失败”的证据。
- 确认空 `{}` 不能蒙混过关。
- 确认本地引擎输出仍会被 `local_engine_artifact_rejected` 拦截。

## 工作包 C：Trust Center 真实进度仪表盘黑盒复核

输出文件：

- `docs/research/antigravity_round17_accuracy_dashboard_blackbox_2026_06_25.md`

请检查用户端是否展示：

| 指标 | 是否可见 | 当前值 | 用户是否能理解 |
|---|---|---|---|

至少包含：

- total template cases
- valid packets
- ready for calibration
- production tuning allowed
- D1/D9/SAV confidence
- Dasha boundary calibration
- Shadbala absolute calibration

## 工作包 D：第一条 JHora 样本公开教程复核

输出文件：

- `docs/research/antigravity_round17_first_jhora_guide_review_2026_06_25.md`

请检查是否已有可公开给志愿者的教程，并判断：

- 输入项是否与 `template_private_oracle_redacted` 一致。
- 是否明确 JHora 只做黑盒取数，不复制实现。
- 是否说明要截哪些页面、摘哪些字段。
- 是否说明如何填写 `source_artifact`、Moon longitude、Vimshottari start date、Shadbala 六分量。
- 是否说明哪些情况不能晋级。

## 工作包 E：下一批 oracle 样本扩展建议

输出文件：

- `docs/research/antigravity_round17_next_oracle_sample_matrix_2026_06_25.md`

请设计下一批样本矩阵，至少覆盖：

- Ashtakoot 合婚。
- KP Horary。
- Muhurta date-range solver。
- Bhava Chalit Sripati/Placidus。
- D24/D30/D60 深分盘模板。

每个样本必须说明：

| 样本 | 外部来源 | 目标字段 | source_artifact 类型 | 是否需要人工截图 | 风险 |
|---|---|---|---|---|---|

## 工作包 F：给 Codex 的 Round 18 任务建议

输出文件：

- `docs/research/antigravity_round17_codex_round18_recommendations_2026_06_25.md`

请给出 5-8 个可执行任务，每个任务必须包含：

- 文件路径
- 测试命令
- 验收标准
- 是否需要用户人工提供外部截图

优先考虑：

1. 生成公开版 JHora 样本采集教程。
2. 将 artifact storage policy 显示到 Evidence Packet 下载结果中。
3. 将 Dasha/Shadbala 进度仪表盘接入导出 HTML/JSON。
4. 新增 Ashtakoot/KP Horary/Muhurta oracle template cases。
5. 为第一条外部样本准备 `external_verified` promotion checklist。

## 工作包 G：全局同品类差距重排

输出文件：

- `docs/research/antigravity_round17_global_gap_rerank_2026_06_25.md`

请重新对标 JHora、PyJHora、VedAstro、Hora Prakash、Maitreya、HinduVahini、AstroSage/Kundli 类产品，给当前项目做 20 项差距重排。

输出表格：

| 排名 | 能力 | 当前状态 | 对标对象 | 为什么重要 | Codex 下一步 |
|---|---|---|---|---|---|

至少覆盖：

- Oracle/accuracy workflow。
- Shadbala absolute calibration。
- Dasha boundary calibration。
- Ashtakoot 合婚样本。
- KP Horary 样本。
- Muhurta 搜索样本。
- Bhava Chalit/Sripati/Placidus 样本。
- D24/D30/D60 深分盘样本。
- PWA/static demo 边界。
- AI Prompt Pack/RAG 用户端承载。

## 工作包 H：用户端黑盒流程压力测试计划

输出文件：

- `docs/research/antigravity_round17_user_flow_stress_plan_2026_06_25.md`

请设计不少于 12 条用户端黑盒流程，每条写清：

| 流程 | 用户动作 | 预期结果 | 失败风险 | 建议自动化入口 |
|---|---|---|---|---|

至少包含：

- 静态 demo 无 API 首次打开。
- 本地 API 在线完整排盘。
- Raman/KP ayanamsa 切换。
- AI Prompt Pack 复制。
- Evidence Packet 下载。
- Evidence Packet 导入失败。
- Evidence Packet 导入成功模拟。
- 移动端 Trust Center。
- PDF/HTML 导出。
- 保存/打开本地星盘库。
- Skill Workbench API Explorer。
- Oracle progress dashboard。

## 工作包 I：隐私与仓库卫生专项审计

输出文件：

- `docs/research/antigravity_round17_privacy_repo_hygiene_audit_2026_06_25.md`

请做只读仓库卫生审计，重点是哪些文件不应进入 Git 或公开报告：

```bash
git status --short
rg -n "output_report|results_extracted|private|token|api_key|cookie|birth report|source_artifact|artifacts" \
  .gitignore README.md docs references tests scripts jyotish-app
```

输出：

| 风险 | 路径或 token | 是否已防护 | 建议 |
|---|---|---|---|

不要读取密钥文件内容，不要输出任何疑似密钥值。

## 最终回报格式

请用中文输出：

1. 已创建的文件列表。
2. Artifacts 存档规范是否成立。
3. Shadbala 六分量强校验是否成立。
4. 真实进度仪表盘是否可被普通用户理解。
5. 第一条 JHora 教程还缺什么。
6. Bug 表（P0/P1/P2，文件路径，行号或搜索 token，修复建议）。
7. Codex 可立刻执行的前 10 个任务，按 ROI 排序。
8. 哪些任务必须等待用户人工截图或外部工具输出。

结尾必须写：

> 下一步建议 Codex 优先……
