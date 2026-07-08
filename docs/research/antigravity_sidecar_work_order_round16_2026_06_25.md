# Antigravity AI 副手任务单 Round 16（2026-06-25）

## 任务目标

本轮继续“多包并行”，优先完成技法与准确率基础设施。Codex 主线将推进 `references/oracle/artifacts/` 存档规范与 Shadbala 六分量强校验，请你并行做黑盒复核、对标和下一步任务拆分。

请只做复核、对标、报告，不修改核心实现。

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

- 可以读取 `README.md`、`SKILL.md`、`progress.md`。
- 可以读取 `docs/research/*round15*`、本任务单和相关公开研究报告。
- 可以读取 `references/oracle/dasha_shadbala_oracle_cases.json`、`scripts/oracle_collection_queue.py`、`scripts/oracle_evidence_validator.py`、`scripts/jyotish_api_server.py`、`jyotish-app/main.js`、`api-bridge.js`、`style.css`、`tests/test_frontend_productization.py`、`tests/test_api_server_security.py`、`tests/test_oracle_evidence_validator.py`，只做复核。
- 可以运行只读命令：`git status`、`git log`、`rg`、`python3 ... --format json`、`pytest`、`npm run build --prefix jyotish-app`。
- 只能新增 `docs/research/*round16*2026_06_25.md` 报告文件。

## 必跑命令

### 1. Git / 本地状态复核

```bash
git status --short --branch
git log --oneline --decorate -n 8
```

### 2. Artifacts 存档规范复核

```bash
rg -n "references/oracle/artifacts|oracle_artifact|source_artifact|artifact storage|外部截图|隐私|打码|external_oracle_artifact" \
  README.md \
  references/oracle \
  docs/research \
  tests
```

### 3. Shadbala 六分量校验复核

```bash
rg -n "sthana|dig|kala|chesta|naisargika|drik|shadbala_components|missing_shadbala_component|reject_global_shadbala_scaling" \
  scripts/oracle_evidence_validator.py \
  tests/test_oracle_evidence_validator.py \
  tests/test_api_server_security.py \
  references/oracle/dasha_shadbala_oracle_cases.json
```

### 4. Oracle / evidence gate 复验

```bash
python3 scripts/oracle_collection_queue.py \
  --oracle-file references/oracle/dasha_shadbala_oracle_cases.json \
  --format json > /tmp/jyotish_oracle_queue_round16.json
```

```bash
python3 scripts/oracle_evidence_validator.py \
  --queue-file /tmp/jyotish_oracle_queue_round16.json
```

```bash
python3 -B -m pytest \
  tests/test_oracle_collection_queue.py \
  tests/test_oracle_evidence_validator.py \
  tests/test_api_server_security.py::test_oracle_evidence_api_validates_uploaded_packets \
  tests/test_frontend_productization.py::test_trust_center_exposes_oracle_evidence_intake_cards \
  -q
```

### 5. 用户端构建复核

```bash
npm run build --prefix jyotish-app
```

## 工作包 A：Artifacts 存档规范黑盒复核

输出文件：

- `docs/research/antigravity_round16_artifact_storage_blackbox_2026_06_25.md`

固定小节：

1. 对标
2. 开源参考
3. Bug

判断：

- 是否已有 `references/oracle/artifacts/` 或等效规范。
- Evidence Packet 的 `source_artifact` 是否能引用该规范。
- 是否有隐私打码要求。
- 是否禁止私人 PDF、完整出生报告、浏览器 scratch 入库。

## 工作包 B：Shadbala 六分量强校验复核

输出文件：

- `docs/research/antigravity_round16_shadbala_component_validator_audit_2026_06_25.md`

请检查 validator 是否强制七曜每颗具备：

- `sthana`
- `dig`
- `kala`
- `chesta`
- `naisargika`
- `drik`

输出：

| 规则 | 是否检查 | 缺口 | 推荐修复 |
|---|---|---|---|

## 工作包 C：第一条真实 JHora 样本准备清单

输出文件：

- `docs/research/antigravity_round16_first_jhora_sample_checklist_2026_06_25.md`

请把 `template_private_oracle_redacted` 转成手工操作清单：

1. JHora 输入项。
2. 需要截图的页面。
3. 需要摘录的字段。
4. Evidence Packet 填写模板。
5. 运行 validator 后的期望结果。
6. 不能晋级的情况。

注意：只能黑盒取数，不得逆向或复制 JHora 实现。

## 工作包 D：Dasha/Shadbala 真实进度仪表盘建议

输出文件：

- `docs/research/antigravity_round16_accuracy_dashboard_plan_2026_06_25.md`

请设计一个用户可理解的仪表盘：

| 指标 | 当前值 | 用户解释 | 数据来源 |
|---|---|---|---|

至少包含：

- total template cases
- valid packets
- ready for calibration
- production tuning allowed
- D1/D9/SAV confidence
- Dasha boundary calibration
- Shadbala absolute calibration

## 工作包 E：给 Codex 的 Round 17 任务建议

输出文件：

- `docs/research/antigravity_round16_codex_round17_recommendations_2026_06_25.md`

请给出 5-8 个可执行任务，每个任务必须包含：

- 文件路径
- 测试命令
- 验收标准
- 是否需要用户人工提供外部截图

优先考虑：

1. 将 artifacts 存档规范接入 README 和 Evidence Packet 下载文案。
2. 将 Shadbala 六分量强校验接入后端 `/api/oracle_evidence`。
3. 生成第一条 `template_private_oracle_redacted` 的外部样本填表说明。
4. 增加 Dasha/Shadbala 真实进度仪表盘。
5. 将 Ashtakoot 合婚纳入下一批 oracle 样本。

## 最终回报格式

请用中文输出：

1. 已创建的文件列表。
2. Artifacts 存档规范是否成立。
3. Shadbala 六分量强校验是否成立。
4. 第一条 JHora 样本还缺什么。
5. Bug 表（P0/P1/P2，文件路径，行号或搜索 token，修复建议）。

结尾必须写：

> 下一步建议 Codex 优先……
