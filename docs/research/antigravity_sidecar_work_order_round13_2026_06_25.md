# Antigravity AI 副手任务单 Round 13（2026-06-25）

## 任务目标

本轮优先级改为“技法覆盖与准确率”。请围绕 Codex 正在补的 `Oracle Evidence Intake` 用户端入口做黑盒复核，并继续评估 Dasha/Shadbala 外部真值采集如何真正启动。

请只做复核、对标、报告，不修改核心实现。

需要确认：

1. Trust Center 是否暴露 `Oracle Evidence Intake`，并展示 5 个 `oracle_collection_queue.py` 模板任务。
2. 每个卡片是否能下载空白 Evidence Packet，并包含外部工具元数据与目标字段。
3. 下载包是否明确保持 `status: draft`，并包含 `must_not_come_from_local_engine`、`requires_external_artifact`、`reject_global_shadbala_scaling` 等防污染规则。
4. UI 是否仍清楚区分“D1/D9/SAV 高可信”和“Dasha/Shadbala 绝对值等待外部校准”。
5. 相对 JHora、PyJHora、VedAstro，下一批最该优先补的高阶技法与准确率缺口是什么。

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
- 可以读取 `docs/research/*round12*`、本任务单和相关公开研究报告。
- 可以读取 `jyotish-app/main.js`、`style.css`、`ai-chat.js`、`api-bridge.js`、`public/api-bridge.js`、`export.js`、`tests/test_frontend_productization.py`，只做复核。
- 可以运行只读命令：`git status`、`git log`、`rg`、`python3 ... --format json`、`pytest`、`npm run build --prefix jyotish-app`。
- 只能新增 `docs/research/*round13*2026_06_25.md` 报告文件。

## 必跑命令

### 1. Git / 本地状态复核

```bash
git status --short --branch
git log --oneline --decorate -n 8
```

### 2. Oracle Evidence Intake 静态复核

```bash
rg -n "ORACLE_EVIDENCE_INTAKE_TASKS|ORACLE_EVIDENCE_PACKET_REQUIRED_METADATA|renderOracleEvidenceIntakePanel|downloadOracleEvidencePacket|Oracle Evidence Intake|data-action=\"oracle-download-packet\"|external_verified|must_not_come_from_local_engine|requires_external_artifact|reject_global_shadbala_scaling" \
  jyotish-app/main.js \
  tests/test_frontend_productization.py
```

```bash
rg -n "template_private_oracle_redacted|template_steve_jobs_dasha_lahiri|template_redacted_place_shadbala_raman|template_extreme_latitude_kp|template_historical_epoch_lahiri|moon_sidereal_longitude_deg|vimshottari_start_date|shadbala_components|tool_name|tool_version_or_url|capture_date|source_artifact|operator_note" \
  jyotish-app/main.js \
  tests/test_frontend_productization.py
```

### 3. 样式与移动端风险复核

```bash
rg -n "oracle-evidence-intake-panel|oracle-evidence-intake-grid|oracle-evidence-card|oracle-evidence-fields|dasha-shadbala-calibration-panel|trust-status-grid" \
  jyotish-app/style.css
```

### 4. Oracle / evidence gate 复验

```bash
python3 scripts/oracle_collection_queue.py \
  --oracle-file references/oracle/dasha_shadbala_oracle_cases.json \
  --format json > /tmp/jyotish_oracle_queue_round13.json
```

```bash
python3 scripts/oracle_evidence_validator.py \
  --queue-file /tmp/jyotish_oracle_queue_round13.json
```

```bash
python3 -B -m pytest \
  tests/test_frontend_productization.py::test_trust_center_exposes_oracle_evidence_intake_cards \
  tests/test_frontend_productization.py::test_trust_center_and_ai_expose_dasha_shadbala_calibration_status \
  tests/test_oracle_collection_queue.py \
  tests/test_oracle_evidence_validator.py \
  -q
```

### 5. 用户端构建复核

```bash
npm run build --prefix jyotish-app
```

## 输出报告 A：Evidence Intake 黑盒复核

输出文件：

- `docs/research/antigravity_round13_evidence_intake_blackbox_2026_06_25.md`

固定小节：

1. 对标
2. 开源参考
3. Bug

必须判断：

- 5 个任务是否全部可见。
- 空白包是否包含必要元数据与目标字段。
- 是否仍可能误导用户把 draft 当作 external_verified。

## 输出报告 B：准确率工作流断点清单

输出文件：

- `docs/research/antigravity_round13_accuracy_workflow_gap_2026_06_25.md`

请按流程列出断点：

| 步骤 | 当前状态 | 缺口 | 推荐修复文件 |
|---|---|---|---|

至少覆盖：

- 外部软件取数
- Evidence Packet 下载
- Evidence Packet 回填
- Validator 校验
- JSON case 晋级
- 生产调参解锁
- 前端准确率披露

## 输出报告 C：高阶技法优先级矩阵

输出文件：

- `docs/research/antigravity_round13_technique_priority_matrix_2026_06_25.md`

请对照 JHora、PyJHora、VedAstro，列出下一批技法优先级：

| 优先级 | 技法 | 为什么影响准确率 | 推荐验证方式 | 涉及文件 |
|---|---|---|---|---|

至少评估：

- Vimshottari Dasha 边界日期
- Shadbala 六分量
- Multi-Ayanamsa / node mode
- Ashtakavarga/SAV
- Divisional charts D1/D9/D10/D60
- Panchanga/Muhurta
- Koota 合婚
- KP Prashna / Sub Lord

## 输出报告 D：给 Codex 的 Round 14 任务建议

输出文件：

- `docs/research/antigravity_round13_codex_round14_recommendations_2026_06_25.md`

请给出 3-5 个可执行任务，并明确每个任务涉及的文件路径、测试命令和验收标准。

优先考虑：

1. 支持用户导入填写后的 Evidence Packet，并调用 validator 给出本地结果。
2. 将 `oracle_collection_queue` 摘要动态或静态同步到 Trust Center。
3. 补 JHora/PyJHora 手动采集操作说明，不接触实现代码。
4. 继续提高 Dasha/Shadbala 绝对值校准样本覆盖率。
5. 把准确率披露和技法覆盖矩阵同步到用户导出报告。

## 最终回报格式

请用中文输出：

1. 已创建的文件列表。
2. Evidence Intake 是否可见、可下载、可防污染。
3. 当前准确率工作流还卡在哪一步。
4. 下一批技法优先级前三名。
5. Bug 表（P0/P1/P2，文件路径，行号或搜索 token，修复建议）。

结尾必须写：

> 下一步建议 Codex 优先……
