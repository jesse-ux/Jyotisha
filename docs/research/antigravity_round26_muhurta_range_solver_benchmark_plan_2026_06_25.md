# Antigravity AI Muhurta Range Solver 外部对标方案 (Round 26)

Muhurta（择吉）不只是算出哪天好，更是排除凶时。

| 步骤 | 操作细则与对比点 |
|---|---|
| 1. AstroSage 操作 | 打开 `astrosage.com` 的 `Muhurat` 页面。 |
| 2. 设置时间跨度 | 选 2026-06-01 到 2026-06-30，地点选 New Delhi。 |
| 3. 选择活动类型 | 选 `Marriage` (婚姻)。 |
| 4. 获取基准结果 | 记录 AstroSage 给出的几个良辰吉日及其具体小时（比如 6月5日 10:00-14:00）。 |
| 5. 提取排除时段 | 记录哪些日子被因为 `Rahu Kala` 或者凶星 Tithi 被完全剔除了。 |
| 6. 本地模拟执行 | `python3 -c "import muhurta; print(muhurta.muhurta_range_search('2026-06-01', '2026-06-30', 'marriage', lat=28.6, lon=77.2, tz=5.5))"` |
| 7. 对比项 1: 吉日命中率 | 我们推荐的日期，是否在 AstroSage 的吉日列表中？ |
| 8. 对比项 2: 凶时排雷率 | 我们的算法是否成功在每日明细中给出了与 AstroSage 相同的 `Rahu Kala` 警告红条？ |
| 9. JHora 对比 | 打开 JHora 8.0，输入相同的起始时间，进入 `Muhurta` tab，验证 Panchanga 的五个细分项。 |
| 10. 测试框架落地 | `tests/test_muhurta.py` 中已经有 `test_muhurta_range_search_respects_inauspicious_conditions`。 |
| 11. Codex 任务 1 | 🟢 Codex可做 | 将那 5 个从 AstroSage 拿到的 `Rahu Kala` 具体起止时间点硬编码到 `test_muhurta.py` 进行断言。 |
| 12. Codex 任务 2 | 🟢 Codex可做 | 对 `muhurta_range_search` 的返回结果，增加 `astro_sage_match_score` 的字段预留。 |
| 13. Codex 任务 3 | 🟢 Codex可做 | 去 `api_server` 中把对 `lat` 和 `lon` 的传参做好，防止时区计算偏移。 |
| 14. 副手下轮 1 | 🟢 副手继续做 | 查阅古典文献，确认在结婚（Marriage）时，哪些特定的 `Yoga` 是被绝对禁止的。 |
| 15. 副手下轮 2 | 🟢 副手继续做 | 给前端设计一个能够渲染 `muhurta_range_search` 结果的时间轴 UI 草图。 |
| 16. 需要人工 | 🟢 需人工 | 需要人工去截 AstroSage 那个吉日表。 |
| 17. 方案评估 | 极具价值。Muhurta 是直接变现的付费点。 |
| 18. 复杂度 | 中高，因为涉及大量的太阳起落运算。 |
| 19. 前置条件 | Tithi 算法必须精确到秒。 |
| 20. 总结 | 择吉功能绝非空白，而是蓄势待发，只欠对标。 |
