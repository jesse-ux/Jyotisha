# Antigravity AI Ashtakoot 外部 Oracle 采集最短路径 (Round 25)

为了最快速度打破 0/5，我们只测 AstroSage，因为它是个免费网站：

| 动作流 | 具体执行指令 |
|---|---|
| 1. 输入月亮度数 | 为了极简，我们找 5 对名人的阳历生日（无需知道具体出生分钟，只要能算月亮即可，因为 Ashtakoot 纯按月亮算）。 |
| 2. AstroSage 来源 | 访问 `astrosage.com/matching/`。 |
| 3. 目标字段 | 输入名人 1 和 名人 2。 |
| 4. 截图位置 | 往下滚，找到一个 `Guna Milan Table` (8行表) 以及 `Total Score: X / 36` 的地方，截图。 |
| 5. JSON 填写路径 | 打开我们库里的 `references/oracle/ashtakoot_oracle_cases.json`。 |
| 6. 验证命令 | `python3 scripts/oracle_evidence_validator.py` |
| 7. 失败处理 | 如果我们算的总分与 AstroSage 的差超 0.01，那就是我们的算法有漏。 |
| 8. 样本1 (名人) | 比如 Virat Kohli 和 Anushka Sharma。 |
| 9. 样本2 (虚拟) | 男方出生于 2000-01-01，女方 2000-01-02。 |
| 10. 样本3 (极差) | 选一个 Manglik 严重冲突的。 |
| 11. 样本4 (同宿) | 选两个生日极度接近的，测试 Nadi 豁免。 |
| 12. 样本5 (满分) | 找个完美匹配的日子。 |
| 13. 最短人力 | 熟手在网页上点一点，这 5 个包 15 分钟就能生成完毕。 |
| 14. 不去用 JHora | JHora 的界面太杂，AstroSage 的表一目了然。 |
| 15. 是否需要人工 | 🟢 需人工外部工具 | 是的。必须用浏览器自己点。 |
| 16. 下一步 Codex 1 | 🟢 Codex可做 | 无。这纯人工。 |
| 17. 下一步 Codex 2 | 🟢 Codex可做 | 在 `ashtakoot.py` 加一段 logger 把两边月亮落点打出来，方便排错。 |
| 18. 下一步 副手 | 🟢 副手继续做 | 如果人工填好报错，我来负责扒我们算法和人家差在了哪一个 Kuta 上。 |
