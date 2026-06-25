# Antigravity AI Muhurta 外部 Oracle SOP (Round 27)

| 操作步骤 | 人类执行手册 |
|---|---|
| 1. 工具选择 | 推荐使用 `drikpanchang.com`。 |
| 2. 设置位置 | 右上角，设置为 `New Delhi, India`。 |
| 3. 设置时间 | 选择 `June 2026`。 |
| 4. 采集吉日 | 进入 `Muhurat` -> `Marriage Muhurat`，截图。 |
| 5. 采集凶时 | 回到主页 Panchang，选择 2026-06-25，往下滑找到 `Inauspicious Timings`，截图 (包含 Rahu Kalam, Yamaganda, Gulika Kalam)。 |
| 6. 采集 Choghadiya | 点击 `Day Choghadiya`，截图一张。 |
| 7. 采集 Tithi | 同样是 2026-06-25 主页，截图 `Tithi` 的起始时间和结束时间。 |
| 8. 存入仓库 | 把上述 4 张图放入 `references/oracle/artifacts/`，如 `muhurta_drik_rahu_june25.png`。 |
| 9. 新建 JSON 模板 | 我 (Codex) 会在 `references/oracle/muhurta_oracle_cases.json` 给你留好空位。 |
| 10. 录入数据 | 人类只需把图上的具体时刻（如 14:30）敲进 JSON 对应的键值里。 |
| 11. Codex 任务 1 | 🟢 Codex可做 | 新建 `references/oracle/muhurta_oracle_cases.json`。 |
| 12. Codex 任务 2 | 🟢 Codex可做 | 结构体包含 `date`, `lat`, `lon`, `expected_rahu_start`, `expected_rahu_end`。 |
| 13. Codex 任务 3 | 🟢 Codex可做 | 在 validator 里加上 `_validate_muhurta_evidence` 的读取功能。 |
| 14. 副手下轮 1 | 🟢 副手可做 | 编写计算当地日落偏移的浮点容差，因为算 Rahu Kala 很容易差几分钟。 |
| 15. 副手下轮 2 | 🟢 副手可做 | 了解 AstroSage 和 Drik Panchang 在日出定义上的细微差距（比如上边缘还是中心）。 |
| 16. 需要人工 | 🟢 需人工 | 截图和手打 JSON 的体力活。 |
| 17. 为什么不自己编 | 坚守黑盒法则，一切以商业标杆的实际输出为准。 |
| 18. 重要性 | 择日（Muhurta）错一分钟，吉时变凶时。 |
| 19. 时区大坑 | JSON 必须明确标出所用的是 IST (UTC+5:30) 还是当地平太阳时。 |
| 20. 样本多样性 | 除了德里，日后还需补充高纬度地区（如伦敦）的验证，那里的日出差异极大。 |
| 21. 最终目标 | 我们要在这个细分领域达到 0 误差的底气。 |
| 22. 证据保存 | 截图永远存在，任何人 clone 代码都能复现。 |
| 23. 无缝衔接 | 有了这些，Codex 就能 TDD 狂飙了。 |
| 24. 防作弊 | 不许人类直接跑我们自己的代码来填。 |
| 25. 总结 | 这是占星引擎的绝对真理试金石。 |
