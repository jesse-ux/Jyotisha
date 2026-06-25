# Antigravity AI 副手任务单 Round 6（2026-06-25）

## 角色边界

本轮继续作为外部审计与黑盒复验副手。Codex 已把 Dasha/Shadbala 外部真值采集队列升级为带 `evidence_packet` 的可填写证据包；副手负责复验这个证据包是否足够可执行、是否阻止本地输出伪装外部真值、README/质量门是否同步。

禁止事项：

- 不要提交、重置、删除、批量格式化或覆盖现有文件。
- 不要读取、记录、传播任何 token、API key、浏览器登录态、系统钥匙串或远端凭证。
- 不要复制 JHora/PyJHora/AGPL/GPL 项目的实现代码、公式常量或内部数据表。
- 不要修改 `scripts/`、`jyotish-app/`、`skills/`、`SKILL.md`、`tests/` 下的实现文件。
- 不要把 `template_only`、`local_baseline`、本仓库输出或空目标字段标成 `external_verified`。
- 不要建议为了单个样本调生产常数、Shadbala scaling、Dasha 年长常数。

允许事项：

- 可以读取 `scripts/oracle_collection_queue.py`、`references/oracle/dasha_shadbala_oracle_cases.json`、`tests/test_oracle_collection_queue.py`、`README.md`、`scripts/run_quality_gate.py` 和 Round 5 报告。
- 可以运行只读验证命令：
  - `python3 scripts/oracle_collection_queue.py --oracle-file references/oracle/dasha_shadbala_oracle_cases.json --format json`
  - `python3 scripts/oracle_collection_queue.py --oracle-file references/oracle/dasha_shadbala_oracle_cases.json --format markdown`
  - `python3 -B -m pytest tests/test_oracle_collection_queue.py tests/test_frontend_productization.py::test_dasha_reference_audit_is_documented_and_gated -q`
- 可以创建 `docs/research/*round6*2026_06_25.md` 报告。
- 可以在 `/tmp` 做外部包/API 探测，但不能把代码复制进仓库。

## 当前背景

`oracle_collection_queue.py` 现在每个 task 都应包含：

- `evidence_packet.capture_id`
- `evidence_packet.status == draft`
- `required_metadata_fields`: `tool_name`、`tool_version_or_url`、`capture_date`、`source_artifact`、`ayanamsa`、`node_mode`、`timezone`、`operator_note`
- `target_placeholders`: 与 `missing_target_fields` 一一对应，值保持 `null`
- `integrity_checks.must_not_come_from_local_engine == true`
- `integrity_checks.requires_external_artifact == true`
- `promotion_status_after_fill == external_verified`

队列仍必须保持：

- `summary.total_tasks == 5`
- `summary.ready_for_collection == 5`
- `summary.ready_for_calibration == 0`
- `summary.production_tuning_allowed == false`

## 对标任务 A：evidence_packet 黑盒复验

目标：验证 JSON 输出中每个 task 都有完整证据包，且证据包不会把本地输出误当作外部真值。

输出文件：

- `docs/research/antigravity_round6_evidence_packet_blackbox_2026_06_25.md`

必须检查：

- 5 个 task 都包含 `evidence_packet.capture_id`。
- `target_placeholders` 的 key 与 `missing_target_fields` 完全一致。
- 所有 placeholder 值都是 null。
- integrity checks 包含 `must_not_come_from_local_engine` 与 `requires_external_artifact`。
- shadbala 缺失任务必须标记 `reject_global_shadbala_scaling`。

## 开源参考任务 B：人工采集模板可执行性

目标：把 `evidence_packet` 转成人工/JHora/PyJHora/VedAstro 采集检查清单，确认字段不会遗漏关键元数据。

输出文件：

- `docs/research/antigravity_round6_manual_collection_template_checklist_2026_06_25.md`

必须包含表格：

| 字段 | 必填原因 | JHora 采集方式 | PyJHora 黑盒方式 | VedAstro HTTP 方式 | 风险 |
|---|---|---|---|---|---|

至少覆盖：

- `tool_name`
- `tool_version_or_url`
- `capture_date`
- `source_artifact`
- `ayanamsa`
- `node_mode`
- `timezone`
- `operator_note`
- `target_placeholders`

## Bug 任务 C：README/质量门 evidence packet 同步复验

目标：确认这个证据包不是隐藏实现细节，而是进入开发者流程。

输出文件：

- `docs/research/antigravity_round6_readme_quality_gate_evidence_packet_sync_2026_06_25.md`

检查点：

- README 是否包含 `evidence_packet.capture_id`。
- README 是否提到 `tool_name`、`source_artifact`。
- README 是否明确本仓库本地计算输出不得作为外部 artifact。
- `scripts/run_quality_gate.py` 是否包含 `ORACLE_COLLECTION_QUEUE_EXPECTED_FIELDS` 或等价守门说明。
- `tests/test_oracle_collection_queue.py` 是否验证 `evidence_packet`。

Bug 表格式：

| 严重程度 | 文件路径 | 行号 | 现象 | 复现步骤 | 修复建议 |
|---|---|---:|---|---|---|

严重度：

- P0：证据包可能允许本地输出伪装为外部真值。
- P1：证据包字段缺失或 README/质量门完全未接入。
- P2：文案不够清晰或字段名容易误解。

## 普通用户/产品任务 D：准确率透明度文案复验

目标：确认对普通用户的解释不会夸大 Dasha/Shadbala 准确率。

输出文件：

- `docs/research/antigravity_round6_accuracy_wording_guardrails_2026_06_25.md`

必须分三章：

1. 对标
2. 开源参考
3. Bug

必须包含：

- 当前基础排盘/分盘可作为高可信计算证据。
- Dasha/Shadbala 绝对值仍需外部证据包扩充。
- `ready_for_calibration: 0` 时不得声称完全校准。
- 明确禁止“已与 JHora/PyJHora 100% 对齐”“人生事件预测准确率世界第一”等话术。

## 最终回复格式

完成后在 Antigravity 聊天里回复：

1. 已创建哪些 `docs/research/*round6*2026_06_25.md` 文件。
2. evidence packet 是否通过黑盒复验。
3. 当前队列任务数、可采集数、可校准数。
4. P0/P1/P2 Bug 总表。
5. 下一步建议给 Codex 的可执行修复事项。

最终报告必须使用中文，章节固定为：

- 对标
- 开源参考
- Bug
