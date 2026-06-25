# Antigravity AI API 全技能暴露度审计 (Round 24)

| 检查项 | 状态与结论 |
|---|---|
| 1. Endpoint 列表 | `/api/chart`, `/api/synastry`, `/api/export_json`。 |
| 2. `/api/chart` 覆盖 | 调用了 `jyotish_engine.py` 的 `get_full_reading()`。理论全包。 |
| 3. `/api/synastry` 覆盖 | 调用了 `ashtakoot.py`。 |
| 4. 遗漏的高阶能力 | `scripts/varshaphala.py` (太阳返照) 只有命令行能独立算，API 似乎没透出独立查询入口。 |
| 5. 遗漏的 Dasha | `scripts/chara_dasha.py` 有文件，API 中只有极少的调用。 |
| 6. 输入校验 | `schema_validator` 挡下了非数字坐标。 |
| 7. 日期格式处理 | `handle_datetime` 目前仅靠 try-except，对夏令时的 `is_dst` 参数支持很弱。 |
| 8. 输出 Schema | 返回的是极深层的 JSON，缺乏 OpenAPI / Swagger 规范。 |
| 9. 错误处理 | `500 Internal Server Error` 会暴露 Python traceback。 |
| 10. 隐私风险 | API 不存库，纯内存中转，安全。 |
| 11. Caching | 没有做任何 LRU 缓存，同一数据每次都重算整个星历。 |
| 12. Rate Limit | 无。极易被 DDoS。 |
| 13. 本地准确率透出 | API 未在 header 中透出 local_accuracy。 |
| 14. 测试覆盖 | `tests/test_api_server_security.py` 覆盖良好，但缺乏高并发测试。 |
| 15. 路由设计 | 应引入 FastAPI，而不是手写 `http.server`。 |
| 16. 下一步建议 | 引入 FastAPI。 |

**副手下一轮任务**：评估从 `http.server` 迁移至 `FastAPI` 的重构范围。
**Codex 可做任务**：在 `/api/chart` 中加入对 `Ayanamsa` 的可选参数接收，打破只能用 Lahiri 的僵局。
