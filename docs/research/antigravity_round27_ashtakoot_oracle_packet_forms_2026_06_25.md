# Antigravity AI Ashtakoot 5/5 Oracle Packet 手工表单 (Round 27)

为了让人类不用写代码也能提供 Oracle Evidence，我把 5 个包的设计直接变成可复制的 JSON 表单：

| 包编号 / 样本目的 | 手工填写表单结构 (存入 `ashtakoot_oracle_cases.json`) |
|---|---|
| 1. 名人 (Virat & Anushka) | `{ "boy_dob": "1988-11-05", "girl_dob": "1988-05-01", "varna_score": _, "vashya_score": _, "tara_score": _, "yoni_score": _, "grahamaitri_score": _, "gana_score": _, "bhakoot_score": _, "nadi_score": _, "total_score": _, "image_path": "artifacts/ash_1.png", "source": "AstroSage", "status": "external_verified" }` |
| 2. 随机常人 (95/96) | (同上结构，换生日和分数，换 artifacts/ash_2.png) |
| 3. 高分绝配 (1990 同月) | (同上结构，换生日和分数，换 artifacts/ash_3.png) |
| 4. 刑克烂配 (火星冲) | (同上结构，换生日和分数，换 artifacts/ash_4.png) |
| 5. 同月同日 (豁免测) | (同上结构，测 Nadi 0 分但总分合格的豁免，换 artifacts/ash_5.png) |
| 6. 月亮补充 | 必须附加字段：`"boy_moon_nakshatra"`, `"girl_moon_nakshatra"` 供交叉比对。 |
| 7. 填写要求 1 | 所有的分项 `*_score` 相加必须等于 `total_score`，这是小学生的数学。 |
| 8. 填写要求 2 | 如果 AstroSage 没有提供某些细分项（一般都有），就填 null，并在 source_note 里说明。 |
| 9. Ayanamsa 锚定 | 统一在 AstroSage 里选择 Lahiri (Chitra Paksha)。 |
| 10. 时区锚定 | 由于合婚极端依赖月亮星宿，所以时间必须尽量给 12:00 PM 以防月亮跨界。 |
| 11. Codex 任务 1 | 🟢 Codex可做 | 把上面这段 JSON 骨架直接塞进 `ashtakoot_oracle_cases.json` 里，留空等待填。 |
| 12. Codex 任务 2 | 🟢 Codex可做 | 跑 `test_oracle_collection_queue.py`，确认它发现了 5 个待处理的任务。 |
| 13. Codex 任务 3 | 🟢 Codex可做 | 完善 validator 对 `image_path` 是否存在的检测。 |
| 14. 副手下轮 1 | 🟢 副手可做 | 查证除了 Lahiri，AstroSage 是否支持其它岁差供切换比对。 |
| 15. 副手下轮 2 | 🟢 副手可做 | 如果人类迟迟不填，写个模拟脚本生成假数据，但保持状态为 `draft`，防止污染正式线。 |
| 16. 需要人工 | 🟢 需人工 | 必须有一个真实的人去网站点点点，然后把图截下来，把数字填进去。 |
| 17. 为什么不用爬虫 | 商业网站的 API 会变，且爬虫有法律风险；截屏作为电子存证（Artifact）最坚固。 |
| 18. 分数上限验证 | Varna(1), Vashya(2), Tara(3), Yoni(4), Graha(5), Gana(6), Bhakoot(7), Nadi(8)。 |
| 19. 工具版本 | `"source_version": "2026-06"`。 |
| 20. 验收目标 | 一旦填满，我们就能跑通过所有的合婚断言了！ |
| 21. 误差容忍 | 如果差了 0.5 分，我们在后续再慢慢修，先有一套标准靶标。 |
| 22. 自动化前传 | 这是我们迈向 E2E Playwright 的先决条件。 |
| 23. 知识下放 | 大大降低了外部贡献者的门槛。 |
| 24. 易用性 | 纯 JSON，连代码都不用会。 |
| 25. 总结 | 这是玄学工程化最质朴的一步。 |
