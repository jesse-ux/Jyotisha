# Antigravity AI Ashtakoot / 竞品 License 与复用范围 (Round 27)

| 开源项目 | License | 判定 | 可复用范围说明 |
|---|---|---|---|
| 1. VedAstro/VedAstro | 🟢 MIT | 放心复用 | 合婚的 8 项查表矩阵、行星吉凶分、各派岁差常数。**不可抄**其 UI 代码或封装逻辑。 |
| 2. RaviKarrii/Marriage... | 🟢 MIT | 放心复用 | 如果它有更完整的 Java 矩阵，直接扒取常量数组。 |
| 3. RoxyAPI/jyotish... | 🟢 MIT | UI对标 | 不能用其私有服务端点，但其 Next.js 的用户交互路径、Panchang 面板排版完全可以借鉴思路。 |
| 4. naturalstupid/PyJHora | 🔴 AGPL-3.0 | **剧毒** | 绝对不可以复制代码。只允许运行其 App 作为外部计算黑盒获取比对数据。 |
| 5. kunjara/jyotish | 🔴 GPL-2.0+ | **极毒** | 绝对不可复制。我们是 MIT，GPL 会传染导致我们必须开源所有衍生闭源云服务逻辑。只可做行为基准。 |
| 6. fusionstrings/panchangam | 🟡 待确认 | 需详查 | 尚未确认前，一律视为闭源不可用。 |
| 7. PriyankGahtori/... | 🟡 网页应用 | 仅对标 | 不提供源码，只能当做产品经理视角的功能参考。 |
| 8. 代码清洗要求 | 必须摘取 | 摘取 C# 或 Java 代码时，只能剥离出 `Array` 或 `Dict`，不能保留其类名。 |
| 9. 版权声明要求 | 必须保留 | `scripts/ashtakoot_constants.py` 顶部必须写明：`Constants derived from VedAstro (MIT License) and RaviKarrii (MIT License)`. |
| 10. 测试用例隔离 | 我们自己的 | 测试必须自己写，不可抄别人的测试集以免侵权边缘试探。 |
| 11. Codex 任务 1 | 🟢 Codex可做 | 创建 `NOTICE.md`。 |
| 12. Codex 任务 2 | 🟢 Codex可做 | 在里面写上：`This product includes software derived from VedAstro...`。 |
| 13. Codex 任务 3 | 🟢 Codex可做 | 打开 VedAstro 的仓库，开始人工复制那些大表。 |
| 14. 副手下轮 1 | 🟢 副手可做 | 去查 fusionstrings 的 license 是什么。 |
| 15. 副手下轮 2 | 🟢 副手可做 | 找到 PyJHora 的替代品，看有没有 MIT 的流派。 |
| 16. 需要人工 | 🔴 否 | |
| 17. 商业化边界 | 我们要保证任何公司拿了我们的代码，不会面临被起诉的风险。 |
| 18. 合规为王 | 一段脏代码毁了一个库。 |
| 19. Github 搜索 | 很多所谓的开源其实没放 License 文件，按 Default Copyright 算，也就是闭源。不能碰。 |
| 20. 总结 | VedAstro 简直是天赐的 MIT 宝库。 |
| 21. 知识沉淀 | 把这些法律排雷过程写下来，也是极高的项目价值。 |
| 22. AI 的限制 | 大模型有时候记错 License，必须在 prompt 里强调只查根目录的 LICENSE 文件。 |
| 23. 重写比例 | 常量占 90%，业务逻辑我们自己全重写了，所以很安全。 |
| 24. 依赖扫描 | 目前 requirements.txt 里都是干净的。 |
| 25. 定调 | 拥抱 MIT，隔离 GPL。 |
