# Antigravity AI 开源许可证隔离清单 (Round 27)

防范开源侵权是生死底线。我们将 Github 上的占星库做如下隔离判定：

| 开源包/项目 | License 状态 | 本项目处理策略 |
|---|---|---|
| 1. `VedAstro/VedAstro` | 🟢 MIT | **copy_allowed**: 随意扒取其中的 C# 常量数组并翻译为 Python 字典。 |
| 2. `flatlib/flatlib` | 🟢 MIT | **copy_allowed**: 我们的核心星历依赖，可随意用。 |
| 3. `sanatana/panchanga` | 🟢 MIT | **copy_allowed**: 可借鉴其 Rahu Kala 的逻辑。 |
| 4. `RoxyAPI/...` | 🟢 MIT | **copy_allowed**: 借鉴其 Next.js 界面的设计和色彩。 |
| 5. `RaviKarrii/Marriage...` | 🟢 MIT | **copy_allowed**: 扒取其 Ashtakoot 的 Java 表格。 |
| 6. `astral-sh/astral` | 🟢 MIT | **copy_allowed**: 昼夜时间推算。 |
| 7. `kerykeion/kerykeion` | 🟢 MIT | **copy_allowed**: 参考其 SVG 绘制技巧。 |
| 8. `dashaflow/app` | 🟢 MIT | **copy_allowed**: JS 测 Vimshottari 实现。 |
| 9. `PriyankGahtori/...` | 🟡 闭源/无声明 | **benchmark_only**: 仅供打开它的网页把玩，看看产品该怎么做。 |
| 10. `fusionstrings/...` | 🟡 待确认 | **quarantine**: 尚未探明前，一律不碰。 |
| 11. `naturalstupid/PyJHora` | 🔴 AGPL-3.0 | **benchmark_only**: 绝对不可抄源码！只用其软件/API 跑结果做黑盒对比。 |
| 12. `kunjara/jyotish` | 🔴 GPL-2.0+ | **benchmark_only**: 传染性极强，不可碰源码。 |
| 13. `pyswisseph` | 🔴 GPL/特例 | **port_with_attribution**: 它有特殊的 FOSS 豁免条款，目前我们的包里合规。 |
| 14. 闭源商业 APP | 🔴 Proprietary | **benchmark_only**: 如 AstroSage，只能截图测算结果做靶标。 |
| 15. Codex 任务 1 | 🟢 Codex可做 | 在 `NOTICE.md` 建立“感恩名单”，列入前 8 个 MIT 项目。 |
| 16. Codex 任务 2 | 🟢 Codex可做 | 确保没有任何带有 GPL 字眼的片段被粘贴进我们的代码库。 |
| 17. 副手下轮 1 | 🟢 副手可做 | 持续巡逻我们引入的新 pip 包的 license。 |
| 18. 人工 | 🔴 否 | |
| 19. 意义 | 保护项目未来的商业化。 |
| 20. 总结 | 拥抱 MIT，隔离毒药。 |
