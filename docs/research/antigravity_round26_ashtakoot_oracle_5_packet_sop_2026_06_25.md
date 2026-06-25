# Antigravity AI Ashtakoot Oracle 5/5 采样 SOP (Round 26)

写给任何一位愿意花 10 分钟帮忙的人类：

| 步骤 | 具体操作 |
|---|---|
| 1. 准备清单 | 电脑/手机浏览器，打开 `astrosage.com/matching/`。 |
| 2. 第一对 (名人样本) | 男方名字填 Virat，出生 1988-11-05；女方 Anushka，1988-05-01。忽略时分秒，选 New Delhi。 |
| 3. 截第一张图 | 点 Match，翻到页面底部的 `Guna Milan Table` (有 Varna, Vashya 等 8 项打分的那张大表)。截图。 |
| 4. 第二对 (普通样本) | 男方 1995-01-01，女方 1996-02-02。截图。 |
| 5. 第三对 (极佳样本) | 男方 1990-05-15，女方 1990-05-18。截图。 |
| 6. 第四对 (极差样本) | 选一对火星严重相冲的日子 (比如一个巨蟹座一个摩羯座随机日)。截图。 |
| 7. 第五对 (同宿例外) | 男方女方填同一天，比如都是 1999-09-09。测试 Nadi 豁免。截图。 |
| 8. 存入代码库 | 将这 5 张截图放进本项目的 `references/oracle/artifacts/` 里，命名如 `ashtakoot_1.png`。 |
| 9. 修改 JSON 1 | 打开 `references/oracle/ashtakoot_oracle_cases.json`。 |
| 10. 抄写八项分数 | 对照截图，把 `varna_score`, `vashya_score` 等 8 个小项的分数敲进去。 |
| 11. 抄写总分 | 敲入 `total_score` (满分 36)。 |
| 12. 敲入月亮落点 | 把页面上显示的男女双方的月亮 Nakshatra（星宿名）填进去。 |
| 13. 改状态 | 把这 5 个块的 `status` 从 `draft` 改为 `external_verified`。 |
| 14. 验证 | 在终端运行 `python3 scripts/oracle_evidence_validator.py`。 |
| 15. 如果报错 | 截图发给我（AI），我来修代码！ |
| 16. Codex 任务 1 | 🟢 Codex可做 | 没你的事，这全是人工活。 |
| 17. Codex 任务 2 | 🟢 Codex可做 | 确保 validator 里有容忍小数点的 float 比对。 |
| 18. 副手下轮 1 | 🟢 副手继续做 | 随时待命，一旦人工上传报错，我光速出修复补丁。 |
| 19. 需要人工 | 🟢 需人工 | 100% 依赖人工。 |
| 20. 为什么非要 5 对 | 因为覆盖了 0分，极低分，满分和例外，足够证明算法健壮性。 |
