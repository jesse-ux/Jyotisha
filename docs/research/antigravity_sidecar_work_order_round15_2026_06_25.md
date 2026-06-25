# Antigravity AI 副手任务单 Round 15（2026-06-25）

## 任务目标

从本轮开始，副手任务升级为“多包并行审计”。主线优先“技法与准确率”，不要停留在单点 UI 复核。请按 6 个工作包同时推进，只做黑盒复核、资料对标和报告产出，不修改核心实现。

## 严格边界

禁止事项：

- 不要提交、推送、重置、删除、移动、批量格式化或覆盖现有文件。
- 不要读取、记录、传播任何 GitHub token、API key、浏览器登录态、cookie、SSH 私钥或系统钥匙串。
- 不要打开或摘录用户私人星盘完整报告正文。
- 不要修改 `scripts/`、`jyotish-app/`、`skills/`、`SKILL.md`、`tests/`、`README.md` 的实现内容。
- 不要把 `output_report.txt`、`results_extracted.md`、PDF 原件、Antigravity scratch 或私人出生资料纳入同步建议。
- 不要复制 JHora、PyJHora、AGPL/GPL 项目的实现代码、公式常量或内部数据表。
- 不要把 `template_only`、`local_baseline`、本仓库输出或空目标字段标成 `external_verified`。
- 不要使用“绝对可信”“世界第一”“完全校准”等过度准确率话术。

允许事项：

- 可以读取 `README.md`、`SKILL.md`、`progress.md`。
- 可以读取 `docs/research/*round13*`、`docs/research/*round14*`、本任务单和相关公开研究报告。
- 可以读取 `scripts/oracle_collection_queue.py`、`scripts/oracle_evidence_validator.py`、`scripts/jyotish_api_server.py`、`jyotish-app/main.js`、`api-bridge.js`、`style.css`、`export.js`、`tests/test_frontend_productization.py`、`tests/test_api_server_security.py`、`tests/test_oracle_evidence_validator.py`，只做复核。
- 可以运行只读命令：`git status`、`git log`、`rg`、`python3 ... --format json`、`pytest`、`npm run build --prefix jyotish-app`。
- 只能新增 `docs/research/*round15*2026_06_25.md` 报告文件。

## 必跑命令

### 1. Git / 本地状态复核

```bash
git status --short --branch
git log --oneline --decorate -n 8
```

### 2. Evidence Intake + 判卷闭环复核

```bash
rg -n "oracle-evidence-upload|importOracleEvidencePacket|validateOracleEvidencePacket|renderOracleEvidenceValidationResult|validateOracleEvidence|/api/oracle_evidence|external_oracle_evidence_validation|valid_packets|ready_for_calibration|production_tuning_allowed|status_not_external_verified|local_engine_artifact_rejected" \
  jyotish-app/main.js \
  jyotish-app/api-bridge.js \
  scripts/jyotish_api_server.py \
  tests/test_frontend_productization.py \
  tests/test_api_server_security.py
```

```bash
python3 -B -m pytest \
  tests/test_frontend_productization.py::test_trust_center_exposes_oracle_evidence_intake_cards \
  tests/test_api_server_security.py::test_oracle_evidence_api_validates_uploaded_packets \
  tests/test_oracle_collection_queue.py \
  tests/test_oracle_evidence_validator.py \
  -q
```

### 3. Oracle 队列/validator 复验

```bash
python3 scripts/oracle_collection_queue.py \
  --oracle-file references/oracle/dasha_shadbala_oracle_cases.json \
  --format json > /tmp/jyotish_oracle_queue_round15.json
```

```bash
python3 scripts/oracle_evidence_validator.py \
  --queue-file /tmp/jyotish_oracle_queue_round15.json
```

### 4. 用户端构建复核

```bash
npm run build --prefix jyotish-app
```

## 工作包 A：Evidence 判卷闭环黑盒复核

输出文件：

- `docs/research/antigravity_round15_evidence_validation_loop_blackbox_2026_06_25.md`

固定小节：

1. 对标
2. 开源参考
3. Bug

判断：

- 用户是否能下载、导入、判卷。
- 返回结果是否清楚展示 `problems`。
- 本地输出、空字段、`draft` 是否仍被拦截。

## 工作包 B：Shadbala 六分量准确率战役

输出文件：

- `docs/research/antigravity_round15_shadbala_accuracy_campaign_2026_06_25.md`

请输出：

| 项 | 当前项目状态 | JHora/PyJHora/VedAstro 参考 | 缺口 | 下一步 |
|---|---|---|---|---|

必须覆盖：

- Sthana
- Dig
- Kala
- Chesta
- Naisargika
- Drik
- Rupa/Virupa total
- 不允许全局缩放系数

## 工作包 C：Vimshottari Dasha 边界日期战役

输出文件：

- `docs/research/antigravity_round15_dasha_boundary_campaign_2026_06_25.md`

请输出：

| 样本 | 当前字段 | 外部目标字段 | 可能偏差来源 | 推荐采集步骤 |
|---|---|---|---|---|

必须覆盖：

- 月亮黄经
- Nakshatra / Pada
- 大运起点
- Antardasha 起点
- 年长/时区/秒精度
- Ayanamsa 与 node mode

## 工作包 D：高需求技法补齐优先级

输出文件：

- `docs/research/antigravity_round15_high_demand_technique_gap_2026_06_25.md`

对照普通用户需求和开源竞品，排序：

- Ashtakoot/Koota 合婚
- KP Sub Lord / Prashna
- Panchanga/Muhurta
- D10/D60 分盘
- Tajika/Annual
- Yogas/Arishta/Raja Yoga

输出：

| 排名 | 技法 | 用户价值 | 准确率风险 | 推荐实现/验证路径 |
|---|---|---|---|---|

## 工作包 E：外部截图工件与隐私存档规范

输出文件：

- `docs/research/antigravity_round15_oracle_artifact_storage_policy_2026_06_25.md`

请设计仓库规范：

- `references/oracle/artifacts/` 是否应该创建。
- 截图命名规则。
- 哪些内容必须遮挡。
- 哪些内容不能入库。
- Evidence Packet 如何引用截图路径。
- 如何避免私人出生资料泄露。

## 工作包 F：给 Codex 的 Round 16 任务建议

输出文件：

- `docs/research/antigravity_round15_codex_round16_recommendations_2026_06_25.md`

请给出 5-8 个可执行任务，每个任务必须包含：

- 文件路径
- 测试命令
- 验收标准
- 是否需要用户人工提供外部截图

优先考虑：

1. 创建 `references/oracle/artifacts/` 与 README 说明。
2. 增加 Evidence Packet 本地存档/版本记录。
3. 补第一条真实 JHora external_verified 样本。
4. Shadbala 六分量完整性校验。
5. Dasha 边界样本的秒精度/ayanamsa/node mode 验证。
6. Ashtakoot 合婚对标样本。
7. 技法覆盖矩阵同步到 Trust Center/导出报告。
8. 自动生成给外部工具录入的采集清单。

## 最终回报格式

请用中文输出：

1. 已创建的文件列表。
2. Evidence 判卷闭环是否已成立。
3. Shadbala/Dasha/合婚三条准确率战线的当前缺口。
4. 是否建议创建 `references/oracle/artifacts/`。
5. Bug 表（P0/P1/P2，文件路径，行号或搜索 token，修复建议）。

结尾必须写：

> 下一步建议 Codex 优先……
