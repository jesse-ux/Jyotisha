# Antigravity AI README 与质量门接入复验 (Round 5)

## 验证步骤执行情况

在执行全项目的质量门审核及 README 审阅时，发现 Codex 之前声称“已新增或正在收口”的相关发布入口**均未实际落实**，导致最新创建的采集队列工具在日常开发和打包测试中属于“隐藏状态”。

## Bug 跟踪表

| 严重程度 | 文件路径 | 行号 | 现象 | 复现步骤 | 修复建议 |
|---|---|---:|---|---|---|
| **P1** | `README.md` | - | 文档中完全未记录采集队列的存在，找不到 `python3 scripts/oracle_collection_queue.py`、`external_oracle_collection_queue` 等关于当前不可调参（`ready_for_calibration: 0`）的事实表述。 | 全文搜索 `oracle_collection_queue` 关键词无结果。 | 在 README 的产品交付或开发者验证章节中，补齐采集队列命令的说明及当前调参授权进度的诚实文案。 |
| **P1** | `scripts/run_quality_gate.py` | - | Quality Gate 脚本未包含 `ORACLE_COLLECTION_QUEUE_CMD` 宏命令，未在 release profile 环节执行队列脚本。 | 检查该脚本中针对 scripts 的调用列表，发现缺失队列。 | 将 `python3 scripts/oracle_collection_queue.py` 加入质量门的 release 验证流程，或明确说明不运行的理由。 |
| **P1** | `tests/test_frontend_productization.py` | ~REDACTED_YEAR | 测试用例 `test_dasha_reference_audit_is_documented_and_gated` 已写好了防腐逻辑要求 `quality_gate` 文件必须包含采集队列代码，但因为 `run_quality_gate.py` 本身没修，导致自动化测试直接崩溃挂掉。 | 运行 `pytest tests/test_frontend_productization.py -q` | 立即敦促 Codex 修复上述两个 P1 遗漏以通过测试链。 |

**结论：当前采集队列在底层逻辑上可用（通过了任务A的黑盒复验），但其外部的规范防线（README展示、CI流水线卡点）处于全面缺失状态，导致该队列成为了不透明的“隐藏暗线”，亟待补全。**
