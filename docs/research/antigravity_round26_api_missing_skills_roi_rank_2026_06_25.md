# Antigravity AI API 未暴露技能 ROI 排序 (Round 26)

剔除 `/api/chart`, `/api/synastry`, `/api/panchanga_range`, `/api/muhurta` 等已存在的端点，继续深挖底层函数未暴露的宝藏：

| 排名 | API 缺口端点名 | 引擎支撑 | ROI / 业务价值 |
|---|---|---|---|
| **1** | `/api/tajika` | `scripts/varshaphala.py` | 极高。支持用户的“看明年运势”独立查询。 |
| **2** | `/api/dasha/chara` | `scripts/chara_dasha.py` | 高。避免把所有大运都塞进 `/api/chart` 导致 payload 巨大。 |
| **3** | `/api/yoga_list` | 混合在全盘里。 | 高。作为独立查询知识库，方便百科功能。 |
| **4** | `/api/ashtakavarga`| `scripts/ashtakavarga_v2.py`| 高。独立输出 12 宫分，供第三方 App 画图。 |
| **5** | `/api/export_ics` | 无 | 中。一键下发日历订阅流。 |
| **6** | `/api/aspect` | 混合计算 | 中。给“我太阳和月亮什么关系”的快速答疑。 |
| 7. `/api/kp` | | | |
| 8. `/api/prashna` | | | |
| 9. Codex 任务 1 | 🟢 Codex可做 | 在 `jyotish_api_server.py` 里加上 `elif path == '/api/tajika':`。 |
| 10. Codex 任务 2 | 🟢 Codex可做 | 为其加上接收 `target_year` 的 JSON 解析逻辑。 |
| 11. Codex 任务 3 | 🟢 Codex可做 | 在 `test_api_server_security.py` 加一个请求该接口的测试。 |
| 12. 副手下轮 1 | 🟢 副手继续做 | 构思 `/api/export_ics` 怎么写才能兼容 Apple Calendar 格式。 |
| 13. 副手下轮 2 | 🟢 副手继续做 | 设计 Tajika 返回的 JSON Schema (包括 Muntha 宫位等特有字段)。 |
| 14. 需要人工 | 🔴 否 | |
| 15. 安全性考量 | `/api/chart` 越来越大，切分端点也是一种性能解药。 |
| 16. 后续架构 | 强烈建议最终重构到 FastAPI 体系下。 |
| 17. API 描述 | 应该给每个 API 加上 Swagger docstring。 |
| 18. 本质 | 我们不能只做一个“算命机”，还要做“占星 API 数据服务商”。 |
| 19. 重要 | 尤其是 `varshaphala.py` 极其孤立，急需盘活。 |
| 20. 总结 | 这些是变现/扩大开源影响力的利器。 |
