# Antigravity AI 副手任务单 Round 7（2026-06-25）

## 角色边界

本轮继续作为外部审计与黑盒复验副手。Codex 已把 Dasha/Shadbala 外部真值采集队列扩展为“队列生成 + 证据包校验 + quick/release 质量门守护”的闭环。你负责验证闭环是否真实可执行，尤其确认 `oracle_evidence_validator.py` 不会把本仓库输出、本地脚本输出或空字段误判成外部真值。

禁止事项：

- 不要提交、重置、删除、批量格式化或覆盖现有文件。
- 不要读取、记录、传播任何 token、API key、浏览器登录态、系统钥匙串或远端凭证。
- 不要复制 JHora/PyJHora/AGPL/GPL 项目的实现代码、公式常量或内部数据表。
- 不要修改 `scripts/`、`jyotish-app/`、`skills/`、`SKILL.md`、`tests/` 下的实现文件。
- 不要把 `template_only`、`local_baseline`、本仓库输出或空目标字段标成 `external_verified`。
- 不要建议为了单个样本调生产常数、Shadbala scaling、Dasha 年长常数。

允许事项：

- 可以读取 `scripts/oracle_collection_queue.py`、`scripts/oracle_evidence_validator.py`、`scripts/run_quality_gate.py`、`references/oracle/dasha_shadbala_oracle_cases.json`、`tests/test_oracle_collection_queue.py`、`tests/test_oracle_evidence_validator.py`、`tests/test_frontend_productization.py`、`README.md` 和 Round 5/Round 6 报告。
- 可以运行只读验证命令。
- 可以在 `/tmp` 生成临时 JSON 队列文件、临时验证日志。
- 可以创建 `docs/research/*round7*2026_06_25.md` 报告。
- 可以在 `/tmp` 做外部包/API 探测，但不能把任何第三方实现代码复制进仓库。

## 必跑命令

请按顺序执行并记录关键输出：

```bash
python3 scripts/oracle_collection_queue.py \
  --oracle-file references/oracle/dasha_shadbala_oracle_cases.json \
  --format json > /tmp/jyotish_oracle_queue_round7.json
```

```bash
python3 scripts/oracle_evidence_validator.py \
  --queue-file /tmp/jyotish_oracle_queue_round7.json
```

```bash
python3 -B -m pytest \
  tests/test_oracle_collection_queue.py \
  tests/test_oracle_evidence_validator.py \
  tests/test_frontend_productization.py::test_dasha_reference_audit_is_documented_and_gated \
  -q
```

```bash
python3 scripts/run_quality_gate.py \
  --profile quick \
  --skip-frontend-runtime \
  --skip-yoga-logic
```

预期状态：

- 队列 `summary.total_tasks == 5`
- 队列 `summary.ready_for_collection == 5`
- 队列 `summary.ready_for_calibration == 0`
- validator `summary.total_packets == 5`
- validator `summary.valid_packets == 0`
- validator `summary.production_tuning_allowed == false`
- pytest 通过
- quick 质量门会直接覆盖 `tests/test_oracle_collection_queue.py` 与 `tests/test_oracle_evidence_validator.py`

## 对标任务 A：证据校验器黑盒复验

输出文件：

- `docs/research/antigravity_round7_evidence_validator_blackbox_2026_06_25.md`

必须检查：

- draft packet 因缺少 metadata、source artifact、target placeholders 和 `external_verified` 状态被拒绝。
- 人工填满单个外部 packet 时，只能让该 packet 变成 valid，不能让全队列进入 `production_tuning_allowed: true`。
- `Local Engine`、`this-repo`、`scripts/jyotish_engine.py` 等本仓库来源会被拒绝。
- validator 输出 scope 必须是 `external_oracle_evidence_validation`。

## 开源参考任务 B：外部真值晋级清单复验

输出文件：

- `docs/research/antigravity_round7_external_verified_promotion_checklist_2026_06_25.md`

必须包含：

- JHora 手工截图采集流程。
- PyJHora 黑盒 stdout/截图采集流程，明确 AGPL 代码不可复制。
- VedAstro HTTP/SDK 采集流程，明确仅作为辅助交叉参照。
- 每种来源如何填写 `tool_name`、`tool_version_or_url`、`capture_date`、`source_artifact`、`ayanamsa`、`node_mode`、`timezone`、`operator_note`。
- 晋级为 `external_verified` 前必须补齐哪些 target 字段。

## Bug 任务 C：quick/release 质量门同步复验

输出文件：

- `docs/research/antigravity_round7_core_quality_gate_sync_2026_06_25.md`

检查点：

- `CORE_PYTEST_TARGETS` 是否包含 `tests/test_oracle_collection_queue.py`。
- `CORE_PYTEST_TARGETS` 是否包含 `tests/test_oracle_evidence_validator.py`。
- `EXTRA_COMPILE_TARGETS` 是否包含两个 oracle 脚本。
- `RELEASE_CRITICAL_UNTRACKED_PATHS` 是否包含两个脚本和两个测试。
- release profile 是否在 `skip_oracle_audit == false` 时运行 collection queue + validator。

Bug 表格式：

| 严重程度 | 文件路径 | 行号 | 现象 | 复现步骤 | 修复建议 |
|---|---|---:|---|---|---|

严重度：

- P0：质量门可能允许空数据或本地输出进入生产调参。
- P1：quick/release 任一关键质量门未覆盖证据包校验。
- P2：文档或错误输出不够清晰。

## 普通用户/产品任务 D：准确率透明度复核

输出文件：

- `docs/research/antigravity_round7_user_accuracy_disclaimer_review_2026_06_25.md`

必须分三章：

1. 对标
2. 开源参考
3. Bug

必须判断：

- 产品是否可以说“基础排盘、D1/D9、SAV 与外部参考高度一致”。
- 产品是否仍不能说“Dasha/Shadbala 已完全与 JHora/PyJHora 校准”。
- `ready_for_calibration: 0` 时，前台/Skill/README 是否有夸大准确率风险。
- 建议普通用户话术：哪些结果可作为高可信，哪些结果仍处于外部校准队列。

## 最终回复格式

完成后在 Antigravity 聊天里回复：

1. 已创建哪些 `docs/research/*round7*2026_06_25.md` 文件。
2. validator 是否通过黑盒复验。
3. 当前队列任务数、可采集数、可校准数、有效证据包数。
4. P0/P1/P2 Bug 总表。
5. 下一步建议给 Codex 的可执行修复事项。

最终报告必须使用中文，章节固定为：

- 对标
- 开源参考
- Bug
