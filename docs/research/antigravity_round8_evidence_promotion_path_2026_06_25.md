# Antigravity AI 外部证据包晋级导入路径复核 (Round 8)

## 导入路径分析

通过复盘当前库中的 `oracle_collection_queue.py` 与 `oracle_evidence_validator.py` 逻辑，本系统对外部真值的晋级和导入设计了一条极度严格的防伪路径。

### 标准的外部证据晋级流转 (Promotion Path)

1. **提取空置任务**：系统通过 `scripts/oracle_collection_queue.py` 解析出所有 `template_only` 状态的模板，明确列出该模板缺失的 `missing_target_fields`（如大运日期、力量分值等）。
2. **外部取样操作**：开发或数据维护者手动操作 JHora 或 PyJHora 黑盒，在确保 Ayanamsa、经纬度、时区等参数完全一致的情况下提取出黄经、力量、日期。
3. **手动合并与装填**：修改 `references/oracle/dasha_shadbala_oracle_cases.json` 源文件：
   - 将采集到的数据填入 `target` 的对应字段下。
   - 在该 case 下新增并填满 `evidence_packet.metadata` 对象（包含 `tool_name`, `capture_date`, `source_artifact`, `ayanamsa`, `operator_note` 等 8 项必填元数据）。
   - 将 `status` 状态从 `"template_only"` 修改为 `"external_verified"`。
4. **校验器验尸官**：执行 `scripts/oracle_evidence_validator.py`：
   - 它会对导入的 payload 进行交叉查验。
   - **防伪拦截**：如果 `metadata` 中出现了 `local engine`、`this-repo` 甚至我们的源文件名等蛛丝马迹，校验器会直接以 `local_engine_artifact_rejected` 将其拦截，死守绝对不自产自销底线。
   - **完整性拦截**：只要还差一个靶心字段为空，都会报 `placeholder_unfilled`。

### 结论
当前的晋级机制没有任何后门，所有想要解锁生产常数调优（`production_tuning_allowed=True`）的行为，必须实打实地完成 JSON 文本中繁琐且无捷径可走的合法性声明。这使得我们的外部对齐动作不仅是一个数据更新行为，更是一次严谨的证据质控行为。
