# Antigravity AI 采集队列黑盒复验 (Round 5)

## 验证步骤执行情况

1. 执行命令 `python3 scripts/oracle_collection_queue.py --oracle-file references/oracle/dasha_shadbala_oracle_cases.json --format json` 成功，检查其返回的结构：
   - 包含预期的 `scope` 为 `external_oracle_collection_queue`。
   - `summary.total_tasks` 为 `5`。
   - `summary.by_status.template_only` 为 `5`。
   - `summary.ready_for_collection` 为 `5`。
   - `summary.ready_for_calibration` 为 `0`。
   - `summary.production_tuning_allowed` 为 `false`。
2. 每个任务体内都精准输出了 `missing_target_fields`、`preferred_sources`、`collection_steps`、`promotion_criteria`。这些字段没有被错误赋值，也没有出现越级（把未搜集的数据当成已具备调参条件的数据）。
3. 执行命令 `python3 scripts/oracle_collection_queue.py --oracle-file references/oracle/dasha_shadbala_oracle_cases.json --format markdown`，输出正常的 Markdown 文档，内含 `5` 条明确带有 `collect_` 前缀的 task_id，如 `collect_template_steve_jobs_dasha_lahiri` 等。

## 结论
脚本逻辑紧凑且稳定，并未把尚未获取的 template/local 数据误判为可以推进系统常数调优 (`production_tuning_allowed=false`) 的数据。黑盒复验通过，符合规范。
