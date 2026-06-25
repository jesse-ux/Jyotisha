# Antigravity AI AI Prompt Pack Ashtakoot 扩展设计 (Round 21)

| 扩展维度 | 设计建议 |
|---|---|
| 1. 新增进度 | 是的，在 Prompt Pack 中增加 `ashtakoot_oracle_progress`。 |
| 2. 与当前合并 | 不合并，独立成数组：`oracle_progresses: [{scope: 'shadbala'...}, {scope: 'ashtakoot'...}]`。 |
| 3. Scope 数组 | 把现有的字典重构为一个 List，包含多个并发收集任务的状态。 |
| 4. 避免误称 | 提示模型：“当前合婚算法的基础模型进度为 0/5，切勿对合婚绝对分数做武断定论。” |
| 5. CLI 输出 | `full-reading` 同样增加一个列表输出。 |
| 6. API 输出 | `/api/chart` 的 payload 修改。 |
| 7. 前端 fallback | 离线计算如果出 Ashtakoot，也挂载这个假数据。 |
| 8. Retrieval tag | `external_oracle_ashtakoot_validation`。 |
| 9. Token 成本 | 增加约 30 token，忽略不计。 |
| 10. 测试改动 | `test_cli_smoke.py` 要断言 `len(oracle_progresses) == 2`。 |
| 11. UI 展示 | AI Chat 对话框初始化时，展示“大运与合婚正在等待验证”。 |
| 12. 最小实现路径 | 先在 `jyotish_engine.py` 写死两个 0/5 的返回体装配。 |

**最小 Codex 改动建议**：在 `jyotish_engine.py` 的 `_oracle_progress_snapshot` 中支持数组返回。
