# Antigravity AI 副手任务单 Round 12（2026-06-25）

## 任务目标

本轮任务聚焦 Codex 刚完成的“导出报告继承 Dasha/Shadbala 校准边界”以及下一步“外部真值采集表单化”。

请只做黑盒复核与报告，不修改核心实现。

需要确认：

1. `jyotish-app/export.js` 的 JSON 导出是否包含 `meta.calibration_status` 与 `modules.calibration_status.dasha_shadbala`。
2. HTML/PDF fallback 报告是否渲染“高级技法校准状态”，并包含 `ready_for_calibration: 0`、`valid_packets: 0`、`production_tuning_allowed: false`、`external_oracle_evidence_validation`。
3. Trust Center / AI Chat / API Prompt / Skill / Export 五个用户面是否已经口径一致。
4. 下一步如何把 `oracle_collection_queue.py` 的 5 个采集任务做成普通用户可填写、可截图、可复验的采集表单。

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
- 可以读取 `docs/research/*round11*`、本任务单和相关公开研究报告。
- 可以读取 `jyotish-app/export.js`、`main.js`、`ai-chat.js`、`api-bridge.js`、`public/api-bridge.js`、`tests/test_frontend_productization.py`，只做复核。
- 可以运行只读命令：`git status`、`git log`、`git ls-remote`、`rg`、`python3 ... --format json`、`pytest`、`npm run build --prefix jyotish-app`。
- 只能新增 `docs/research/*round12*2026_06_25.md` 报告文件。

## 必跑命令

### 1. Git / GitHub 同步复核

```bash
git status --short --branch
git log --oneline --decorate -n 8
```

```bash
GIT_SSH_COMMAND='ssh -p 443 -o IPQoS=none -o ConnectTimeout=30' \
git ls-remote ssh://git@ssh.github.com:443/732642856/yinduzhanxing.git \
  refs/heads/codex/release-hygiene-ci refs/heads/main
```

### 2. 导出校准边界静态复核

```bash
rg -n "DASHA_SHADBALA_EXPORT_CALIBRATION_STATUS|calibration_status|dasha_shadbala|高级技法校准状态|ready_for_calibration: 0|valid_packets: 0|production_tuning_allowed: false|external_oracle_evidence_validation|不得把大运起点或 Shadbala 绝对值说成已完成外部校准" \
  jyotish-app/export.js \
  tests/test_frontend_productization.py
```

### 3. 五个用户面一致性复核

```bash
rg -n "Dasha/Shadbala Calibration Status|ready_for_calibration: 0|valid_packets: 0|production_tuning_allowed: false|external_oracle_evidence_validation|不得把大运起点或 Shadbala 绝对值说成已完成外部校准|高级技法校准状态" \
  jyotish-app/main.js \
  jyotish-app/ai-chat.js \
  jyotish-app/api-bridge.js \
  jyotish-app/public/api-bridge.js \
  jyotish-app/export.js \
  SKILL.md
```

### 4. Oracle / evidence gate 复验

```bash
python3 scripts/oracle_collection_queue.py \
  --oracle-file references/oracle/dasha_shadbala_oracle_cases.json \
  --format json > /tmp/jyotish_oracle_queue_round12.json
```

```bash
python3 scripts/oracle_evidence_validator.py \
  --queue-file /tmp/jyotish_oracle_queue_round12.json
```

```bash
python3 -B -m pytest \
  tests/test_frontend_productization.py::test_provenance_panchanga_workspace_panel_is_productized \
  tests/test_frontend_productization.py::test_trust_center_and_ai_expose_dasha_shadbala_calibration_status \
  tests/test_oracle_collection_queue.py \
  tests/test_oracle_evidence_validator.py \
  -q
```

### 5. 用户端构建复核

```bash
npm run build --prefix jyotish-app
```

## 输出报告 A：导出报告校准边界复核

输出文件：

- `docs/research/antigravity_round12_export_calibration_boundary_audit_2026_06_25.md`

固定小节：

1. 对标
2. 开源参考
3. Bug

必须判断：

- JSON 导出是否结构化携带校准状态。
- HTML/PDF fallback 是否可见地携带校准状态。
- 是否仍有“网页有边界，但导出物丢边界”的风险。

## 输出报告 B：五个用户面口径一致性

输出文件：

- `docs/research/antigravity_round12_user_surface_consistency_2026_06_25.md`

覆盖：

| 用户面 | 文件 | 是否有校准状态 | 风险 |
|---|---|---|---|

至少包括 Trust Center、AI Chat、API Prompt Bridge、SKILL.md、JSON/HTML 导出。

## 输出报告 C：外部真值采集表单化方案

输出文件：

- `docs/research/antigravity_round12_oracle_collection_form_plan_2026_06_25.md`

必须把 `oracle_collection_queue.py` 的 5 个任务转换成普通人可执行表单方案：

| 字段 | 类型 | 是否必填 | 示例 | 校验规则 |
|---|---|---|---|---|

至少包含：

- `case_id`
- `tool_name`
- `tool_version_or_url`
- `capture_date`
- `source_artifact`
- `ayanamsa`
- `node_mode`
- `timezone`
- `operator_note`
- `moon_sidereal_longitude_deg`
- `vimshottari_start_date`
- `shadbala_components`
- `external_verified`

同时明确：

- 不能上传本仓库本地输出作为外部证据。
- JHora/PyJHora 只能黑盒取数，不复制实现代码。
- `production_tuning_allowed` 只有在足够证据包通过后才可开启。

## 输出报告 D：给 Codex 的 Round 13 任务建议

输出文件：

- `docs/research/antigravity_round12_codex_round13_recommendations_2026_06_25.md`

请给出 3-5 个可执行任务，并明确每个任务涉及的文件路径、测试命令和验收标准。

优先考虑：

1. 在 Web/App 增加 `Oracle Evidence Intake` 只读/本地表单原型。
2. 为 evidence packet 生成可下载空白 JSON 模板。
3. 支持把人工填写的 evidence packet 导入并用 `oracle_evidence_validator.py` 校验。
4. 移动端真实浏览器检查导出报告/Trust Center 长文案不溢出。
5. 继续降低普通用户启动/安装摩擦。

## 最终回报格式

请用中文输出：

1. 已创建的文件列表。
2. GitHub 同步是否一致。
3. 导出报告校准边界是否已修复。
4. 五个用户面是否口径一致。
5. Bug 表（P0/P1/P2，文件路径，行号或搜索 token，修复建议）。

结尾必须写：

> 下一步建议 Codex 优先……
