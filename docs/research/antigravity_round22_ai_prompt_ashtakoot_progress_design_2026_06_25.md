# Antigravity AI Prompt Pack Ashtakoot 进度设计 (Round 22)

在与 AI 的对话中加入合婚模块验证进度：

| 设计维度 | 具体建议 |
|---|---|
| 1. 当前结构 | 目前是单字典 `dasha_shadbala_oracle_progress`。 |
| 2. 新增进度 | 是的，加入 `ashtakoot_oracle_progress`。 |
| 3. 合并数组 | 将其放入 `oracle_progresses: [...]`。 |
| 4. CLI 字段 | `jyotish_engine.py` 的 JSON 返回中增加该数组。 |
| 5. API 字段 | `/api/chart` 响应增加对应数据。 |
| 6. 前端 Fallback | `main.js` 需处理假返回。 |
| 7. Retrieval Tag | `external_oracle_ashtakoot_validation`。 |
| 8. Token 成本 | 很小，不影响大局。 |
| 9. 用户边界文案 | 让 AI 说明：“当前的合婚算法只经过了 0/5 个真实案例测试，不可做确定性人生指导”。 |
| 10. Tests | 测试需断言 `len(oracle_progresses) >= 2`。 |
| 11. Trust Center | UI 会独立使用这部分数据来渲染新的卡片。 |
| 12. 最小实现 | 直接在 `scripts/jyotish_engine.py` 中写一个针对 Ashtakoot 的查询，将其与原有进度合并。 |

**落地建议**：在引擎里多调一次 Queue 解析，组装成两个字典组成的列表下发即可。
