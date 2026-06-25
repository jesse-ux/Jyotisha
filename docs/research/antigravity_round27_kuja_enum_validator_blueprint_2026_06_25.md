# Antigravity AI Kuja Enum Validator 蓝图 (Round 27)

| 蓝图拆解项 | 规则 / 架构细节 |
|---|---|
| 1. 定义 Enum 字典 | `["none", "low_dosha", "medium_dosha", "high_dosha", "neutralized", "requires_review"]`。 |
| 2. API 返回类型 | `/api/synastry` 里的火星煞不再返回 `kuja_boy: true`，而是 `kuja_boy: "high_dosha"`。 |
| 3. validator 校验 | `_validate_synastry_evidence` 读取 json 时，对 `kuja_status_boy` 和 `girl` 做白名单 in 检查。 |
| 4. 报错行为 | 非法枚举抛出 `ValueError: Invalid kuja status ...`。 |
| 5. 兼容策略 (向后兼容) | 允许 validator 在短时间内把 `True` 自动转为 `"high_dosha"`，并在日志打出 deprecation warning。 |
| 6. 前端 UI 兼容 | `main.js` 里需要 `if (kuja === 'high_dosha') return '火星煞 (严重)'` 的映射表。 |
| 7. 前端 UI 颜色 | high: 红色, medium: 橙色, none: 绿色, neutralized: 黄色。 |
| 8. 豁免情况 (neutralized) | 当占星书提到“火星在第 2 宫但落在双子座时无害”，就返回此值。 |
| 9. 测试名 1 | `test_kuja_validator_rejects_boolean_values()` |
| 10. 测试名 2 | `test_kuja_validator_rejects_unknown_strings()` |
| 11. 测试名 3 | `test_synastry_api_returns_kuja_enum_instead_of_boolean()` |
| 12. Codex 任务 1 | 🟢 Codex可做 | 在 `oracle_evidence_validator.py` 修改 Kuja 逻辑。 |
| 13. Codex 任务 2 | 🟢 Codex可做 | 去 `jyotish_engine.py` 和 `ashtakoot.py` 把底层的 bool 返回彻底消灭。 |
| 14. Codex 任务 3 | 🟢 Codex可做 | 去前端 `jyotish-app/main.js` 更新火星状态的渲染逻辑。 |
| 15. 副手下轮 1 | 🟢 副手可做 | 罗列出南印和北印流派里把 low_dosha 定义为哪些宫位（如第 1 宫 vs 第 2 宫）。 |
| 16. 副手下轮 2 | 🟢 副手可做 | 收集 BPHS 里的 neutralized 豁免细则。 |
| 17. 需要人工 | 🔴 否 | |
| 18. 重要性 | 占星界对火星煞有着极其复杂的辩经，一刀切的 true/false 显得业余且武断。 |
| 19. 代码位置 | 深入到 AST/Engine 层级。 |
| 20. 结构体 | JSON Schema 需要同步更新。 |
| 21. 对标 AstroSage | 他们有 Anshik Manglik (部分火星煞) 的概念，对应我们的 low/medium。 |
| 22. 对标 JHora | 它也会列出 Exceptions。 |
| 23. 向前推进 | TDD 的好机会。 |
| 24. API 版本 | 可不用改 v1/v2，直接在当前版硬切。 |
| 25. 总结 | 枚举是刻画模糊世界的最佳数据结构。 |
