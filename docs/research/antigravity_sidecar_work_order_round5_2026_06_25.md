# Antigravity AI 副手任务单 Round 5（2026-06-25）

## 角色边界

Antigravity AI 本轮继续作为外部审计与黑盒复验副手。Codex 正在把 Dasha/Shadbala 外部真值采集流程做成可执行队列；副手负责复验队列输出、README/质量门接入、外部来源采集可行性和报告产出。

禁止事项：

- 不要提交、重置、删除、批量格式化或覆盖现有文件。
- 不要读取、记录、传播任何 token、API key、浏览器登录态、系统钥匙串或远端凭证。
- 不要复制 JHora/PyJHora/AGPL/GPL 项目的实现代码、公式常量或内部数据表。
- 不要修改 `scripts/`、`jyotish-app/`、`skills/`、`SKILL.md`、`tests/` 下的实现文件。
- 不要把 `template_only`、`local_baseline`、本仓库输出或空目标字段标成 `external_verified`。
- 不要建议为了单个样本调生产常数、Shadbala scaling、Dasha 年长常数。

允许事项：

- 可以读取 `scripts/oracle_collection_queue.py`、`references/oracle/dasha_shadbala_oracle_cases.json`、`scripts/oracle_boundary_audit.py`、`tests/test_oracle_collection_queue.py`、`tests/test_oracle_boundary_audit.py`、README 和 Round 4 报告。
- 可以运行只读验证命令：
  - `python3 scripts/oracle_collection_queue.py --oracle-file references/oracle/dasha_shadbala_oracle_cases.json --format json`
  - `python3 scripts/oracle_collection_queue.py --oracle-file references/oracle/dasha_shadbala_oracle_cases.json --format markdown`
  - `python3 -B -m pytest tests/test_oracle_collection_queue.py tests/test_oracle_boundary_audit.py -q`
  - `python3 scripts/oracle_boundary_audit.py --oracle-file references/oracle/dasha_shadbala_oracle_cases.json`
- 可以创建 `docs/research/*round5*2026_06_25.md` 报告。
- 可以在 `/tmp` 做外部包/API 探测，但不能把代码复制进仓库。

## 当前背景

Codex 已新增或正在收口：

- `scripts/oracle_collection_queue.py`
- `tests/test_oracle_collection_queue.py`
- README 中的采集队列说明
- release/quality gate 中的采集队列命令

该队列目标：把 5 个 `template_cases` 自动转成可执行任务，输出缺失字段、目标模块、推荐外部来源、采集步骤、升级 `external_verified` 的判据，并保持 `production_tuning_allowed=false`。

## 对标任务 A：采集队列黑盒复验

目标：验证队列脚本真实可运行、输出稳定、不会误导为可调参。

执行：

```bash
python3 scripts/oracle_collection_queue.py \
  --oracle-file references/oracle/dasha_shadbala_oracle_cases.json \
  --format json

python3 scripts/oracle_collection_queue.py \
  --oracle-file references/oracle/dasha_shadbala_oracle_cases.json \
  --format markdown
```

输出文件：

- `docs/research/antigravity_round5_oracle_collection_queue_blackbox_2026_06_25.md`

必须检查：

- `scope == external_oracle_collection_queue`
- `summary.total_tasks == 5`
- `summary.by_status.template_only == 5`
- `summary.ready_for_collection == 5`
- `summary.ready_for_calibration == 0`
- `summary.production_tuning_allowed == false`
- 每个 task 有 `missing_target_fields`、`preferred_sources`、`collection_steps`、`promotion_criteria`
- Markdown 表格包含 5 个 `collect_*` task。

## 开源参考任务 B：外部来源采集动作清单

目标：不要泛泛说“用 JHora/PyJHora”，而是给每个 source 一个可执行采集动作。

输出文件：

- `docs/research/antigravity_round5_external_source_collection_actions_2026_06_25.md`

必须包含：

| source | 可采字段 | 采集动作 | 需要记录的元数据 | 许可证/合规边界 | 风险 |
|---|---|---|---|---|---|

至少覆盖：

- JHora / Jagannatha Hora：人工截图/手工录入。
- PyJHora：黑盒输出采集，AGPL，不复制实现。
- VedAstro HTTP API：黄经/API 方法清单，频控/超时限制。
- Swiss Ephemeris 文档：sidereal mode/ayanamsa 规范，非 Dasha/Shadbala oracle。

## Bug 任务 C：README 与质量门接入复验

目标：确认采集队列不是隐藏工具。

输出文件：

- `docs/research/antigravity_round5_readme_quality_gate_sync_2026_06_25.md`

检查点：

- README 是否包含：
  - `python3 scripts/oracle_collection_queue.py`
  - `external_oracle_collection_queue`
  - `ready_for_calibration: 0`
  - `production_tuning_allowed: false`
- `scripts/run_quality_gate.py` 是否包含：
  - `oracle_collection_queue.py` 编译目标
  - `ORACLE_COLLECTION_QUEUE_CMD`
  - release profile 下运行该命令，或者有明确 reason 不运行。
- `tests/test_frontend_productization.py` 是否守住 README/quality gate 文案。

Bug 表格式：

| 严重程度 | 文件路径 | 行号 | 现象 | 复现步骤 | 修复建议 |
|---|---|---:|---|---|---|

严重度：

- P0：队列可能把 template/local 数据误认为可调参。
- P1：队列无法运行、README/质量门完全未接入。
- P2：文案或字段名不清晰。

## 普通用户/产品任务 D：把采集队列转成用户可理解说明

目标：准确解释“为什么还不能说 Dasha/Shadbala 完全校准，以及下一步怎么做”。

输出文件：

- `docs/research/antigravity_round5_user_facing_oracle_collection_explainer_2026_06_25.md`

必须分三章：

1. 对标
2. 开源参考
3. Bug

必须包含：

- 面向普通用户的话术：基础排盘可信、Dasha/Shadbala 仍在外部真值扩充。
- 面向开发者的话术：5 个采集任务、5 个 `template_only`、0 个 `ready_for_calibration`。
- 禁止话术：不得声称 JHora/PyJHora 已完全对齐、不得声称人生事件预测准确率。

## 最终回复格式

完成后在 Antigravity 聊天里回复：

1. 已创建哪些 `docs/research/*round5*2026_06_25.md` 文件。
2. `oracle_collection_queue.py` 是否通过黑盒复验。
3. 当前队列任务数、可采集数、可校准数。
4. P0/P1/P2 Bug 总表。
5. 下一步建议给 Codex 的可执行修复事项。

最终报告必须使用中文，章节固定为：

- 对标
- 开源参考
- Bug
