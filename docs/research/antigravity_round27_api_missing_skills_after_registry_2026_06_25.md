# Antigravity AI API 未暴露技能 ROI 重排 (Round 27)

剔除 `/api/chart`, `/api/synastry`, `/api/panchanga_range`, `/api/muhurta` 后，目前存在于后端逻辑但尚未有独立 `/api/*` 路由的技能池：

| 排名 | 缺口端点与描述 | 支撑模块 / 难度 | 商业 ROI 评估 |
|---|---|---|---|
| 1 | `/api/tajika` (太阳返照 / 年运) | `varshaphala.py` / 极易 | 极高。这是用户每年复购的杀手锏。 |
| 2 | `/api/dasha_chara` (Jaimini运) | `chara_dasha.py` / 易 | 高。避免把所有的流派运势都揉进 `/api/chart` 导致 JSON 爆炸。 |
| 3 | `/api/kp` (KP 星曜强弱) | `kp_system.py` / 易 | 高。KP 门派在印度南方受众极大。 |
| 4 | `/api/ashtakavarga` (12宫打分) | `ashtakavarga_v2.py` / 中 | 中。为极客前端画 12 宫散点图提供原始数据流。 |
| 5 | `/api/calendar_export` (日历订阅) | 无 / 难 (需组装ICS) | 中。能让排盘软件变成每天收推送的系统日历。 |
| 6 | `/api/prashna` (卜卦) | `prashna.py` / 中 | 中。面向单次咨询（如失物、出行）。 |
| 7 | `/api/aspects_detailed` (全相位) | `jyotish_engine.py` / 易 | 低。图表里已经画了，通常不需单独调用。 |
| 8. | Codex 任务 1 | 🟢 Codex可做 | 在 `jyotish_api_server.py` 里加上 `elif path == '/api/tajika':`。 |
| 9. | Codex 任务 2 | 🟢 Codex可做 | 解析 `{ "dob": "...", "target_year": 2026 }`，并返回 Tajika 结果。 |
| 10. | Codex 任务 3 | 🟢 Codex可做 | 添加 `test_api_server_security.py::test_tajika_endpoint_returns_muntha` 断言。 |
| 11. | 副手下轮 1 | 🟢 副手可做 | 起草 `/api/calendar_export` 的 Headers 返回头 (`text/calendar`) 标准。 |
| 12. | 副手下轮 2 | 🟢 副手可做 | 阅读 `kp_system.py` 弄清它怎么返回 1-249 的 Sublord 数字，好定 API schema。 |
| 13. | 人工 | 🔴 否 | |
| 14. | 战略目的 | RESTful 化。 |
| 15. | Swagger | 未来的 FastAPI 重构极度依赖这些清晰拆分的端点。 |
| 16. | 性能优化 | 减轻 `/api/chart` 的载荷。 |
| 17. | TDD | API 端点的增加必须伴随 tests 的覆盖。 |
| 18. | 难度 | `varshaphala.py` 完全就绪，只是没连上线而已。 |
| 19. | 前端耦合 | 前端可以先不画 Tajika UI，API 先行。 |
| 20. | 总结 | 这是让我们的引擎能力真正发挥服务价值的必经之路。 |
