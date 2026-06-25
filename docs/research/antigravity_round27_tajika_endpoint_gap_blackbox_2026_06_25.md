# Antigravity AI Tajika 端点缺口黑盒复核 (Round 27)

| 复核项 | 状态与描述 |
|---|---|
| 1. `varshaphala.py` 存在性 | 🟢 存在。包含完整的 Muntha 和 Panchavargiya Bala 计算。 |
| 2. `jyotish_api_server.py` 挂载 | 🔴 不存在。完全没有 `/api/tajika` 的路由配置。 |
| 3. `/api/chart` 包含性 | 🔴 未包含。全盘 JSON 也没有带出 Tajika 的内容（因为其极其特殊，需要指定年份）。 |
| 4. 前端调用 | 🔴 不存在。前端的 `/api-bridge` 里没有任何 `postJson('/api/tajika')` 的痕迹。 |
| 5. 结论 | 这个核心功能处于**完全游离**的状态，属于僵尸代码（虽有测试但无业务链路）。 |
| 6. Payload 格式 | 必须传入 `birth_date`, `birth_time`, `lat`, `lon`, `tz`，**还要外加一个 `target_year`**。 |
| 7. Return 格式 | `{ "muntha_sign": "...", "muntha_house": _, "lord_of_year": "...", "panchavargiya_bala": {...} }` |
| 8. 准确率测试 | 已经有 `tests/test_tajika.py` 覆盖。 |
| 9. Codex 任务 1 | 🟢 Codex可做 | 在 `jyotish_api_server.py` 增加 `/api/tajika` 路由和处理函数 `_compute_tajika`。 |
| 10. Codex 任务 2 | 🟢 Codex可做 | 在 `api_server` 测试里加入 `test_api_server_security.py::test_tajika_endpoint_returns_muntha` 断言。 |
| 11. Codex 任务 3 | 🟢 Codex可做 | 去 `jyotish-app/api-bridge.js` 里写个封装函数 `fetchTajika(payload)`。 |
| 12. 副手下轮 1 | 🟢 副手可做 | 设计前端如果展示这套年盘，应该长什么样（跟本命盘左右并列？）。 |
| 13. 副手下轮 2 | 🟢 副手可做 | 翻译 Muntha 和 Panchavargiya Bala 的用户科普解释文案。 |
| 14. 人工 | 🔴 否 | |
| 15. 商业价值 | "我明年运势怎么样" 是占星学的终极刚需。Tajika 专解此题。 |
| 16. 安全性 | 作为独立端点，不会拖累主 API 的速度。 |
| 17. 缓存 | 这属于幂等计算，完全可以加 HTTP Cache-Control。 |
| 18. TDD 意义 | 把死代码激活是重构的极简方式。 |
| 19. 代码行数 | 大概只要在 API server 里加 15 行代码。 |
| 20. 总结 | 这是沉睡的巨兽，快唤醒它。 |
